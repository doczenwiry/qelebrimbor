import pyzx

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser
from qelebrimbor.utilities.ring_making import find_realisation, find_completion, extend_unrealised
from qelebrimbor.vedo.zx_layout.hexagon import HexagonLayout
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)

if __name__ == "__main__":
    with open("../assets/pyzx/steane-code-qubits7-spiders7.json", 'r') as file:
        pyzx_graph = pyzx.Graph().from_json(file.read())

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_graph)

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
            (0,1) : PathSpecification(
                source_cube = vzx.get_zx_node(0).realising_cube,
                target_cube=vzx.get_zx_node(1).realising_cube,
                pipes = [ vzx.get_zx_edge(0, 1).type ]
            ),
            (1, 4): PathSpecification(
                source_cube = vzx.get_zx_node(1).realising_cube,
                target_cube = vzx.get_zx_node(4).realising_cube,
                extras = [
                    BgCube(CubeKind.ZXZ, Coordinates(-1,-1,-1)), BgCube(CubeKind.ZXZ, Coordinates( 0,-1,-1)),
                    BgCube(CubeKind.ZXZ, Coordinates( 0,-1,-2)), BgCube(CubeKind.ZXZ, Coordinates(1, -1,-2))
                ],
                pipes=[ vzx.get_zx_edge(1, 4).type if i == 0 else EdgeType.IDENTITY for i in range(5) ]
            ),
        }
    )

    BlockGraphConstructor.realise_edges(
        graph = vzx,
        specifications = {
            (1, 6) : PathSpecification(
                source_cube = vzx.get_bg_cube(23), # Chosen cube for node 1
                target_cube = vzx.get_zx_node(6).realising_cube,
                extras = [
                    BgCube(CubeKind.XXZ, Coordinates(-1,-1,-2)), BgCube(CubeKind.XZZ, Coordinates(-1, 0,-2)),
                    BgCube(CubeKind.XZX, Coordinates(-1, 0,-1))
                ],
                pipes = [ vzx.get_zx_edge(1, 6).type if i == 0 else EdgeType.IDENTITY for i in range(4) ]
            )
        }
    )

    extend_unrealised(vzx)

    vzx.log_report()

    hexagon = HexagonLayout(graph=vzx, nodes=[0, 2, 4, 5, 6, 3], extras={1: (0.0, 0.0), 7: (0.7, 1.0 / 6.0)})
    viewer = VolumetricZxGraphViewer(graph= vzx, label ="steane-code-7", layout = hexagon)
    viewer.display()