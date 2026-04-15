import random
import pyzx

SEED = 27
QUBITS = 5
LAYERS = 20

import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)

random.seed(SEED)
if __name__ == "__main__":
    circuit = f"random-s{SEED}-q{QUBITS}-d{LAYERS}"
    zx = pyzx.generate.cnots(qubits = QUBITS, depth = LAYERS)

    with open(f"../assets/pyzx/{circuit}.json", 'w') as file:
        file.write(zx.to_json())