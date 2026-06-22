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

import qelebrimbor.core.zx
from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.formats.preprocessing.full_reduction import FullReduction
from qelebrimbor.formats.pyzx import PYZX
from qelebrimbor.spacetime.ringfinders.colorblind_bfs import RingfinderColorblindBFS
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.planar import PlanarLayout

logging.basicConfig(level=logging.INFO)
logging.getLogger("qelebrimbor.spacetime.colorblind.painter_cycle").setLevel(logging.INFO)

qelebrimbor.core.zx.attributes.ZX_COLORING = True

COUNT = 6
if __name__ == "__main__":
    vzx: VolumetricZxGraph

    # nodes = [(node_id, NodeType.Z) for node_id in range(COUNT)]
    # edges = [(node_id, (node_id + 1) % COUNT, EdgeType.HADAMARD) for node_id in range(COUNT)]
    # vzx = VolumetricZxGraph(nodes, edges)

    pyzx_input = PYZX.from_file("../benchmarking/datasets/small/identity/random-cnots-q4-d4-s2712719750.pyzx.json")
    FullReduction.process(pyzx_input)
    vzx = PYZX.from_pyzx_graph(pyzx_input)

    cycle0 = CycleAnalyser.decompose(vzx, minimal=True)[0]
    print(f"Cycle : {str(cycle0)}")

    # ringfinder = RingfinderBFS(graph=vzx, reporting=SpacetimeTracingReport.FINAL)
    ringfinder = RingfinderColorblindBFS(graph=vzx, reporting=SpacetimeTracingReport.FINAL)
    # ringfinder = RingfinderDFS(graph = vzx, tracing = SpacetimeTracingReport.FINAL)
    # ringfinder = RingfinderColorblindDFS(graph = vzx, reporting = SpacetimeTracingReport.FINAL)

    start = time()
    ring = ringfinder.find_optimum(cycle0, maximal_excess=2)
    final = time()
    runtime = round(final - start, 2)

    label = f"{ringfinder.__class__.__name__} : time = {runtime}s"
    if ring is not None:
        print(f"Found a ring with volume : {ring.volume()}")
        print(f"> {ring}")

        vzx.realise_zx_cycle(cycle0, ring)

        volume = ring.volume()
        excess = volume - cycle0.length
        label += f", volume = {ring.volume()}, excess = +{ring.volume() - cycle0.length}"
    else:
        label += ", volume =n/a, excess = +n/a"
        print("> Failed to find optimal ring.")

    viewer = VolumetricZxGraphViewer(graph=vzx, label="label", layout=PlanarLayout(vzx, scale=3.0))
    viewer.display()
