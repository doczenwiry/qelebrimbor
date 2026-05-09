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

import random

import pyzx

from qelebrimbor.formats.pyzx import PYZX
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker
from qelebrimbor.spacetime.ringfinders.breadth_first_search import RingfinderBFS
from qelebrimbor.spacetime.subringfinders.depth_first_search import SubringfinderDFS
from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

SEED = 42
QUBITS = 4
LAYERS = 10

import logging
logging.basicConfig(level=logging.CRITICAL)
console = logging.getLogger(__name__)

random.seed(SEED)
if __name__ == "__main__":
    circuit = f"random-s{SEED}-q{QUBITS}-d{LAYERS}"
    pyzx_input = pyzx.generate.cnots(qubits = QUBITS, depth = LAYERS)

    with open(f"../assets/pyzx/random/{circuit}.json", 'w') as file:
        file.write(pyzx_input.to_json())

    vzx = PYZX.from_pyzx_graph(pyzx_input)

    connectivity = OpenPortsTracker(vzx)
    ringfinder = RingfinderBFS(graph = vzx, ports_tracker = connectivity)
    subringfinder = SubringfinderDFS(graph = vzx, ports_tracker = connectivity, branch_and_bound = True)

    CycleAnalyser.analyse(vzx)
    cycles = CycleAnalyser.decompose(vzx)

    index = 0
    cycle = cycles[index][6:] + cycles[index][:6]
    console.info(f"Cycle {index} : {CycleAnalyser.string(cycle)}")

    ring = ringfinder.find_optimum(cycle, maximal_excess = 6)
    if ring:
        console.info(f"Found realisation [volume={ring.volume()}] for cycle : {CycleAnalyser.string(cycle)}")
        console.info(f"> {ring}")
        vzx.realise_zx_cycle(cycle, ring)

        # Reserve the ports for all the nodes that were realised as part of this ring.
        for node, _ in cycle:
            # Since each of these node is part of a ring, it already has two of its edges realised.
            connectivity.reserve(node.realising_cube, required_ports =vzx.get_zx_degree(node.id) - 2)

        for cube in ring.cubes[len(cycle):]:
            connectivity.occlude(cube.position)

    # for index in [ 5, 6, 4, 3, 2, 1 ]:
    #     cycle = cycles[index]
    #     chains = CycleAnalyser.identify_chains(cycle)
    #     chain = chains[0]
    #     console.info(f"Cycle {index} : {CycleAnalyser.string(cycle)}")
    #     console.info(f"> Chain : {chain}")
    #
    #     completion = subringfinder.find_optimum(chain, maximal_excess = 8)
    #     if completion:
    #         console.info(f"Found completion [volume={completion.manhattan_length()-1}] for chain : {chain}")
    #         console.info(f"> {completion}")
    #         vzx.realise_zx_chain(chain, completion)
    #
    # ZxGraphInflaterBoundaries(graph = vzx).process()

    vzx.log_report()

    console.info(f"Realised nodes : {sum(1 for node in vzx.get_zx_nodes() if node.is_realised())} of {vzx.number_of_nodes()}")
    console.info(f"Overall volume : {vzx.number_of_cubes()}")

    viewer = VolumetricZxGraphViewer(vzx, label = circuit)
    viewer.display()

    pyzx_output = PYZX.into_pyzx_graph(vzx)
    pyzx.draw(pyzx_input, labels=True)
    pyzx.draw(pyzx_output, labels=True)

    PYZX.into_file(vzx, filepath =f"../assets/pyzx/random/{circuit}-blockgraph.json")