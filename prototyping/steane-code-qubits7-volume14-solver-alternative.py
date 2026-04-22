import pyzx

from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser
from qelebrimbor.utilities.ring_making import find_realisation, find_completion

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.vedo.zx_layout.hexagon import HexagonLayout
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.helpers.blockgraph').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders.pathfinder_dfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.ringfinders.ringfinder_bfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.utilities.ring_making').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.utilities.blockgraph_constructor').setLevel(logging.DEBUG)
logging.getLogger('qelebrimbor.vedo').setLevel(logging.CRITICAL)

if __name__ == "__main__":
    with open("../assets/pyzx/steane-code-qubits7-spiders7.json", 'r') as file:
        pyzx_graph = pyzx.Graph().from_json(file.read())

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_graph)

    CycleBasisAnalyser.analyse(vzx)
    cycles = CycleBasisAnalyser.decompose_nodes(vzx)

    index = 0
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_realisation(vzx, cycle, maximal_overhead = 4)

    index = 1
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 4)

    index = 2
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 4)

    # extend_unrealised(vzx)

    vzx.log_report()

    hexagon = HexagonLayout(graph = vzx, nodes = [0,2,4,5,6,3], extras = { 1 : (0.0, 0.0), 7 : (0.7, 1.0 / 6.0) })
    viewer = VolumetricZxGraphViewer(graph= vzx, label ="steane-code-7", layout = hexagon)
    viewer.display()