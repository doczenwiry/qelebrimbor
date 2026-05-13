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

import itertools
from time import time

import qelebrimbor.core.zx
from qelebrimbor.core.zx.attributes import NodeId, NodeType, EdgeType
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.spacetime.ringfinders.breadth_first_search import RingfinderBFS
from qelebrimbor.spacetime.ringfinders.colorblind_dfs import RingfinderColorblindDFS
from qelebrimbor.spacetime.ringfinders.depth_first_search import RingfinderDFS
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport

from qelebrimbor.analysis.cycles import CycleAnalyser

from qelebrimbor.vedo.zx_layout.cycle import CycleLayout
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
logging.basicConfig(level=logging.INFO)

qelebrimbor.core.zx.attributes.ZX_COLORING = True

if __name__ == "__main__":
    nodes = list(zip(itertools.count(0, 1),
        [ NodeType.X, NodeType.Z, NodeType.X, NodeType.Z ]
    ))
    edges = [ (index, (index+1) % len(nodes), EdgeType.IDENTITY) for index in range(len(nodes)) ]

    vzx = VolumetricZxGraph(nodes, edges)

    cycle0 = CycleAnalyser.decompose(vzx, minimal = True)[0]
    print(f"Cycle : {str(cycle0)}")

    ringfinder = RingfinderBFS(graph = vzx, tracing = SpacetimeTracingReport.FINAL)
    # ringfinder = RingfinderDFS(graph = vzx, tracing = SpacetimeTracingReport.FINAL)
    # ringfinder = RingfinderColorblindDFS(graph = vzx, reporting = SpacetimeTracingReport.FINAL)

    start = time()
    ring = ringfinder.find_optimum(cycle0, maximal_excess = 6)
    final = time()
    runtime = round(final - start, 2)

    if ring is not None:
        print(f"Found a ring with volume : {ring.volume()}")
        print(f"> {ring}")

        vzx.realise_zx_cycle(cycle0, ring)

        volume = ring.volume()
        excess = volume - cycle0.length
    else:
        print(f"> Failed to find optimal ring.")
        volume = None
        excess = None


    label = f"volume = {volume}, excess = +{excess}, time={runtime}s"
    viewer = VolumetricZxGraphViewer(graph = vzx, label = label, layout = CycleLayout(vzx))
    viewer.display()
