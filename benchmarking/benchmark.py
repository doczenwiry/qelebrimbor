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
import random

import pyzx

random.seed(42)

DATASET_PARAMETERS = {"small": {"QUBITS": [4, 8, 16, 32], "DEPTHS": [4, 8, 16, 32]}}
DATASET = "small"
DATASET_DIRECTORY = f"../benchmarking/datasets/{DATASET}"

SEED_COUNT = 10
SEEDS = [int(random.random() * 4242424242) for _ in range(SEED_COUNT)]
QUBITS = DATASET_PARAMETERS[DATASET]["QUBITS"]
DEPTHS = DATASET_PARAMETERS[DATASET]["DEPTHS"]


def get_dataset_filenames(prefix: str | None = None) -> list[str]:
    return list(
        map(
            lambda parameters: (
                f"{(prefix + '/') if prefix else ''}random-cnots-q{parameters[0]}-d{parameters[1]}-s{parameters[2]}.pyzx.json"  # noqa: E501
            ),
            itertools.product(QUBITS, DEPTHS, SEEDS),
        )
    )


def dataset_detected():
    present_inputs = set(filter(lambda name: name.endswith(".pyzx.json"), os.listdir(DATASET_DIRECTORY)))
    dataset_inputs = set(get_dataset_filenames())

    return dataset_inputs.issubset(present_inputs)


def generate_dataset():
    for seed, qubits, depth in itertools.product(SEEDS, QUBITS, DEPTHS):
        random.seed(seed)
        circuit = f"random-cnots-q{qubits}-d{depth}-s{seed}"
        zx = pyzx.generate.cnots(qubits=qubits, depth=depth)

        with open(f"{DATASET_DIRECTORY}/{circuit}.pyzx.json", "w") as file:
            file.write(zx.to_json())
