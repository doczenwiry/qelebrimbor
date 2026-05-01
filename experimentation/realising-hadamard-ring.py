#   Copyright 2026 Seweryn Dynerowicz
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from qelebrimbor.common.components import ZxNode, ZxEdge
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
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
logging.getLogger('qelebrimbor.vedo').setLevel(logging.INFO)

LENGTH = 6
MAX_OVERHEAD = 2 if LENGTH <= 5 else 1 if LENGTH % 2 != 0 else 0
if __name__ == "__main__":
    nodes = [ NodeType.Z for _ in range(LENGTH) ]
    edges = [ EdgeType.HADAMARD for _ in range(LENGTH)]

    zx_nodes = [ ZxNode(id = i, type = nodes[i]) for i in range(LENGTH) ]
    zx_edges = [ ZxEdge(source = zx_nodes[s], target = zx_nodes[(s+1) % LENGTH], type = edges[s]) for s in range(LENGTH)]

    vzx = VolumetricZxGraph(
        nodes = zip(range(LENGTH), nodes),
        edges = ( (s, (s + 1) % LENGTH, edges[s]) for s in range(LENGTH) )
    )

    vzx.log_summary()

    realisations = RingFinderBFS.find_minimal_rings(zx_nodes, zx_edges, number_sought = -1, maximal_overhead = MAX_OVERHEAD + 2)
    console.info(f"Found {len(realisations)} realisations for Hadamard Ring of length {LENGTH}")

    for realisation in realisations[:2]:
        console.info(f"> Realisation [{realisation.manhattan_length()}] : {realisation}")
        vzx = VolumetricZxGraph(
            nodes = zip(range(LENGTH), nodes),
            edges = ( (s, (s + 1) % LENGTH, edges[s]) for s in range(LENGTH) )
        )

        nodes_specifications = realisation.to_nodes_specifications(zx_nodes)
        console.info(f"Nodes specifications : {nodes_specifications}")
        BlockGraphConstructor.realise_nodes(graph= vzx, specifications = nodes_specifications)

        # Update the realising cubes of all zx_nodes involved
        for node in zx_nodes:
            node.realising_cube = vzx.get_zx_node(node.id).realising_cube
        for edge in zx_edges:
            edge.source.realising_cube = vzx.get_zx_node(edge.source.id).realising_cube
            edge.target.realising_cube = vzx.get_zx_node(edge.target.id).realising_cube

        edges_specifications = realisation.to_edges_specifications(zx_edges)
        console.info(f"Edges specifications : {edges_specifications}")
        BlockGraphConstructor.realise_edges(graph= vzx, specifications = edges_specifications)

        viewer = VolumetricZxGraphViewer(vzx, f"Hadamard Ring, n={LENGTH}", CycleLayout(vzx))
        viewer.display()