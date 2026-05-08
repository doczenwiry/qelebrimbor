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

from qelebrimbor.core import attributes_zx

from qelebrimbor.formats.pyzx import PYZX
from qelebrimbor.inflaters.boundaries import ZxGraphInflaterBoundaries
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker

from qelebrimbor.spacetime.ringfinders.breadth_first_search import RingfinderBFS
from qelebrimbor.spacetime.subringfinders.depth_first_search import SubringfinderDFS

from qelebrimbor.analysis.cycles import CycleAnalyser

from qelebrimbor.vedo.zx_layout.hexagon import HexagonLayout
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
# logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)
# logging.getLogger('qelebrimbor.utilities.cycle_analyser').setLevel(logging.DEBUG)
logging.getLogger('qelebrimbor.vedo').setLevel(logging.CRITICAL)


attributes_zx.ZX_COLORING = True
if __name__ == "__main__":
    vzx = PYZX.from_file("../assets/pyzx/steane/steane-code-qubits7-spiders7.json")

    ports_tracker = OpenPortsTracker(vzx)
    ringfinder = RingfinderBFS(graph = vzx, ports_tracker = ports_tracker)
    subringfinder = SubringfinderDFS(graph = vzx, ports_tracker = ports_tracker, branch_and_bound = True)

    CycleAnalyser.analyse(vzx)
    cycles = CycleAnalyser.decompose(vzx, minimal = True)

    # Realise the root ring
    index = 0
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")

    ring = ringfinder.find_optimum(cycle, maximal_excess = 2)
    if ring:
        console.info(f"Found realisation [volume={ring.volume()}] for cycle : {CycleAnalyser.string(cycle)}")
        console.info(f"> {ring}")
        vzx.realise_zx_cycle(cycle, ring)

        # Reserve the ports for all the nodes that were realised as part of this ring.
        for node, _ in cycle:
            # Since each of these node is part of a ring, it already has two of its edges realised.
            ports_tracker.reserve_ports(node.realising_cube, required_ports = vzx.get_zx_degree(node.id) - 2)
            for position in ports_tracker.reserved(node.realising_cube):
                vzx.spacetime.reserve(node.realising_cube, position)

    ports_tracker.verify_ports()

    # Realise the remaining chains
    index = 1
    cycle = cycles[index]

    chains = CycleAnalyser.identify_chains(cycle)
    chain = chains[0]

    console.info(f"Cycle {index} : {CycleAnalyser.string(cycle)}")
    console.info(f"> Chain : {chain}")
    completion = subringfinder.find_optimum(chain, maximal_excess = 12)

    if completion:
        console.info(f"Found completion [volume={completion.manhattan_length()-1}] for chain : {chain}")
        console.info(f"> {completion}")
        vzx.realise_zx_chain(chain, completion)

    index = 2
    cycle = cycles[index]

    chains = CycleAnalyser.identify_chains(cycle)
    chain = chains[0]

    console.info(f"Cycle {index} : {CycleAnalyser.string(cycle)}")
    console.info(f"> Chain : {chain}")
    completion = subringfinder.find_optimum(chain, maximal_excess = 8)

    if completion:
        console.info(f"Found completion [volume={completion.manhattan_length()-1}] for chain : {chain}")
        console.info(f"> {completion}")
        vzx.realise_zx_chain(chain, completion)

    ZxGraphInflaterBoundaries(vzx).process()

    vzx.log_report()

    hexagon = HexagonLayout(graph=vzx, nodes=[0, 2, 4, 5, 6, 3], extras={1: (0.0, 0.0), 7: (0.7, 1.0 / 6.0)})
    viewer = VolumetricZxGraphViewer(graph= vzx, label ="steane-code-7", layout = hexagon)
    viewer.display()

    PYZX.into_file(vzx, filepath ="../assets/pyzx/steane/steane-code-qubits7-spiders7-blockgraph.pyzx.json")