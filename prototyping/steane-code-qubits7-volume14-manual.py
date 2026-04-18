import numpy as np
import pyzx as zx
import networkx as nx

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeId, NodeType, EdgeType
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
    placements[1] = (0.0, 0.0)
    placements[7] = (0.7 * np.cos(step), 0.7 * np.sin(step))
    for node in [0,2,4,5,6,3]:
        x = rho * np.cos(phi)
        y = rho * np.sin(phi)
        placements[node] = (x,y)
        boundary = min(filter(lambda bd: vzx.has_edge(node, bd), vzx.get_nodes(node_type = NodeType.O)))
        bx = 1.4 * rho * np.cos(phi)
        by = 1.4 * rho * np.sin(phi)
        placements[boundary] = (bx, by)
        phi += step
    return ManualLayout(placements)

if __name__ == "__main__":
    pyzx_graph = zx.Graph()

    layer = 0
    for q in range(1,8):
        pyzx_graph.add_vertex(ty = zx.VertexType.X, row = layer, qubit = q)

    layer += 1
    layer = add_steane_chunk(pyzx_graph, layer, target_qubits= [1, 2, 3, 4])
    layer += 1
    layer = add_steane_chunk(pyzx_graph, layer, target_qubits= [1, 2, 5, 6])
    layer += 1
    layer = add_steane_chunk(pyzx_graph, layer, target_qubits= [1, 3, 5, 7])
    layer += 1

    for q in range(1,8):
        terminal = find_terminal_node(pyzx_graph, q)
        boundary = pyzx_graph.add_vertex(ty = zx.VertexType.BOUNDARY, row = layer, qubit = q)
        pyzx_graph.add_edge((terminal, boundary), zx.EdgeType.SIMPLE)

    # Hadamard color-changes
    for vt in [ 7, 16, 17, 26, 27, 36]:
        zx.basicrules.color_change(pyzx_graph, vt)

    # Spider fusion
    zx.simplify.spider_simp(pyzx_graph)

    # Identity rule
    zx.simplify.id_simp(pyzx_graph)

    with open("../assets/pyzx/steane-code-qubits7-volume14.json", 'w') as file:
        file.write(pyzx_graph.to_json())

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_graph)
    vzx.print_summary()

    CycleBasisAnalyser.analyse(vzx)

    BlockGraphConstructor.realise_nodes(vzx= vzx,
                                        specifications = {
            0 : (CubeKind.XXZ, Coordinates( 0,  0,  0)),
            1 : (CubeKind.ZZX, Coordinates( 1,  0,  1)),
            2 : (CubeKind.ZXZ, Coordinates(-1,  0,  0)),
            3 : (CubeKind.XZZ, Coordinates( 0,  1,  0)),
            4 : (CubeKind.ZXX, Coordinates(-1,  0,  1)),
            5 : (CubeKind.ZZX, Coordinates(-1,  1,  1)),
            6 : (CubeKind.XZX, Coordinates( 0,  1,  1)),
            7 : (CubeKind.OOO, Coordinates( 2,  0,  1)),
            8 : (CubeKind.OOO, Coordinates(-2,  0,  0)),
            9 : (CubeKind.OOO, Coordinates( 0,  2,  0)),
            10: (CubeKind.OOO, Coordinates( 1,  0,  0)),
            11: (CubeKind.OOO, Coordinates(-1,  2,  1)),
            12: (CubeKind.OOO, Coordinates(-1,  0,  2)),
            13: (CubeKind.OOO, Coordinates( 0,  1,  2))
        }
                                        )

    BlockGraphConstructor.realise_edges(vzx= vzx,
                                        specifications = {
            (0, 1) : PathSpecification(
                source_cube = vzx.get_zx_node(0).realising_cube,
                target_cube = vzx.get_zx_node(1).realising_cube,
                extras = [
                    (CubeKind.XXZ, Coordinates( 0, -1,  0)),
                    (CubeKind.ZXZ, Coordinates( 1, -1,  0)),
                    (CubeKind.ZXX, Coordinates( 1, -1,  1))
                ],
                pipes = [ EdgeType.IDENTITY for _ in range(4) ],
            ),
            (1, 4) : PathSpecification(
                source_cube = vzx.get_zx_node(1).realising_cube,
                target_cube = vzx.get_zx_node(4).realising_cube,
                extras = [
                    (CubeKind.ZZX, Coordinates( 0,  0,  1)),
                    (CubeKind.ZZX, Coordinates( 0, -1,  1)),
                    (CubeKind.ZZX, Coordinates(-1, -1,  1))
                ],
                pipes = [ EdgeType.IDENTITY for _ in range(4) ],
            ),
            (1, 6) : PathSpecification(
                source_cube = vzx.get_zx_node(1).realising_cube,
                target_cube = vzx.get_zx_node(6).realising_cube,
                extras = [
                    (CubeKind.ZZX, Coordinates(1,1,1))
                ],
                pipes = [ EdgeType.IDENTITY ]
            )
        }
                                        )

    hexagon = prepare_layout()
    viewer = VolumetricZxGraphViewer(vzx, "steane-code-7", hexagon)
    viewer.display()