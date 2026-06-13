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

import logging
from time import time

import qelebrimbor.core.zx.attributes
from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.core.colorless.frenet import FrenetRing
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType, NodeType
from qelebrimbor.spacetime.ringfinders.colorblind_frenet_bfs import RingfinderColorblindFrenetBFS
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport

logging.basicConfig(level=logging.INFO)
logging.getLogger("qelebrimbor.spacetime.ringfinders.colorblind_frenet_dfs").setLevel(logging.DEBUG)

qelebrimbor.core.zx.attributes.ZX_COLORING = True

COUNT = 8
if __name__ == "__main__":
    vzx: VolumetricZxGraph
    # vzx = PYZX.from_pyzx_graph(PYZX.from_file("../assets/pyzx/random-cnots-q4-d32-s2712719750.pyzx.internal.json"))
    vzx = VolumetricZxGraph(
        nodes=[(node_id, NodeType.Z) for node_id in range(COUNT)],
        edges=[(node_id, (node_id + 1) % COUNT, EdgeType.HADAMARD) for node_id in range(COUNT)],
    )

    cycles = CycleAnalyser.decompose(vzx, minimal=True)
    cycle0 = cycles[0]

    for node in cycle0.nodes:
        print(f"Node {node} : {node.degree}")

    ringfinder = RingfinderColorblindFrenetBFS(graph=vzx, reporting=SpacetimeTracingReport.FINAL)

    start = time()
    ring: FrenetRing | None = ringfinder.find_optimum(cycle0, maximal_excess=2)
    final = time()
    runtime = round(final - start, 2)

    print(f"Frenet ring : {ring}")

    label = f"{ringfinder.__class__.__name__} : time = {runtime}s"
    # if ring is not None:
    #     print(f"Found a ring with volume : {ring.volume()}")
    #     print(f"> {ring}")
    #
    #     vzx.realise_zx_cycle(cycle0, ring)
    #
    #     volume = ring.volume()
    #     excess = volume - cycle0.length
    #     label += f", volume = {ring.volume()}, excess = +{ring.volume() - cycle0.length}"
    # else:
    #     label += ", volume =n/a, excess = +n/a"
    #     print("> Failed to find optimal ring.")

    # VolumetricZxGraphViewer(graph=vzx, cycles=cycles, label=label, layout=PlanarLayout(vzx, scale=5.0)).display()
