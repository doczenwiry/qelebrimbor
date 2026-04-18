from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.attributes_zx import NodeId, NodeType, EdgeType
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.cycle import CycleLayout

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('qelebrimbor').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.DEBUG)
logging.getLogger('qelebrimbor.utilities.blockgraph_constructor').setLevel(logging.DEBUG)

LENGTH = 4
MAX_OVERHEAD = 2 if LENGTH <= 5 else 1 if LENGTH % 2 != 0 else 0
if __name__ == "__main__":
    nodes = [ NodeType.X if i % 2 == 0 else NodeType.Z for i in range(LENGTH) ]
    edges = [ EdgeType.IDENTITY for s in range(LENGTH)]

    rings = RingFinderBFS.find_minimal_rings(nodes, edges, number_sought = -1, maximal_overhead = MAX_OVERHEAD + 4)
    console.info(f"Found {len(rings)} rings of length {LENGTH}")

    for realisation in rings[:1]:
        cubes = len(realisation.cubes)
        console.info(f"> Realisation [{cubes}] : {realisation}")
        ring = VolumetricZxGraph(
            nodes = zip(range(LENGTH), nodes),
            edges = zip( ((s, (s + 1) % LENGTH) for s in range(LENGTH)), edges)
        )

        nodes_specifications: dict[NodeId, tuple[CubeKind, Coordinates]] = {
            nd: realisation.cubes[nd] for nd in range(ring.number_of_nodes())
        }

        BlockGraphConstructor.realise_nodes(ring,
            specifications = {
                nd: realisation.cubes[nd] for nd in range(ring.number_of_nodes())
            }
        )

        BlockGraphConstructor.realise_edges(ring,
            specifications = {
                (0, LENGTH - 1) : PathSpecification(
                    source_cube = ring.get_zx_node(0).realising_cube,
                    target_cube = ring.get_zx_node(LENGTH - 1).realising_cube,
                    extras = list(reversed(realisation.cubes[LENGTH:cubes])),
                    pipes = [EdgeType.IDENTITY for _ in range(LENGTH)]
                )
            }
        )

        viewer = VolumetricZxGraphViewer(ring, f"Identity Ring, n={LENGTH}", CycleLayout(ring))
        viewer.display()