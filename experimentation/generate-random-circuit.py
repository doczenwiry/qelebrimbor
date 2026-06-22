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

import logging
import random
from argparse import ArgumentParser

import pyzx

console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

parser = ArgumentParser(
    prog="generate-random-circuit",
    description="A script to generate a random circuit using PyZX facilities.",
)
parser.add_argument("-s", "--seed")
parser.add_argument("-q", "--qubits")
parser.add_argument("-d", "--depth")
args = parser.parse_args()

if __name__ == "__main__":
    args = parser.parse_args()

    random.seed(int(args.seed))
    circuit = f"random-cnots-s{args.seed}-q{args.qubits}-d{args.depth}"
    zx = pyzx.generate.cnots(qubits=int(args.qubits), depth=int(args.depth))

    with open(f"../assets/pyzx/random/{circuit}.pyzx.json", "w") as file:
        file.write(zx.to_json())
