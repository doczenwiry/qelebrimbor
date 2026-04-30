import pyzx
import random

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SEED = 42
QUBITS = 8
LAYERS = 32

random.seed(SEED)
if __name__ == "__main__":
    circuit = f"random-cnots-seed={SEED}-qubits={QUBITS}-depth={LAYERS}"
    zx = pyzx.generate.cnots(qubits = QUBITS, depth = LAYERS)

    with open(f"../assets/pyzx/random/{circuit}.json", 'w') as file:
        file.write(zx.to_json())