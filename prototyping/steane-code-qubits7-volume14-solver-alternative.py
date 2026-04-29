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

from venv import CORE_VENV_DEPS

import pyzx
from mypy.modulefinder import PathSpec

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser
from qelebrimbor.utilities.least_cycle_analyser import MinimalCycleBasisAnalyser
from qelebrimbor.utilities.ring_making import find_realisation, find_completion, extend_unrealised

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.vedo.zx_layout.hexagon import HexagonLayout
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.vedo').setLevel(logging.INFO)

if __name__ == "__main__":
    with open("../assets/pyzx/steane/steane-code-qubits7-spiders7.json", 'r') as file:
        pyzx_input = pyzx.Graph().from_json(file.read())

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_input)

    MinimalCycleBasisAnalyser.analyse(vzx)
    cycles = MinimalCycleBasisAnalyser.decompose_nodes(vzx)

    index = 0
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_realisation(vzx, cycle, maximal_overhead = 4)

    BlockGraphConstructor.realise_nodes(
        graph = vzx,
        specifications = {
            2 : BgCube(kind = CubeKind.ZXZ, position = Coordinates( 1,-2, 0)),
            4 : BgCube(kind = CubeKind.XXZ, position = Coordinates( 0,-1, 1)),
            5 : BgCube(kind = CubeKind.ZXZ, position = Coordinates(-1,-1, 0))
        }
    )

    BlockGraphConstructor.realise_edges(
        graph = vzx,
        specifications = {
            (0, 2) : PathSpecification(
                vzx.get_zx_node(0).realising_cube, vzx.get_zx_node(2).realising_cube,
                extras = [ BgCube(kind = CubeKind.ZXX, position = Coordinates( 1,-2,-1)) ],
                pipes = [ EdgeType.IDENTITY for _ in range(2) ]
            ),
            (1, 4): PathSpecification(
                vzx.get_zx_node(1).realising_cube, vzx.get_zx_node(4).realising_cube,
                extras = [ BgCube(kind = CubeKind.ZXZ, position = Coordinates( 1,-1, 1)) ],
                pipes = [EdgeType.IDENTITY for _ in range(2) ]
            ),
            (4, 5): PathSpecification(
                vzx.get_zx_node(4).realising_cube, vzx.get_zx_node(5).realising_cube,
                extras = [ BgCube(kind = CubeKind.ZXZ, position = Coordinates(-1,-1, 1)) ],
                pipes = [EdgeType.IDENTITY for _ in range(2) ]
            ),
            (5,6) : PathSpecification(
                vzx.get_zx_node(5).realising_cube, vzx.get_zx_node(6).realising_cube,
                pipes = [ EdgeType.IDENTITY ]
            ),
            (2,4) : PathSpecification(
                vzx.get_zx_node(2).realising_cube, vzx.get_zx_node(4).realising_cube,
                extras = [ BgCube(kind = CubeKind.ZXZ, position = Coordinates( 1,-2, 1)),
                           BgCube(kind = CubeKind.XXZ, position = Coordinates( 0,-2, 1))
                ],
                pipes = [ EdgeType.IDENTITY for _ in range(3) ]
            )
        }
    )

    extend_unrealised(vzx)

    vzx.log_report()

    hexagon = HexagonLayout(graph = vzx, nodes = [0,2,4,5,6,3], extras = { 1 : (0.0, 0.0), 7 : (0.7, 1.0 / 6.0) })
    viewer = VolumetricZxGraphViewer(graph= vzx, label ="steane-code-7", layout = hexagon)
    viewer.display()

    pyzx_output = vzx.into_pyzx_graph(filepath ="../assets/pyzx/steane/steane-code-qubits7-spiders7-alt-blockgraph.json")
    pyzx.draw(pyzx_output, labels = True)