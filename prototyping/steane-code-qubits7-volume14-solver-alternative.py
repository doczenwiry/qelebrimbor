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

from qelebrimbor.formats.pyzx import PYZX
from qelebrimbor.spacetime.ringfinders.breadth_first_search import RingfinderBFS
from qelebrimbor.spacetime.subringfinders.depth_first_search import SubringfinderDFS
from qelebrimbor.analysis.cycles import CycleAnalyser

from qelebrimbor.vedo.zx_layout.hexagon import HexagonLayout
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.vedo').setLevel(logging.INFO)

if __name__ == "__main__":
    vzx = PYZX.from_file("../assets/pyzx/steane/steane-code-qubits7-spiders7.json")

    ringfinder = RingfinderBFS(graph = vzx)
    subringfinder = SubringfinderDFS(graph = vzx, branch_and_bound = True)

    CycleAnalyser.analyse(vzx)
    cycles = CycleAnalyser.decompose(vzx)

    index = 0
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")

    ring = ringfinder.find_optimum(cycle, maximal_excess = 4)
    if ring:
        console.info(f"Found realisation [volume={ring.volume()}] for cycle : {CycleAnalyser.string(cycle)}")
        console.info(f"> {ring}")
        vzx.realise_zx_cycle(cycle, ring)

    # BlockGraphConstructor.realise_edges(
    #     graph = vzx,
    #     specifications = {
    #         (0, 2) : Path(vzx.get_zx_node(0).realising_cube).extend(
    #             cube = BgCube(kind=CubeKind.ZXX, position=Coordinates(1, -2, -1)),
    #             pipe_type = EdgeType.IDENTITY
    #         ).extend(
    #             cube = vzx.get_zx_node(2).realising_cube,
    #             pipe_type = EdgeType.IDENTITY
    #         ),
    #         (1, 4): Path(vzx.get_zx_node(1).realising_cube).extend(
    #             cube = BgCube(kind = CubeKind.ZXZ, position = Coordinates( 1,-1, 1)),
    #             pipe_type = EdgeType.IDENTITY
    #         ).extend(
    #             cube = vzx.get_zx_node(4).realising_cube,
    #             pipe_type = EdgeType.IDENTITY
    #         ),
    #         (4, 5): Path(vzx.get_zx_node(4).realising_cube).extend(
    #             cube = BgCube(kind=CubeKind.ZXZ, position=Coordinates(-1, -1, 1)),
    #             pipe_type = EdgeType.IDENTITY
    #         ).extend(
    #             cube = vzx.get_zx_node(5).realising_cube,
    #             pipe_type = EdgeType.IDENTITY
    #         ),
    #         (5,6) : Path(vzx.get_zx_node(5).realising_cube).extend(
    #             cube = vzx.get_zx_node(6).realising_cube,
    #             pipe_type = EdgeType.IDENTITY
    #         ),
    #         (2,4) : Path(vzx.get_zx_node(2).realising_cube).extend(
    #             cube = BgCube(kind = CubeKind.ZXZ, position = Coordinates( 1,-2, 1)),
    #             pipe_type=EdgeType.IDENTITY
    #         ).extend(
    #             cube = BgCube(kind = CubeKind.XXZ, position = Coordinates( 0,-2, 1)),
    #             pipe_type=EdgeType.IDENTITY
    #         ).extend(
    #             cube = vzx.get_zx_node(4).realising_cube,
    #             pipe_type = EdgeType.IDENTITY
    #         )
    #     }
    # )

    # ZxGraphInflaterBoundaries(graph = vzx).process()

    vzx.log_report()

    hexagon = HexagonLayout(graph = vzx, nodes = [0,2,4,5,6,3], extras = { 1 : (0.0, 0.0), 7 : (0.7, 1.0 / 6.0) })
    viewer = VolumetricZxGraphViewer(graph= vzx, label ="steane-code-7", layout = hexagon)
    viewer.display()

    PYZX.into_file(vzx, filepath ="../assets/pyzx/steane/steane-code-qubits7-spiders7-alt-blockgraph.pyzx.json")