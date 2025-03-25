
import pickle

from qiskit.quantum_info import StabilizerState
from qiskit_nature.second_q.circuit.library import HartreeFock
from qiskit_nature.second_q.mappers import BravyiKitaevMapper

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit_ibm_runtime import Batch
import math
from dyn_shadow import generage_dynamic_shadow_circuit_nonest


#pickle directry
from get_token_path import get_dir_path, get_token, get_hub_group_project
pickle_dir = get_dir_path()
#ibm token 
ibm_token = get_token()
hub, group, project = get_hub_group_project()


# input =================================
num_qubits = 28
shot_num_per_circuit = 10000
circuit_num = 1
backend_name =  "torino"
circuits_per_batch = 2
# end input =================================

print(f"total circuit number {shot_num_per_circuit*circuit_num}")

#load hamiltonian
with open(f"{pickle_dir}QubitHamiltonian_H{num_qubits//2}_1.0.pickle", "rb") as file:
    hamiltonian = pickle.load(file)

#get backend
service = QiskitRuntimeService(channel="ibm_quantum", instance = f'{hub}/{group}/{project}')    
if backend_name == "least_busy":
    backend = service.least_busy(simulator=False, operational=True)
elif backend_name == "kyiv":
    backend = service.backend("ibm_kyiv")
elif backend_name == "torino":
    backend = service.backend("ibm_torino")
elif backend_name == "fez":
    backend = service.backend("ibm_fez")
else:
    raise Exception("unknown backend")

#prepare state. Hartree-Fock state was adopoted in this case.
#You can sample from a different state by replacing the follwoing three lines. 
mapper = BravyiKitaevMapper()
hf_state = HartreeFock(num_qubits // 2,    num_particles=(num_qubits // 4, num_qubits // 4),    qubit_mapper=mapper,)
state = StabilizerState(hf_state)

# get circuit
shadow_circuit = generage_dynamic_shadow_circuit_nonest(hf_state)

#transpile
pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
qc_transpiled = pm.run(shadow_circuit)

with open(f"{pickle_dir}quantum_circuit.txt", "w") as f:
    print(qc_transpiled,file=f)

print(f"num batch {math.ceil(circuit_num/circuits_per_batch)}")

#Execute cirucit
flag_print_rep_delay = True
flag_print_job_delay = True
for _ in range(math.ceil(circuit_num/circuits_per_batch)):
    with Batch(backend=backend) as batch:
        sampler = Sampler()
        if num_qubits == 40:
            options = sampler.options
            rep_delay = backend.configuration().rep_delay_range[1]
            options.execution.rep_delay=rep_delay
            if flag_print_rep_delay:
                print(f">>> rep_delay = {sampler.options.execution.rep_delay}")
                flag_print_rep_delay = False
        #job execution
        for _ in range(circuits_per_batch):
            job = sampler.run([qc_transpiled], shots=shot_num_per_circuit)
            if flag_print_job_delay:
                print(f">>> JOB ID")
                flag_print_job_delay = False

            print(f"{job.job_id()}")

print("fin")
