import numpy as np
import pyzx as zx
import networkx as nx

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.components_zx import NodeId, NodeType, EdgeId, EdgeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

from qelebrimbor.vedo.zx_layout.abstract import ZxLayout
from qelebrimbor.vedo.zx_layout.manual import ManualLayout

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('qelebrimbor').setLevel(logging.INFO)

def find_terminal_node(graph: zx.graph.base.BaseGraph, qubit: int) -> int:
    return max(
        filter(lambda vt: graph.qubit(vt) == qubit , graph.vertices())
    )

def add_steane_chunk(graph: zx.graph.base.BaseGraph, layer: int, target_qubits: list[int]):
    row = layer
    start = graph.add_vertex(ty = zx.VertexType.X, row = row, qubit = 0)
    row += 2
    previous = start
    for target_qubit in target_qubits:
        terminal = find_terminal_node(graph, target_qubit)
        control = graph.add_vertex(ty = zx.VertexType.Z, row = row, qubit = 0)
        target = graph.add_vertex(ty = zx.VertexType.X, row = row, qubit = target_qubit)
        graph.add_edge( (control, target) )
        graph.add_edge((previous, control), zx.EdgeType.HADAMARD if previous == start else zx.EdgeType.SIMPLE)
        graph.add_edge((terminal, target), zx.EdgeType.SIMPLE)
        row += 1
        previous = control
    row += 1
    final = graph.add_vertex(ty = zx.VertexType.X, row = row, qubit = 0)

    graph.add_edge( (previous, final), zx.EdgeType.HADAMARD)

    return row

def prepare_layout() -> ZxLayout:
    placements: dict[NodeId, tuple[float, float]] = {}

    rho = 2.0
    phi = 0.0
    step = np.pi / 3.0
    placements[2]  = (0.0,  0.75)
    placements[9]  = (0.75,  0.5)
    placements[5]  = (0.0, -0.75)
    placements[12] = (-0.75, -0.5)
    for nd in [1,4,0,7,3,6]:
        x = rho * np.cos(phi)
        y = rho * np.sin(phi)
        placements[nd] = (x,y)
        neighbouring_boundaries = list(filter(lambda bd: vzx.has_edge(nd, bd), vzx.get_nodes(node_type=NodeType.O)))
        if len(neighbouring_boundaries) > 0:
            boundary = min(neighbouring_boundaries)
            bx = 1.4 * rho * np.cos(phi)
            by = 1.4 * rho * np.sin(phi)
            placements[boundary] = (bx, by)
        phi += step

    return ManualLayout(placements)

if __name__ == "__main__":
    pyzx_graph = zx.Graph()

    layer = 0
    for q in range(4):
        pyzx_graph.add_vertex(ty = zx.VertexType.X)

    for q in range(4):
        pyzx_graph.add_vertex(ty = zx.VertexType.Z)

    for q in range(7):
        pyzx_graph.add_vertex(ty = zx.VertexType.BOUNDARY)

    for edge in [(0,4), (0,7), (1,4), (1,5), (1,6), (2, 5), (2, 7), (3, 6), (3, 7), (0,8), (2, 9), (3, 10), (4, 11), (5, 12), (6, 13), (7, 14)]:
        pyzx_graph.add_edge(edge, zx.EdgeType.SIMPLE)

    with open("../assets/pyzx/steane-code-qubits7-volume12.json", 'w') as file:
        file.write(pyzx_graph.to_json())

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_graph)
    vzx.print_summary()

    CycleBasisAnalyser.analyse(vzx)

    BlockGraphConstructor.realise_nodes(vzx= vzx,
                                        specifications = {
            0 : (CubeKind.ZXZ, Coordinates(-1,  0,  0)),
            1 : (CubeKind.ZZX, Coordinates(-1,  1,  1)),
            2 : (CubeKind.XZZ, Coordinates( 0, -1,  0)),
            3 : (CubeKind.XZZ, Coordinates( 0,  1,  0)),
            4 : (CubeKind.ZXX, Coordinates(-1,  0,  1)),
            5 : (CubeKind.XZX, Coordinates( 0, -1,  1)),
            6 : (CubeKind.XZX, Coordinates( 0,  1,  1)),
            7 : (CubeKind.XXZ, Coordinates( 0,  0,  0)),
            8 : (CubeKind.OOO, Coordinates(-2,  0,  0)),
            9 : (CubeKind.OOO, Coordinates( 0, -2,  0)),
            10: (CubeKind.OOO, Coordinates( 0,  2,  0)),
            11: (CubeKind.OOO, Coordinates(-1,  0,  2)),
            12: (CubeKind.OOO, Coordinates( 0, -1,  2)),
            13: (CubeKind.OOO, Coordinates( 0,  1,  2)),
            14: (CubeKind.OOO, Coordinates( 1,  0,  0)),
        }
                                        )

    BlockGraphConstructor.realise_edges(vzx= vzx,
                                        specifications = {
            (1, 5): PathSpecification(
                source_cube=min(vzx.get_realising_cubes(1)),
                target_cube=min(vzx.get_realising_cubes(5)),
                extras=[
                    (CubeKind.ZZX, Coordinates(-2, 1, 1)),
                    (CubeKind.ZZX, Coordinates(-2, 0, 1)),
                    (CubeKind.ZZX, Coordinates(-2, -1, 1)),
                    (CubeKind.ZZX, Coordinates(-1, -1, 1))
                ],
                pipes=[
                    EdgeType.IDENTITY for _ in range(5)
                ]
            )
        }
                                        )
    hexagon = prepare_layout()
    viewer = VolumetricZxGraphViewer(vzx, "steane-code-7", hexagon)
    viewer.display()