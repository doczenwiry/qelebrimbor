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

import os

import pyzx
import random
import itertools

import logging
logging.basicConfig(level=logging.INFO)

DATASET_PARAMETERS = {
    'small' : {
        'QUBITS' : [4, 8, 16],
        'DEPTHS' : [4, 8, 16]
    }
}
DATASET = 'small'
DATASET_DIRECTORY = f"../benchmarking/datasets/{DATASET}"

random.seed(42)
SEEDS = [ int(random.random() * 4242424242) for _ in range(10) ]
QUBITS = DATASET_PARAMETERS[DATASET]['QUBITS']
DEPTHS = DATASET_PARAMETERS[DATASET]['DEPTHS']

def dataset_detected():
    return len(os.listdir(DATASET_DIRECTORY)) > 0

def generate_dataset():
    if dataset_detected():
        print(f"Existing dataset found in {DATASET_DIRECTORY}. Aborting generation.")
        exit(0)

    print(f"Seeds generated : {SEEDS}")

    for seed, qubits, depth in itertools.product(SEEDS, QUBITS, DEPTHS):
        random.seed(seed)
        circuit = f"random-cnots-q{qubits}-d{depth}-s{seed}"
        zx = pyzx.generate.cnots(qubits = qubits, depth = depth)

        print(f"Generating circuit {circuit}")

        with open(f"{DATASET_DIRECTORY}/{circuit}.json", 'w') as file:
            file.write(zx.to_json())

if __name__ == "__main__":
    print(f"Benchmarking dataset {DATASET}")

    if not dataset_detected():
        generate_dataset()

    for input_file in os.listdir(DATASET_DIRECTORY):
        os.system(f"python ../qb.py -s {DATASET_DIRECTORY}/{input_file}")