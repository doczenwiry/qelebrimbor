import random
import pyzx

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.utilities.least_cycle_analyser import MinimalCycleBasisAnalyser
from qelebrimbor.utilities.ring_making import find_realisation, find_completion, extend_unrealised
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

SEED = 42
QUBITS = 4
LAYERS = 10

import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.utilities.ring_making').setLevel(logging.DEBUG)
logging.getLogger('qelebrimbor.utilities.blockgraph_constructor').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders.pathfinder_dfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.ringfinders.ringfinder_bfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.vedo').setLevel(logging.CRITICAL)

random.seed(SEED)
if __name__ == "__main__":
    circuit = f"random-s{SEED}-q{QUBITS}-d{LAYERS}"
    zx = pyzx.generate.cnots(qubits = QUBITS, depth = LAYERS)

    with open(f"../assets/pyzx/{circuit}.json", 'w') as file:
        file.write(zx.to_json())

    vzx = VolumetricZxGraph.from_pyzx_graph(zx)

    MinimalCycleBasisAnalyser.analyse(vzx)

    cycles = MinimalCycleBasisAnalyser.decompose(vzx)

    idx = 0
    cycle = cycles[idx]
    console.info(f"Cycle {idx} : {cycle}")
    find_realisation(vzx, cycle)
    vzx.set_realising_cube(12, 43)
    vzx.alter_cube_kind(36, CubeKind.ZZX)
    vzx.set_realising_cube(21, 36)

    cycle_order = [1, 3, 4, 6, 5, 2]
    for index in range(4):
        cycle = cycles[cycle_order[index]]
        console.info(f"Cycle {index+1} : {cycle}")
        find_completion(graph = vzx, cycle = cycle)

    # extend_unrealised(vzx)
    # extend_unrealised(vzx)
    # extend_unrealised(vzx)

    vzx.log_summary(cubes = True)

    console.info(f"Realised nodes : {sum(1 for node in vzx.nodes if vzx.is_node_realised(node))} of {vzx.number_of_nodes()}")
    console.info(f"Overall volume : {vzx.number_of_cubes()}")

    viewer = VolumetricZxGraphViewer(vzx, label = circuit)
    viewer.display()