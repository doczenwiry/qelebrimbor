import pyzx
import random
from argparse import ArgumentParser

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

parser = ArgumentParser(
    prog = "generate-random-circuit",
    description = "A script to generate a random circuit using PyZX facilities."
)
parser.add_argument('-s', '--seed')
parser.add_argument('-q', '--qubits')
parser.add_argument('-d', '--depth')
args = parser.parse_args()

if __name__ == "__main__":
    args = parser.parse_args()

    random.seed(int(args.seed))
    circuit = f"random-cnots-s{args.seed}-q{args.qubits}-d{args.depth}"
    zx = pyzx.generate.cnots(qubits = int(args.qubits), depth = int(args.depth))

    with open(f"../assets/pyzx/random/{circuit}.json", 'w') as file:
        file.write(zx.to_json())