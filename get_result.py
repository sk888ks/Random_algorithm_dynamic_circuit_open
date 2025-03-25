import concurrent
from functools import partial
import os
import pickle
import numpy as np
from qiskit_ibm_runtime import QiskitRuntimeService
import json
from qiskit_ibm_runtime import RuntimeEncoder
from dyn_shadow import reconstruct_expval

from get_token_path import get_dir_path, get_token, get_hub_group_project
#save directry
save_dir = get_dir_path()
#ibm token 
ibm_token = get_token()
hub, group, project = get_hub_group_project()

#input ===============================================
result_list_load = False # load result bit list
retrieve_online = True #get result from online
json_write = False #write job result as json
result_list_write = True  # write result bit list
mean_write = True # write list of mean expectation value
mean_load = False # load list of mean expectation value list

num_qubits = 28
shots = int(1e7)
hf_en = -23.97527708837948 #HF energy

job_id_list = ["hogehoge", "hugahuga"] #write job ids
#end input ===============================================


#get result_list
if result_list_load:
    with open(f"{save_dir}result_list_{num_qubits}qubits_{shots}circuits.pickle", "rb") as f:
        result_list = pickle.load(f)
    if num_qubits != len(result_list[0])//3 or shots != len(result_list):
        print(f"qubits input:{num_qubits}, expected:{len(result_list[0])//3}, circuits input{shots}, expected:{len(result_list)}")
        raise Exception("num qubits or circuits incorrect")
else:
    result_list = []
    for job_id in job_id_list:
        if retrieve_online:
            # retrieve result from online 
            service = QiskitRuntimeService(
                channel='ibm_quantum',
                instance=f'{hub}/{group}/{project}',
                token=ibm_token
            )
            job = service.job(job_id=job_id)
            job_result = job.result()
            jb = job.backend()
            
            if json_write:
                # json write
                with open(f"{save_dir}result_{job_id}.json", "w") as file:
                    json.dump(job_result, file, cls=RuntimeEncoder)
        else:
            # retrieve result from offline
            with open(f"{save_dir}result_{job_id}.json", "r") as file:
                job_result = json.load(file, cls=RuntimeDecoder)

        pub_result = job_result[0].data.c.get_counts()

        result_list += [key for key, count in pub_result.items() for _ in range(count)]

    num_qubits = len(result_list[0])//3
    print(num_qubits)

    shots = len(result_list)
    if result_list_write:
        with open(f"{save_dir}result_list_{num_qubits}qubits_{shots}circuits.pickle", "wb") as f:
            pickle.dump(result_list, f)

# get Hamiltonian
with open(f"{save_dir}QubitHamiltonian_H{num_qubits//2}_1.0.pickle", "rb") as file:
    hamiltonian = pickle.load(file)

shots = len(result_list)

#convert array
memory_arr = np.array([[i for i in m] for m in result_list], np.int8)

mapping_pauli = {"I": 0, "X": 1, "Y": 2, "Z": 3}
paulis = np.array(
    [[mapping_pauli[p] for p in spo.paulis[0].to_label()] for spo in hamiltonian],
    dtype=np.int8,
)
coeffs = hamiltonian.coeffs.real

#get expectation value
print("get expectation value")
if mean_load:
    with open(f"{save_dir}means_{num_qubits}qubits_{shots}circuits.pickle", "rb") as f:
        means = pickle.load(f)
    if num_qubits != len(result_list[0])//3 or shots != len(result_list):
        print(f"qubits input:{num_qubits}, expected:{len(result_list[0])//3}, circuits input{shots}, expected:{len(result_list)}")
        raise Exception("num qubits or circuits incorrect")
else:
    del result_list
    #get expectation values
    with concurrent.futures.ProcessPoolExecutor() as executor:
        history = np.array(
            list(
                executor.map(
                    partial(reconstruct_expval, paulis=paulis, coeffs=coeffs),
                    memory_arr,
                    chunksize=shots // os.cpu_count(),
                )
            ),
            dtype=np.float64,
        )
    means = np.cumsum(history) / np.arange(1, shots + 1)
    if mean_write:
        with open(f"{save_dir}means_{num_qubits}qubits_{shots}circuits.pickle", "wb") as f:
            pickle.dump(means, f)

#depiction
import matplotlib.pyplot as plt; plt.rcParams['figure.dpi'] = 300

plt.plot(means)
plt.hlines(hf_en, xmin=0, xmax=shots, colors="red")
plt.savefig(f"{save_dir}Energy_{num_qubits}qubits_{shots}circuits.svg")
plt.savefig(f"{save_dir}Energy_{num_qubits}qubits_{shots}circuits.png")
plt.clf()

plt.plot(np.abs(means - hf_en.real))
plt.xlim((1, shots))
plt.yscale("log")
plt.xscale("log")
plt.savefig(f"{save_dir}Energy_diff_{num_qubits}qubits_{shots}circuits.svg")
plt.savefig(f"{save_dir}Energy_diff_{num_qubits}qubits_{shots}circuits.png")

print("fin")
