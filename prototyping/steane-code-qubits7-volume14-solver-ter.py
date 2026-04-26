import pyzx

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.least_cycle_analyser import MinimalCycleBasisAnalyser
from qelebrimbor.utilities.ring_making import find_realisation

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
        pyzx_graph = pyzx.Graph().from_json(file.read())

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_graph)

    MinimalCycleBasisAnalyser.analyse(vzx)
    cycles = MinimalCycleBasisAnalyser.decompose_nodes(vzx)

    index = 0
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_realisation(vzx, cycle, maximal_overhead = 4)

    BlockGraphConstructor.realise_nodes(
        graph = vzx,
        specifications = {
            2 : BgCube(kind = CubeKind.ZZX, position = Coordinates( 1,-2,-1)),
            4 : BgCube(kind = CubeKind.ZXX, position = Coordinates( 1,-1, 1)),
            5 : BgCube(kind = CubeKind.XZZ, position = Coordinates( 0,-2, 0))
        }
    )

    BlockGraphConstructor.place_cubes(
        graph = vzx,
        specifications = [
            (CubeKind.XZX, vzx.get_zx_node(2).realising_cube.id, SpacetimeHelper.XP),
            (CubeKind.XZX, vzx.get_zx_node(5).realising_cube.id, SpacetimeHelper.ZP),
            (CubeKind.XZZ, 23, SpacetimeHelper.ZP),
            (CubeKind.ZZX, 24, SpacetimeHelper.XP),
            (CubeKind.XZX, 25, SpacetimeHelper.ZP)
        ]
    )

    BlockGraphConstructor.realise_edges(
        graph = vzx,
        specifications = {
            (s,t): PathSpecification(
                vzx.get_zx_node(s).realising_cube, vzx.get_zx_node(t).realising_cube,
                pipes=[ EdgeType.IDENTITY ]
            ) for (s,t) in [ (0,2), (1,4), (5,6) ]
        }
    )

    # extend_unrealised(vzx)

    vzx.log_report()

    hexagon = HexagonLayout(graph = vzx, nodes = [0,2,4,5,6,3], extras = { 1 : (0.0, 0.0), 7 : (0.7, 1.0 / 6.0) })
    viewer = VolumetricZxGraphViewer(graph= vzx, label ="steane-code-7", layout = hexagon)
    viewer.display()