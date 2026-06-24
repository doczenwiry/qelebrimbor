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

from qelebrimbor.analysis.biconnected_components import BiconnectedComponentsAnalyser
from qelebrimbor.analysis.connected_components import ConnectedComponentsAnalyser
from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.formats.preprocessing.bialgebra_reduction import BialgebraReduction
from qelebrimbor.formats.preprocessing.full_reduction import FullReduction
from qelebrimbor.formats.pyzx import PYZX


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
        self.hadamards = hadamards
        self.qubits = Benchmark.__DATASET_PARAMETERS[dataset.name]["QUBITS"]
        self.layers = Benchmark.__DATASET_PARAMETERS[dataset.name]["LAYERS"]
        self.sample_count = Benchmark.__ROBUST_COUNT if robust else Benchmark.__QUICK_COUNT
        dataset_part = f"datasets/{dataset.name.lower()}"
        hadamard_part = "hadamard" if self.hadamards else "identity"
        sample_count_part = "robust" if robust else "quick"
        self.__directory = str(pathlib.Path(__file__).resolve().parent)
        self.__directory += "/" + dataset_part + "/" + hadamard_part + "/" + sample_count_part

    @property
    def directory(self) -> str:
        return self.__directory

    @property
    def parameters(self):
        return itertools.product(self.qubits, self.layers)

    @property
    def filenames(self) -> list[str]:
        filenames = []
        listing = os.listdir(self.__directory)
        for qubits, depth in self.parameters:
            p_filenames = sorted(
                filter(
                    lambda name: name.startswith(f"random-cnots-q{qubits}-d{depth}") and name.endswith(".pyzx.json"),
                    listing,
                )
            )
            filenames.extend(p_filenames)
        return filenames

    def dataset_detected(self):
        for qubits, depth in self.parameters:
            files_present = sum(
                1
                for name in self.filenames
                if name.startswith(f"random-cnots-q{qubits}-d{depth}") and name.endswith(".pyzx.json")
            )
            if files_present < self.sample_count:
                return False

        return True

    def generate_dataset(self):
        random.seed(42)
        directory = self.directory
        for qubits, depth in self.parameters:
            count: int = 0
            while count < self.sample_count:
                seed = int(random.random() * 4242424242)
                random.seed(seed)
                if self.hadamards:
                    circuit = pyzx.generate.CNOT_HAD_PHASE_circuit(qubits=qubits, depth=depth, p_had=0.2, p_t=0.0)
                    zx = circuit.to_graph()
                else:
                    zx = pyzx.generate.cnots(qubits=qubits, depth=depth)

                internal_zx = FullReduction.process(zx)
                internal_zx = BialgebraReduction.process(internal_zx)
                vzx = PYZX.from_pyzx_graph(internal_zx)
                cc_count = ConnectedComponentsAnalyser.count(vzx)
                bcc_count = BiconnectedComponentsAnalyser.count(vzx)
                if CycleAnalyser.has_cycles(vzx) and cc_count == 1 and bcc_count == 1:
                    filename = f"random-cnots-q{qubits}-d{depth}-s{seed}"
                    with open(f"{directory}/{filename}.pyzx.json", "w") as file:
                        file.write(zx.to_json())
                    count += 1
