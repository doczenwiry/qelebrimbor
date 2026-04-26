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
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.utilities.blockgraph_constructor').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders.pathfinder_dfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.ringfinders.ringfinder_bfs').setLevel(logging.CRITICAL)

LENGTH = 4
MAX_OVERHEAD = 2 if LENGTH <= 5 else 1 if LENGTH % 2 != 0 else 0
if __name__ == "__main__":
    nodes = [ NodeType.X if i % 2 == 0 else NodeType.Z for i in range(LENGTH) ]
    edges = [ EdgeType.IDENTITY for s in range(LENGTH)]

    zx_nodes = [ ZxNode(id = i, type = nodes[i]) for i in range(LENGTH) ]
    zx_edges = [ ZxEdge(source = zx_nodes[s], target = zx_nodes[(s+1) % LENGTH], type = edges[s]) for s in range(LENGTH)]

    rings = RingFinderBFS.find_minimal_rings(zx_nodes, zx_edges, number_sought = -1, maximal_overhead = MAX_OVERHEAD + 4)
    console.info(f"Found {len(rings)} rings of length {LENGTH}")

    for realisation in rings[:1]:
        cubes = realisation.manhattan_length()
        console.info(f"> Realisation [{cubes}] : {realisation}")
        vzx = VolumetricZxGraph(
            nodes = zip(range(LENGTH), nodes),
            edges = zip( ((s, (s + 1) % LENGTH) for s in range(LENGTH)), edges)
        )

        BlockGraphConstructor.realise_nodes(graph= vzx, specifications = realisation.to_nodes_specifications(zx_nodes))

        vzx.log_summary()

        edges_specifications = realisation.to_edges_specifications(zx_edges)

        console.info(f"Edges specifications :")
        for edge, proposal in edges_specifications.items():
            console.info(f"> Edge [{edge}] : {proposal}")

        BlockGraphConstructor.realise_edges(graph= vzx, specifications = realisation.to_edges_specifications(zx_edges))

        viewer = VolumetricZxGraphViewer(vzx, f"Identity Ring, n={LENGTH}", CycleLayout(vzx))
        viewer.display()