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

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.path import Path
from qelebrimbor.formats.pyzx import PYZX
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser
from qelebrimbor.utilities.ring_making import find_realisation, extend_unrealised
from qelebrimbor.vedo.zx_layout.hexagon import HexagonLayout
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)

if __name__ == "__main__":
    vzx = PYZX.from_file("../assets/pyzx/steane/steane-code-qubits7-spiders7.json")

    CycleBasisAnalyser.analyse(vzx)
    cycles = CycleBasisAnalyser.decompose_nodes(vzx)

    index = 0
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_realisation(vzx, cycle, maximal_overhead = 4)

    BlockGraphConstructor.realise_nodes(
        graph = vzx,
        specifications = {
            1 : BgCube(CubeKind.ZXZ, Coordinates(-1,-1,0))
        }
    )

    BlockGraphConstructor.realise_edges(
        graph = vzx,
        specifications = {
            (0,1) : Path(vzx.get_zx_node(0).realising_cube).extend(
                cube = vzx.get_zx_node(1).realising_cube,
                pipe_type = vzx.get_zx_edge(0, 1).type
            ),
            (1, 4): Path(vzx.get_zx_node(1).realising_cube).extend(
                cube = BgCube(CubeKind.ZXZ, Coordinates(-1, -1, -1)),
                pipe_type = EdgeType.IDENTITY
            ).extend(
                cube = BgCube(CubeKind.ZXZ, Coordinates(0, -1, -1)),
                pipe_type = EdgeType.IDENTITY
            ).extend(
                cube = BgCube(CubeKind.ZXZ, Coordinates(0, -1, -2)),
                pipe_type = EdgeType.IDENTITY
            ).extend(
                cube = BgCube(CubeKind.ZXZ, Coordinates(1, -1, -2)),
                pipe_type = EdgeType.IDENTITY
            ).extend(
                cube = vzx.get_zx_node(4).realising_cube,
                pipe_type = vzx.get_zx_edge(1, 4).type
            ),
        }
    )

    BlockGraphConstructor.realise_edges(
        graph = vzx,
        specifications = { # Chosen cube 23 for node 1
            (1, 6) : Path(vzx.get_bg_cube(23)).extend(
                cube = BgCube(CubeKind.XXZ, Coordinates(-1, -1, -2)),
                pipe_type = EdgeType.IDENTITY
            ).extend(
                cube = BgCube(CubeKind.XZZ, Coordinates(-1, 0, -2)),
                pipe_type = EdgeType.IDENTITY
            ).extend(
                cube = BgCube(CubeKind.XZX, Coordinates(-1, 0, -1)),
                pipe_type = EdgeType.IDENTITY
            ).extend(
                cube = vzx.get_zx_node(6).realising_cube,
                pipe_type = vzx.get_zx_edge(1, 6).type
            )
        }
    )

    extend_unrealised(vzx)

    vzx.log_report()

    hexagon = HexagonLayout(graph=vzx, nodes=[0, 2, 4, 5, 6, 3], extras={1: (0.0, 0.0), 7: (0.7, 1.0 / 6.0)})
    viewer = VolumetricZxGraphViewer(graph= vzx, label ="steane-code-7", layout = hexagon)
    viewer.display()

    PYZX.into_file(vzx, filepath ="../assets/pyzx/steane/steane-code-qubits7-spiders7-blockgraph.pyzx.json")