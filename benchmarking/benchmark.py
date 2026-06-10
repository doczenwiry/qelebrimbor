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


class Dataset(Enum):
    SMALL = 0
    MEDIO = 1
    LARGE = 2


class Benchmark:
    __QUICK_COUNT: int = 10
    __ROBUST_COUNT: int = 100
    __DATASET_PARAMETERS: dict[str, dict[str, list[int]]] = {
        Dataset.SMALL.name: {"QUBITS": [4], "LAYERS": [4, 8, 16, 32, 64, 128, 256, 512, 1024]}
    }

    def __init__(self, dataset: Dataset, robust: bool = False, hadamards: bool = False):
        random.seed(42)
        self.seeds = [
            int(random.random() * 4242424242)
            for _ in range(Benchmark.__ROBUST_COUNT if robust else Benchmark.__QUICK_COUNT)
        ]
        self.hadamards = hadamards
        self.qubits = Benchmark.__DATASET_PARAMETERS[dataset.name]["QUBITS"]
        self.layers = Benchmark.__DATASET_PARAMETERS[dataset.name]["LAYERS"]
        dataset_part = f"datasets/{dataset.name.lower()}"
        hadamard_part = "hadamard" if self.hadamards else "identity"
        self.__directory = str(pathlib.Path(__file__).resolve().parent) + "/" + dataset_part + "/" + hadamard_part

    @property
    def directory(self) -> str:
        return self.__directory

    @property
    def parameters(self):
        return itertools.product(self.qubits, self.layers, self.seeds)

    @property
    def filenames(self) -> list[str]:
        return list(
            map(
                lambda parameters: f"random-cnots-q{parameters[0]}-d{parameters[1]}-s{parameters[2]}.pyzx.json",
                self.parameters,
            )
        )

    def dataset_detected(self):
        present_inputs = set(filter(lambda name: name.endswith(".pyzx.json"), os.listdir(self.directory)))
        dataset_inputs = set(self.filenames)

        return dataset_inputs.issubset(present_inputs)

    def generate_dataset(self):
        directory = self.directory
        for qubits, depth, seed in self.parameters:
            random.seed(seed)
            filename = f"random-cnots-q{qubits}-d{depth}-s{seed}"
            if self.hadamards:
                circuit = pyzx.generate.CNOT_HAD_PHASE_circuit(qubits=qubits, depth=depth, p_had=0.2, p_t=0.0)
                zx = circuit.to_graph()
            else:
                zx = pyzx.generate.cnots(qubits=qubits, depth=depth)

            with open(f"{directory}/{filename}.pyzx.json", "w") as file:
                file.write(zx.to_json())
