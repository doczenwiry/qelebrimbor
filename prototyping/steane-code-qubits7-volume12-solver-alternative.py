import numpy as np
import pyzx as zx
import networkx as nx

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.least_cycle_analyser import MinimalCycleBasisAnalyser
from qelebrimbor.utilities.ring_making import find_realisation, find_completion, extend_unrealised
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.attributes_zx import NodeId, NodeType, EdgeType
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

from qelebrimbor.vedo.zx_layout.abstract import ZxLayout
from qelebrimbor.vedo.zx_layout.manual import ManualLayout

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.pathfinders.pathfinder_dfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.ringfinders.ringfinder_bfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.utilities.ring_making').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.utilities.blockgraph_constructor').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.vedo').setLevel(logging.CRITICAL)

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
        neighbouring_boundaries = list(
            map(lambda bd: bd.id,
                filter(lambda bd: vzx.has_edge(nd, bd.id), vzx.get_zx_nodes(node_type=NodeType.O)))
        )
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

    BlockGraphConstructor.realise_nodes(
        vzx = vzx,
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
        vzx = vzx,
        specifications = {
            (s,t) : PathSpecification(
                source_cube = vzx.get_zx_node(s).realising_cube,
                target_cube = vzx.get_zx_node(t).realising_cube,
                pipes = [ vzx.get_zx_edge(s,t).type ]
            )
            for s, t in [ (2,5) , (0,7) , (0,4) , (1,4) ]
        }
    )
    BlockGraphConstructor.realise_edges(
        vzx = vzx,
        specifications = {
            (1,5) : PathSpecification(
                source_cube = vzx.get_zx_node(1).realising_cube,
                target_cube = vzx.get_zx_node(5).realising_cube,
                extras = [ BgCube(kind=CubeKind.XZZ, position=Coordinates(0,0,1)) ],
                pipes = [ vzx.get_zx_edge(1,5).type , EdgeType.IDENTITY ]
            ),
            (2,7) : PathSpecification(
                source_cube=vzx.get_zx_node(2).realising_cube,
                target_cube=vzx.get_zx_node(7).realising_cube,
                extras=[BgCube(kind=CubeKind.ZXX, position=Coordinates(-1, 1, 2))],
                pipes=[vzx.get_zx_edge(2, 7).type, EdgeType.IDENTITY]
            )
        }
    )

    BlockGraphConstructor.realise_nodes(
        vzx = vzx,
        specifications = {
            3 : BgCube(kind=CubeKind.ZZX, position=Coordinates(-1, 0, 1)),
            6 : BgCube(kind=CubeKind.XXZ, position=Coordinates( 0,-1, 0))
        }
    )
    BlockGraphConstructor.realise_edges(
        vzx = vzx,
        specifications = {
            (s,t) : PathSpecification(
                source_cube = vzx.get_zx_node(s).realising_cube,
                target_cube = vzx.get_zx_node(t).realising_cube,
                pipes = [ vzx.get_zx_edge(s,t).type ]
            )
            for s, t in [ (3,7) , (1,6) ]
        }
    )
    BlockGraphConstructor.realise_edges(
        vzx = vzx,
        specifications = {
            (3,6) : PathSpecification(
                source_cube = vzx.get_zx_node(3).realising_cube,
                target_cube = vzx.get_zx_node(6).realising_cube,
                extras = [
                    BgCube(kind=CubeKind.ZXX, position=Coordinates(-1,-1, 1)),
                    BgCube(kind=CubeKind.ZXZ, position=Coordinates(-1,-1, 0))
                ],
                pipes = [ vzx.get_zx_edge(3,6).type , EdgeType.IDENTITY, EdgeType.IDENTITY ]
            ),
        }
    )

    # extend_unrealised(vzx)

    vzx.log_report()

    hexagon = prepare_layout()
    viewer = VolumetricZxGraphViewer(vzx, "steane-code-7", hexagon)
    viewer.display()