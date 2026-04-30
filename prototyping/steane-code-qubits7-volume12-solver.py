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

import pyzx

from qelebrimbor.utilities.least_cycle_analyser import MinimalCycleBasisAnalyser
from qelebrimbor.utilities.ring_making import find_realisation, find_completion, extend_unrealised
from qelebrimbor.vedo.zx_layout.hexagon import HexagonLayout
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)

if __name__ == "__main__":
    with open("../assets/pyzx/steane/steane-code-qubits7-spiders8.json", 'r') as file:
        pyzx_input = pyzx.Graph().from_json(file.read())

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_input)

    MinimalCycleBasisAnalyser.analyse(vzx)
    cycles = MinimalCycleBasisAnalyser.decompose_nodes(vzx)

    index = 0
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_realisation(vzx, cycle, maximal_overhead = 2)

    index = 1
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 4)

    extend_unrealised(vzx)

    vzx.log_report()

    hexagon = HexagonLayout(graph = vzx, nodes = [1, 4, 0, 7, 3, 6],
        extras = {2 : (0.7, 1.5 / 6.0) , 5 : (0.7, 4.5 / 6.0), 9 : (0.7, 0.5 / 6.0), 12 : (0.7, 3.5 / 6.0)}
    )
    viewer = VolumetricZxGraphViewer(vzx, "steane-code-7", hexagon)
    viewer.display()

    vzx.to_pyzx_graph(filepath ="../assets/pyzx/steane/steane-code-qubits7-spiders8-blockgraph.json")