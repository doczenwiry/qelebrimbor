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

from qelebrimbor.core.components import ZxNode, ZxEdge
from qelebrimbor.spacetime.ringfinders.breadth_first_search import RingfinderBFS
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.attributes_zx import NodeType, EdgeType
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.cycle import CycleLayout

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.CRITICAL)

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

    ringfinder = RingfinderBFS(vzx)

    vzx.log_summary()

    zx_cycle = list(zip(zx_nodes, zx_edges))

    ring = ringfinder.find_optimum(zx_cycle, maximal_excess = MAX_OVERHEAD + 2)

    if ring is None:
        console.info(f"No optimum found for {zx_cycle}")
    else:
        console.info(f"Found an optimal Hadamard Ring of length {ring.volume()}")

        console.info(f"> Realisation [{ring.volume()}] : {ring}")
        vzx = VolumetricZxGraph(
            nodes = zip(range(LENGTH), nodes),
            edges = ( (s, (s + 1) % LENGTH, edges[s]) for s in range(LENGTH) )
        )

        vzx.realise_zx_cycle(zx_cycle, ring)

        viewer = VolumetricZxGraphViewer(vzx, f"Hadamard Ring, n={LENGTH}", CycleLayout(vzx))
        viewer.display()