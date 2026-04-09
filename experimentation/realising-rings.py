from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.components_zx import NodeId, NodeType, EdgeType
from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.cycle import CycleLayout

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('qelebrimbor').setLevel(logging.CRITICAL)

if __name__ == "__main__":
    n = 6
    mo = 2 if n <= 5 else 1 if n % 2 != 0 else 0

    nodes = [ NodeType.X if i % 2 == 0 else NodeType.Z for i in range(n) ]
    edges = [ ( (s, (s + 1) % n) , EdgeType.IDENTITY ) for s in range(n) ]

    rings = RingFinderBFS.find_minimal_rings(nodes, number_sought = -1, maximal_overhead = mo)

    console.info(f"Found {len(rings)} rings of length {n}")

    for realisation in rings:
        cubes = len(realisation.cubes)
        console.info(f"> Realisation [{cubes}] : {realisation}")
        ring = VolumetricZxGraph(zip(range(n), nodes), edges)

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
                (n-1, 0) : PathSpecification(
                    source_cube = min(ring.get_realising_cubes(n-1)),
                    target_cube = min(ring.get_realising_cubes(0)),
                    extras = realisation.cubes[n:cubes],
                    pipes = [ EdgeType.IDENTITY for _ in range(n) ]
                )
            }
        )

        viewer = VolumetricZxGraphViewer(ring, f"alternating ring, n={n}", CycleLayout(ring))
        viewer.display()