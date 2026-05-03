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

from time import time

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.components import BgCube

from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.spacetime.pathfinders.depth_first_search import PathfinderDFS
from qelebrimbor.spacetime.pathfinders.dijkstra import PathfinderDijkstra

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.circuit import CircuitLayout

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("qelebrimbor").setLevel(logging.CRITICAL)
logging.getLogger("qelebrimbor.spacetime").setLevel(logging.INFO)
logging.getLogger("matplotlib").setLevel(logging.WARNING)

if __name__ == "__main__":
    for d in [ 1, 5, 10, 25, 100, 200 ]:
        vzx = VolumetricZxGraph(
            nodes = [ (0, NodeType.X), (1, NodeType.X) ],
            edges = [ (0, 1, EdgeType.IDENTITY) ],
            qubits = { 0 : 0, 1 : 0 },
            layers = { 0 : 0, 1 : 1 },
        )

        node0 = vzx.get_zx_node(0)
        cube0 = BgCube(CubeKind.XZZ, SpacetimeHelper.ORIGIN)
        node1 = vzx.get_zx_node(1)
        cube1 = BgCube(CubeKind.XZZ, d * SpacetimeHelper.XP)
        vzx.realise_zx_node( node0, cube0 )
        vzx.realise_zx_node( node1, cube1 )

        console.info(f"Benchmarking pathfinder with distance {d}.")

        pathfinder = PathfinderDFS(branch_and_bound = True, tracing = True)
        # pathfinder = PathfinderDijkstra(tracing = True)

        start = time()
        path = pathfinder.find_optimal_paths(cube0, cube1)
        final = time()

        if path is None:
            continue

        vzx.realise_zx_edge( node0.id, node1.id, path )

        console.info(f"Runtime : {round(final - start, 2)} seconds.")

        d = 1
        l = path.manhattan_length()
        viewer = VolumetricZxGraphViewer(vzx, label = f"manhattan distance = {d}, manhattan length = {l}, time={round(final - start, 2)}s", layout = CircuitLayout(vzx))
        viewer.display()