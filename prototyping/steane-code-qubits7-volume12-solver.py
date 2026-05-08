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
from qelebrimbor.spacetime.placefinders.breadth_first_search import PlacefinderBFS

from qelebrimbor.spacetime.ringfinders.breadth_first_search import RingfinderBFS
from qelebrimbor.spacetime.subringfinders.depth_first_search import SubringfinderDFS

from qelebrimbor.utilities.cycle_analyser import CycleAnalyser

from qelebrimbor.vedo.zx_layout.hexagon import HexagonLayout
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
console = logging.getLogger(__name__)
console.setLevel(logging.INFO)
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("qelebrimbor.spacetime").setLevel(logging.INFO)


attributes_zx.ZX_COLORING = True
if __name__ == "__main__":
    vzx = PYZX.from_file("../assets/pyzx/steane/steane-code-qubits7-spiders8.json")

    ringfinder = RingfinderBFS(graph = vzx)
    subringfinder = SubringfinderDFS(graph = vzx, branch_and_bound = True)

    CycleAnalyser.analyse(vzx, minimal = True)
    cycles = CycleAnalyser.decompose(vzx, minimal = True)

    index = 0
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    ring = ringfinder.find_optimum(cycle, maximal_excess = 6)

    if ring:
        console.info(f"Found realisation [volume={ring.volume()}] for cycle : {CycleAnalyser.string(cycle)}")
        console.info(f"> {ring}")
        vzx.realise_zx_cycle(cycle, ring)

    index = 1
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")

    chains = CycleAnalyser.identify_chains(cycle)
    chain = chains[0]

    console.info(f"> Chain : {chain}")

    completion = subringfinder.find_optimum(chain, maximal_excess = 8)

    if completion:
        console.info(f"Found completion [volume={completion.manhattan_length()-1}] for chain : {chain}")
        console.info(f"> {completion}")
        vzx.realise_zx_chain(chain, completion)

    ZxGraphInflaterBoundaries(graph = vzx).process()

    # placefinder = PlacefinderBFS(graph = vzx)
    #
    # for node in vzx.get_zx_nodes():
    #     if not node.is_realised():
    #         continue
    #
    #     for neighbor in vzx.get_zx_neighbors(node):
    #         if not neighbor.is_realised():
    #             print(f"Node {node} is not realised.")
    #             placement = placefinder.find_closest_realisation(node.realising_cube, neighbor)
    #
    #             if placement:
    #                 # Realise the target cube and the path connecting it to the source cube
    #                 vzx.realise_zx_node(neighbor, placement.final)
    #                 vzx.realise_zx_edge(node.id, neighbor.id, placement)

    vzx.log_report()

    hexagon = HexagonLayout(graph = vzx, nodes = [1, 4, 0, 7, 3, 6],
        extras = {2 : (0.7, 1.5 / 6.0) , 5 : (0.7, 4.5 / 6.0), 9 : (0.7, 0.5 / 6.0), 12 : (0.7, 3.5 / 6.0)}
    )
    viewer = VolumetricZxGraphViewer(vzx, "steane-code-7", hexagon)
    viewer.display()

    PYZX.into_file(vzx, filepath ="../assets/pyzx/steane/steane-code-qubits7-spiders8-blockgraph.pyzx.json")