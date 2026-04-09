from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.components_zx import NodeId, NodeType, EdgeType
from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.cycle import CycleLayout

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('qelebrimbor').setLevel(logging.CRITICAL)

def generate_ring(order: int) -> VolumetricZxGraph:
    n = 2 * order
    nodes = [ (s, NodeType.X if s % 2 == 0 else NodeType.Z) for s in range(n) ]
    edges = [ ( (s,(s+1) % n), EdgeType.IDENTITY) for s in range(n) ]
    return VolumetricZxGraph(nodes, edges)

ORDER = 4
LENGTH = 2*ORDER

# TODO: figure out how to realise such rings ...

if __name__ == "__main__":
    rings = RingFinderBFS.find_minimal_alternating_rings(ORDER, maximal_overhead = 0, number_sought = -1)
    console.info(f"Found {len(rings)} rings of length {LENGTH}")
    for realisation in rings:
        console.info(f"> {realisation}")
        ring = generate_ring(order = ORDER)

        nodes_specifications: dict[NodeId, tuple[CubeKind, Coordinates]] = {
            nd: realisation.cubes[nd] for nd in range(ring.number_of_nodes())
        }

        BlockGraphConstructor.realise(ring, nodes_specifications, {})

        viewer = VolumetricZxGraphViewer(ring, f"alternating ring, n={LENGTH}", CycleLayout(ring))
        viewer.display()