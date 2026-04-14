import random
import pyzx

import qelebrimbor
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.utilities.cycle_analyser import CycleAnalyser

SEED = 42
QUBITS = 4
LAYERS = 10

import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)
logging.getLogger('qelebrimbor.ringfinders.ringfinder_bfs').setLevel(logging.INFO)

random.seed(SEED)
if __name__ == "__main__":
    circuit = f"random-s{SEED}-q{QUBITS}-d{LAYERS}"
    zx = pyzx.generate.cnots(qubits = QUBITS, depth = LAYERS)
    pyzx.full_reduce(zx)
    pyzx.draw(zx, labels = True)

    with open(f"../assets/pyzx/{circuit}.json", 'w') as file:
        file.write(zx.to_json())

    vzx = VolumetricZxGraph.from_pyzx_graph(zx)

    CycleAnalyser.analyse(vzx)

    cycles = CycleAnalyser.decompose(vzx)
    cycle0 = cycles[0]
    edges0 = [ (cycle0[i], cycle0[(i+1) % len(cycle0)]) for i in range(len(cycle0)) ]
    n0 = len(cycle0)

    nodes0 = list(map(lambda nd : vzx.get_node_type(nd), cycle0))
    pipes0 = list(map(lambda ed : vzx.get_edge_type(*ed), edges0))
    console.info(f"Nodes 0 : {" ".join(map(lambda nd: str(nd) + ':' + str(vzx.get_node_type(nd)), cycle0))}")
    console.info(f"Edges 0 : {" ".join(map(lambda ed: str(ed) + ':' + str(vzx.get_edge_type(*ed)), edges0))}")

    ring0 = RingFinderBFS.find_minimal_rings(nodes0, pipes0, maximal_overhead = 4)[0]
    c0 = len(ring0.cubes)
    console.info(f"> Cycle 0 [{c0}]: {ring0.cubes}")

    viewer = VolumetricZxGraphViewer(vzx, label = circuit)
    viewer.display()