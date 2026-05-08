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

from qelebrimbor.core.path import Path
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.attributes_zx import EdgeType
from qelebrimbor.core.attributes_bg import CubeKind
from qelebrimbor.core.coordinates import Coordinates

from qelebrimbor.formats.pyzx import PYZX

from qelebrimbor.inflaters.boundaries import ZxGraphInflaterBoundaries

from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor

from qelebrimbor.vedo.zx_layout.hexagon import HexagonLayout
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)

if __name__ == "__main__":
    vzx = PYZX.from_file("../assets/pyzx/steane/steane-code-qubits7-spiders8.json")

    BlockGraphConstructor.realise_nodes(
        graph= vzx,
        specifications = {
            1 : BgCube(kind=CubeKind.XZZ, position=Coordinates( 0, 0, 0)),
            5 : BgCube(kind=CubeKind.XZX, position=Coordinates( 0, 0, 2)),
            2 : BgCube(kind=CubeKind.ZZX, position=Coordinates(-1, 0, 2)),
            7 : BgCube(kind=CubeKind.ZXX, position=Coordinates(-1, 1, 1)),
            0 : BgCube(kind=CubeKind.ZXZ, position=Coordinates(-1, 1, 0)),
            4 : BgCube(kind=CubeKind.XXZ, position=Coordinates( 0, 1, 0)),
        }
    )
    BlockGraphConstructor.realise_edges(
        graph= vzx,
        specifications = {
            (s,t) : Path(vzx.get_zx_node(s).realising_cube).extend(
                cube = vzx.get_zx_node(t).realising_cube,
                pipe_type = vzx.get_zx_edge(s,t).type
            )
            for s, t in [ (2,5) , (0,7) , (0,4) , (1,4) ]
        }
    )
    BlockGraphConstructor.realise_edges(
        graph= vzx,
        specifications = {
            (1,5) : Path(vzx.get_zx_node(1).realising_cube).extend(
                cube = BgCube(kind=CubeKind.XZZ, position=Coordinates(0,0,1)),
                pipe_type = vzx.get_zx_edge(1,5).type
            ).extend(
                cube = vzx.get_zx_node(5).realising_cube,
                pipe_type = EdgeType.IDENTITY
            ),
            (2,7) : Path(vzx.get_zx_node(2).realising_cube).extend(
                cube = BgCube(kind=CubeKind.ZXX, position=Coordinates(-1, 1, 2)),
                pipe_type = vzx.get_zx_edge(2, 7).type
            ).extend(
                cube = vzx.get_zx_node(7).realising_cube,
                pipe_type = EdgeType.IDENTITY
            )
        }
    )

    BlockGraphConstructor.realise_nodes(
        graph= vzx,
        specifications = {
            3 : BgCube(kind=CubeKind.ZZX, position=Coordinates(-1, 0, 1)),
            6 : BgCube(kind=CubeKind.XXZ, position=Coordinates( 0,-1, 0))
        }
    )
    BlockGraphConstructor.realise_edges(
        graph= vzx,
        specifications = {
            (s,t) : Path(vzx.get_zx_node(s).realising_cube).extend(
                cube = vzx.get_zx_node(t).realising_cube,
                pipe_type = vzx.get_zx_edge(s,t).type
            )
            for s, t in [ (3,7) , (1,6) ]
        }
    )
    BlockGraphConstructor.realise_edges(
        graph= vzx,
        specifications = {
            (3,6) : Path(vzx.get_zx_node(3).realising_cube).extend(
                cube = BgCube(kind=CubeKind.ZXX, position=Coordinates(-1, -1, 1)),
                pipe_type = vzx.get_zx_edge(3,6).type
            ).extend(
                cube = BgCube(kind=CubeKind.ZXZ, position=Coordinates(-1, -1, 0)),
                pipe_type = EdgeType.IDENTITY
            ).extend(
                cube = vzx.get_zx_node(6).realising_cube,
                pipe_type = EdgeType.IDENTITY
            ),
        }
    )

    ZxGraphInflaterBoundaries(vzx).process()

    vzx.log_report()

    hexagon = HexagonLayout(graph = vzx, nodes = [1, 4, 0, 7, 3, 6],
        extras = {2 : (0.7, 1.5 / 6.0) , 5 : (0.7, 4.5 / 6.0), 9 : (0.7, 0.5 / 6.0), 12 : (0.7, 3.5 / 6.0)}
    )
    viewer = VolumetricZxGraphViewer(vzx, label = "steane-code-7", layout = hexagon)
    viewer.display()

    PYZX.into_file(vzx, filepath ="../assets/pyzx/steane/steane-code-qubits7-spiders8-alt-blockgraph.json")
