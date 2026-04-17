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
logging.basicConfig(level=logging.INFO)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.CRITICAL)

LENGTH = 6
MAX_OVERHEAD = 2 if LENGTH <= 5 else 1 if LENGTH % 2 != 0 else 0
if __name__ == "__main__":
    nodes = [ NodeType.Z for _ in range(LENGTH) ]
    edges = [ EdgeType.HADAMARD for _ in range(LENGTH)]

    ring = VolumetricZxGraph(
        nodes = zip(range(LENGTH), nodes),
        edges = zip( ((s, (s + 1) % LENGTH) for s in range(LENGTH)), edges)
    )

    ring.log_summary()

    realisations = RingFinderBFS.find_minimal_rings(nodes, edges, number_sought = -1, maximal_overhead = MAX_OVERHEAD + 2)
    console.info(f"Found {len(realisations)} realisations for Hadamard Ring of length {LENGTH}")

    for realisation in realisations[:2]:
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
                (0, LENGTH-1) : PathSpecification(
                    source_cube = ring.get_realising_cube(0),
                    target_cube = ring.get_realising_cube(LENGTH - 1),
                    extras = list(reversed(realisation.cubes[LENGTH:cubes])),
                    pipes = [EdgeType.IDENTITY if i != LENGTH-1 else EdgeType.HADAMARD for i in range(LENGTH)]
                )
            }
        )

        viewer = VolumetricZxGraphViewer(ring, f"Identity Ring, n={LENGTH}", CycleLayout(ring))
        viewer.display()