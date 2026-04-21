from qelebrimbor.common.components import ZxNode, ZxEdge
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
logging.getLogger('qelebrimbor.pathfinders.pathfinder_dfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.ringfinders.ringfinder_bfs').setLevel(logging.CRITICAL)

LENGTH = 6
MAX_OVERHEAD = 2 if LENGTH <= 5 else 1 if LENGTH % 2 != 0 else 0
if __name__ == "__main__":
    nodes = [ NodeType.Z for _ in range(LENGTH) ]
    edges = [ EdgeType.HADAMARD for _ in range(LENGTH)]

    zx_nodes = [ ZxNode(id = i, type = nodes[i]) for i in range(LENGTH) ]
    zx_edges = [ ZxEdge(source = s, target = (s+1) % LENGTH, type = edges[s]) for s in range(LENGTH)]

    vzx = VolumetricZxGraph(
        nodes = zip(range(LENGTH), nodes),
        edges = zip( ((s, (s + 1) % LENGTH) for s in range(LENGTH)), edges)
    )

    vzx.log_summary()

    realisations = RingFinderBFS.find_minimal_rings(zx_nodes, zx_edges, number_sought = -1, maximal_overhead = MAX_OVERHEAD + 2)
    console.info(f"Found {len(realisations)} realisations for Hadamard Ring of length {LENGTH}")

    for realisation in realisations[:2]:
        cubes = realisation.manhattan_length()
        console.info(f"> Realisation [{cubes}] : {realisation}")
        vzx = VolumetricZxGraph(
            nodes = zip(range(LENGTH), nodes),
            edges = zip( ((s, (s + 1) % LENGTH) for s in range(LENGTH)), edges)
        )

        nodes_specifications = realisation.to_nodes_specifications(zx_nodes)
        console.info(f"Nodes specifications : {nodes_specifications}")
        BlockGraphConstructor.realise_nodes(graph= vzx, specifications = nodes_specifications)

        edges_specifications = realisation.to_edges_specifications(vzx, zx_edges)
        console.info(f"Edges specifications : {edges_specifications}")
        BlockGraphConstructor.realise_edges(graph= vzx, specifications = edges_specifications)


        # nodes_specifications: dict[NodeId, tuple[CubeKind, Coordinates]] = {
        #     nd: realisation.extras[nd] for nd in range(ring.number_of_nodes())
        # }
        #
        # BlockGraphConstructor.realise_nodes(ring,
        #     specifications = {
        #         nd: realisation.extras[nd] for nd in range(ring.number_of_nodes())
        #     }
        # )
        #
        # BlockGraphConstructor.realise_edges(ring,
        #     specifications = {
        #         (0, LENGTH-1) : PathSpecification(
        #             source_cube= ring.get_zx_node(0).realising_cube,
        #             target_cube= ring.get_zx_node(LENGTH - 1).realising_cube,
        #             extras = list(reversed(realisation.extras[LENGTH:cubes])),
        #             pipes = [EdgeType.IDENTITY if i != LENGTH-1 else EdgeType.HADAMARD for i in range(LENGTH)]
        #         )
        #     }
        # )

        viewer = VolumetricZxGraphViewer(vzx, f"Hadamard Ring, n={LENGTH}", CycleLayout(vzx))
        viewer.display()