import pyzx
import random

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SEED = 42
QUBITS = 5
LAYERS = 100

random.seed(SEED)
if __name__ == "__main__":
    circuit = f"random-s{SEED}-q{QUBITS}-d{LAYERS}"
    zx = pyzx.generate.cnots(qubits = QUBITS, depth = LAYERS)
    # pyzx.draw(zx, labels = True)

    with open(f"../assets/pyzx/random/{circuit}.json", 'w') as file:
        file.write(zx.to_json())