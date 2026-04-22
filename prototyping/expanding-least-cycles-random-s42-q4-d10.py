import random
import pyzx

from qelebrimbor.common.attributes_zx import EdgeId
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
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.utilities.ring_making').setLevel(logging.INFO)
# logging.getLogger('qelebrimbor.utilities.blockgraph_constructor').setLevel(logging.INFO)
# logging.getLogger('qelebrimbor.vedo.scene_manager_bg').setLevel(logging.DEBUG)

random.seed(SEED)
if __name__ == "__main__":
    circuit = f"random-s{SEED}-q{QUBITS}-d{LAYERS}"
    zx = pyzx.generate.cnots(qubits = QUBITS, depth = LAYERS)

    with open(f"../assets/pyzx/{circuit}.json", 'w') as file:
        file.write(zx.to_json())

    vzx = VolumetricZxGraph.from_pyzx_graph(zx)
    CycleBasisAnalyser.analyse(vzx)
    cycles = CycleBasisAnalyser.decompose_nodes(vzx)

    index = 0
    cycle = cycles[index][6:] + cycles[index][:6]
    console.info(f"Cycle {index} : {cycle}")
    find_realisation(vzx, cycle, maximal_overhead = 2)

    # index = 5
    # cycle = cycles[index]
    # console.info(f"Cycle {index} : {cycle}")
    # find_completion(vzx, cycle, maximal_overhead = 8)

    # index = 6
    # cycle = cycles[index]
    # console.info(f"Cycle {index} : {cycle}")
    # find_completion(vzx, cycle, maximal_overhead = 8)

    # index = 4
    # cycle = cycles[index]
    # console.info(f"Cycle {index} : {cycle}")
    # find_completion(vzx, cycle, maximal_overhead = 4)
    #
    # index = 6
    # cycle = cycles[index]
    # console.info(f"Cycle {index} : {cycle}")
    # find_completion(vzx, cycle, maximal_overhead = 6)
    #
    # index = 5
    # cycle = cycles[index]
    # console.info(f"Cycle {index} : {cycle}")
    # find_completion(vzx, cycle, maximal_overhead = 6)
    #
    # index = 3
    # cycle = cycles[index]
    # console.info(f"Cycle {index} : {cycle}")
    # find_completion(vzx, cycle, maximal_overhead = 6)
    #
    # index = 2
    # cycle = cycles[index]
    # console.info(f"Cycle {index} : {cycle}")
    # find_completion(vzx, cycle, maximal_overhead = 6)

    # extend_unrealised(vzx)

    vzx.log_report()

    console.info(f"Realised nodes : {sum(1 for node in vzx.nodes if vzx.is_zx_node_realised(node))} of {vzx.number_of_nodes()}")
    console.info(f"Overall volume : {vzx.number_of_cubes()}")

    excess_volume: dict[EdgeId, int] = dict()
    for edge in vzx.get_zx_edges():
        if edge.is_realised():
            count = sum(1 for _ in edge.realisation) - 1
            if count > 0:
                excess_volume[edge] = count

    console.info(f"Excess volume : +{sum(excess_volume.values())}")
    for edge in excess_volume:
        console.info(f"> {edge} : +{excess_volume[edge]}")

    viewer = VolumetricZxGraphViewer(vzx, label = circuit)
    viewer.display()