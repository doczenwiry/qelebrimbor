import random
import pyzx

from qelebrimbor.common.attributes_zx import EdgeId
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
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
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.DEBUG)
logging.getLogger('qelebrimbor.utilities.ring_making').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.utilities.blockgraph_constructor').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders.pathfinder_dfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.ringfinders.ringfinder_bfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.vedo').setLevel(logging.INFO)

random.seed(SEED)
if __name__ == "__main__":
    circuit = f"random-s{SEED}-q{QUBITS}-d{LAYERS}"
    zx = pyzx.generate.cnots(qubits = QUBITS, depth = LAYERS)

    with open(f"../assets/pyzx/{circuit}.json", 'w') as file:
        file.write(zx.to_json())

    vzx = VolumetricZxGraph.from_pyzx_graph(zx)
    MinimalCycleBasisAnalyser.analyse(vzx)
    cycles = MinimalCycleBasisAnalyser.decompose(vzx)

    index = 0
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_realisation(vzx, cycle, maximal_overhead = 2)

    index = 1
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle)

    index = 4
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle)
    # BlockGraphConstructor.realise_nodes(vzx,
    #     specifications = {
    #         22 : BgCube(CubeKind.XXZ, Coordinates( 2, 0, 0)),
    #     }
    # )
    # BlockGraphConstructor.realise_edges(vzx, {})

    # index = 6
    # cycle = cycles[index]
    # console.info(f"Cycle {index} : {cycle}")
    # find_completion(vzx, cycle)
    #
    # index = 5
    # cycle = cycles[index]
    # console.info(f"Cycle {index} : {cycle}")
    # find_completion(vzx, cycle)
    #
    # index = 3
    # cycle = cycles[index]
    # console.info(f"Cycle {index} : {cycle}")
    # find_completion(vzx, cycle)
    #
    # index = 2
    # cycle = cycles[index]
    # console.info(f"Cycle {index} : {cycle}")
    # find_completion(vzx, cycle)

    # extend_unrealised(vzx)
    # extend_unrealised(vzx)
    # extend_unrealised(vzx)

    # vzx.log_summary(cubes = True)

    console.info(f"Realised nodes : {sum(1 for node in vzx.nodes if vzx.is_zx_node_realised(node))} of {vzx.number_of_nodes()}")
    console.info(f"Overall volume : {vzx.number_of_cubes()}")

    excess_volume: dict[EdgeId, int] = dict()
    for edge in vzx.edges:
        if vzx.is_zx_edge_realised(*edge):
            count = len(vzx.get_zx_edge(*edge).realisation) - 1
            if count > 0:
                excess_volume[edge] = count

    console.info(f"Excess volume : +{sum(excess_volume.values())}")
    for edge in excess_volume:
        console.info(f"> {edge} : +{excess_volume[edge]}")

    viewer = VolumetricZxGraphViewer(vzx, label = circuit)
    viewer.display()