import random
from time import time

import pyzx

from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser
from qelebrimbor.utilities.ring_making import find_realisation, find_completion, extend_unrealised
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

SEED = 42
QUBITS = 4
LAYERS = 10

import logging
logging.basicConfig(level=logging.CRITICAL)
console = logging.getLogger(__name__)

random.seed(SEED)
if __name__ == "__main__":
    circuit = f"random-s{SEED}-q{QUBITS}-d{LAYERS}"
    pyzx_input = pyzx.generate.cnots(qubits = QUBITS, depth = LAYERS)

    with open(f"../assets/pyzx/random/{circuit}.json", 'w') as file:
        file.write(pyzx_input.to_json())

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_input)
    CycleBasisAnalyser.analyse(vzx)
    cycles = CycleBasisAnalyser.decompose_nodes(vzx)

    index = 0
    cycle = cycles[index][6:] + cycles[index][:6]
    console.info(f"Cycle {index} : {cycle}")
    find_realisation(vzx, cycle, maximal_overhead = 2)

    index = 5
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 8)

    index = 6
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 8)

    index = 4
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 4)

    index = 3
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 6)

    index = 2
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 6)

    index = 1
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 6)

    extend_unrealised(vzx)
    extend_unrealised(vzx)
    extend_unrealised(vzx)

    vzx.log_report()

    console.info(f"Realised nodes : {sum(1 for node in vzx.get_zx_nodes() if node.is_realised())} of {vzx.number_of_nodes()}")
    console.info(f"Overall volume : {vzx.number_of_cubes()}")

    viewer = VolumetricZxGraphViewer(vzx, label = circuit)
    viewer.display()

    pyzx_output = vzx.to_pyzx_graph(filepath =f"../assets/pyzx/random/{circuit}-blockgraph.json")
    pyzx.draw(pyzx_input, labels=True)
    pyzx.draw(pyzx_output, labels=True)