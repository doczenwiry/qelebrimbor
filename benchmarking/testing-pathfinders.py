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

import sys
from time import time

from qelebrimbor.core.attributes_bg import CubeKind
from qelebrimbor.core.attributes_zx import NodeType, EdgeType
from qelebrimbor.core.components import BgCube
from qelebrimbor.helpers.calculator import ManhattanCalculator

from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.spacetime.pathfinders.depth_first_search import PathfinderDFS
from qelebrimbor.spacetime.pathfinders.dijkstra import PathfinderDijkstra
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.circuit import CircuitLayout

import logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("qelebrimbor.spacetime").setLevel(logging.INFO)

SOURCE: int = 0
TARGET: int = 1

if __name__ == "__main__":
    nodes = [(SOURCE, NodeType.X), (TARGET, NodeType.Z)]
    edges = [(SOURCE, TARGET, EdgeType.IDENTITY)]
    qubits = {SOURCE: 0, TARGET: 0}
    layers = {SOURCE: 0, TARGET: 1}

    for md in [1, 5, 10, 25, 100, 200]:
        print(f"Benchmarking pathfinder with distance {md}.")

        sys.stdout.flush()

        # Prepare the VolumetricZxGraph.
        vzx = VolumetricZxGraph(nodes, edges, qubits, layers)
        source = vzx.get_zx_node(SOURCE)
        target = vzx.get_zx_node(TARGET)
        vzx.realise_zx_node(node = source, cube = BgCube(CubeKind.XZZ, SpacetimeHelper.ORIGIN))
        vzx.realise_zx_node(node = target, cube = BgCube(CubeKind.ZXX, md * SpacetimeHelper.XP))

        # Instantiate the Pathfinder to benchmark
        pathfinder = PathfinderDFS(vzx, branch_and_bound = False, tracing = SpacetimeTracingReport.FINAL)
        # pathfinder = PathfinderDijkstra(vzx, tracing = SpacetimeTracingReport.FINAL)

        # Perform the pathfinding from source to target
        start_time = time()
        path = pathfinder.find_optimum(source.realising_cube, target.realising_cube, EdgeType.IDENTITY)
        final_time = time()
        runtime = round(final_time - start_time, 2)

        if path is None:
            continue

        vzx.realise_zx_edge(SOURCE, TARGET, path)

        sys.stderr.flush()

        md = ManhattanCalculator.manhattan_distance(source.realising_cube, target.realising_cube)
        ml = path.manhattan_length()

        print(f"Runtime : {runtime} seconds. Manhattan distance = {md}, Manhattan length = {ml}")

        label = f"manhattan distance = {md}, manhattan length = {ml}, manhattan excess = +{ml - md}, time={runtime}s"
        layout = CircuitLayout(vzx)

        viewer = VolumetricZxGraphViewer(graph = vzx, label = label, layout = layout)
        viewer.display()