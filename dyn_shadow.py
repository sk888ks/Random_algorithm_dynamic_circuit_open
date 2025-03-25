from math import acos, sqrt

import numpy as np
from qiskit import QuantumCircuit

def generage_dynamic_shadow_circuit_nonest(target_circuit: QuantumCircuit) -> QuantumCircuit:
    num_qubits = target_circuit.num_qubits
    qc = QuantumCircuit(num_qubits, num_qubits * 3)
    qc.ry(2 * acos(sqrt(2 / 3)), range(num_qubits))
    qc.measure(range(num_qubits), range(num_qubits))
    qc.reset(range(num_qubits))
    qc.ry(2 * acos(sqrt(1 / 2)), range(num_qubits))
    qc.measure(range(num_qubits), range(num_qubits, num_qubits * 2))

    qc.reset(range(num_qubits))
    qc.compose(target_circuit, range(num_qubits), inplace=True)

    for i in range(num_qubits):
        with qc.if_test((qc.clbits[i], 0)):
            qc.h(i)
            # if 1 -> Z measurement
        with qc.if_test((qc.clbits[2 * num_qubits + i], 1)):
            # if 0 -> X measurement
            # if 1 -> Y measurement
            qc.sdg(i)

    qc.measure(range(num_qubits), range(num_qubits * 2, num_qubits * 3))
    return qc


def reconstruct_expval(
    measurement_outcome: np.ndarray,
    paulis: np.ndarray,
    coeffs: np.ndarray,
) -> float:
    """Notation is from https://doi.org/10.1007/s00220-022-04343-8"""
    bitlen = len(measurement_outcome)
    num_qubits = paulis.shape[1]
    outcome = measurement_outcome[0 : bitlen // 3]
    x_or_y = measurement_outcome[
        bitlen // 3 : 2 * bitlen // 3
    ]  # if 0 then X=1, if 1 then Y=2
    z_or_not = measurement_outcome[2 * bitlen // 3 :]  # if 1 then Z=3
    pauli_meas = 1 + x_or_y + z_or_not * 2
    np.clip(pauli_meas, 1, 3, out=pauli_meas)

    non_zero = paulis * pauli_meas != 0
    num_zero = np.count_nonzero(paulis * pauli_meas == 0, axis=1)
    tmp = paulis * pauli_meas
    num_dup = np.count_nonzero((tmp == 1) | (tmp == 4) | (tmp == 9), axis=1)

    hit = num_dup + num_zero == num_qubits

    alpha = coeffs[hit]
    f = 3 ** num_dup[hit]

    outcome = np.array([o for o in outcome], dtype=np.int8)
    mu = -2 * (np.count_nonzero(outcome * paulis[hit], axis=1) % 2) + 1
    return np.sum(alpha * f * mu)
