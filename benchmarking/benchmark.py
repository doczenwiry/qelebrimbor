#   Copyright 2026 Seweryn Dynerowicz
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import itertools
import os
import pathlib
import random
from enum import Enum

import pyzx

random.seed(42)
SEED_COUNT = 10
SEEDS = [int(random.random() * 4242424242) for _ in range(SEED_COUNT)]

BENCHMARK_DIRECTORY = pathlib.Path(__file__).resolve().parent

class Dataset(Enum):
    SMALL = 0
    MEDIO = 1
    LARGE = 2


DATASET_PARAMETERS: dict[str, dict[str, list[int]]] = {
    Dataset.SMALL.name: {"QUBITS": [4], "DEPTHS": [4, 8, 16, 32, 64, 128, 256, 512]}
}


def get_dataset_parameters(dataset: Dataset):
    return itertools.product(
        DATASET_PARAMETERS[dataset.name]["QUBITS"], DATASET_PARAMETERS[dataset.name]["DEPTHS"], SEEDS
    )


def get_dataset_directory(dataset: Dataset, hadamards: bool = False) -> str:
    return f"{BENCHMARK_DIRECTORY}/datasets/{dataset.name.lower()}/" + ("hadamard" if hadamards else "identity")


def get_dataset_filenames(dataset: Dataset) -> list[str]:
    return list(
        map(
            lambda parameters: (
                f"random-cnots-q{parameters[0]}-d{parameters[1]}-s{parameters[2]}.pyzx.json"  # noqa: E501
            ),
            get_dataset_parameters(dataset),
        )
    )


def dataset_detected(dataset: Dataset, hadamards: bool = False):
    directory = get_dataset_directory(dataset, hadamards)
    present_inputs = set(filter(lambda name: name.endswith(".pyzx.json"), os.listdir(directory)))
    dataset_inputs = set(get_dataset_filenames(dataset))

    return dataset_inputs.issubset(present_inputs)


def generate_dataset(dataset: Dataset, hadamards: bool = False):
    directory = get_dataset_directory(dataset, hadamards)
    for qubits, depth, seed in get_dataset_parameters(dataset):
        random.seed(seed)
        filename = f"random-cnots-q{qubits}-d{depth}-s{seed}"
        if hadamards:
            circuit = pyzx.generate.CNOT_HAD_PHASE_circuit(qubits=qubits, depth=depth, p_had=0.2, p_t=0.0, seed=seed)
            zx = circuit.to_graph()
        else:
            zx = pyzx.generate.cnots(qubits=qubits, depth=depth)

        with open(f"{directory}/{filename}.pyzx.json", "w") as file:
            file.write(zx.to_json())
