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
from qelebrimbor.utilities.cycle_analyser import CycleAnalyser
from qelebrimbor.deprecated.ring_making import find_realisation, find_completion, extend_unrealised
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
    CycleAnalyser.analyse(vzx)
    cycles = CycleAnalyser.decompose_nodes(vzx)

    index = 0
    cycle = cycles[index][6:] + cycles[index][:6]
    console.info(f"Cycle {index} : {cycle}")
    find_realisation(vzx, cycle, maximal_excess= 2)

    index = 5
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 8)

    index = 6
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 8)

    index = 4
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 4)

    index = 3
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 6)

    index = 2
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 6)

    index = 1
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 6)

    extend_unrealised(vzx)
    extend_unrealised(vzx)
    extend_unrealised(vzx)

    vzx.log_report()

    console.info(f"Realised nodes : {sum(1 for node in vzx.get_zx_nodes() if node.is_realised())} of {vzx.number_of_nodes()}")
    console.info(f"Overall volume : {vzx.number_of_cubes()}")

    viewer = VolumetricZxGraphViewer(vzx, label = circuit)
    viewer.display()

    pyzx_output = PYZX.into_pyzx_graph(vzx)
    pyzx.draw(pyzx_input, labels=True)
    pyzx.draw(pyzx_output, labels=True)

    PYZX.into_file(vzx, filepath =f"../assets/pyzx/random/{circuit}-blockgraph.json")