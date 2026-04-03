from logging import basicConfig

import numpy as np
import pyzx as zx
from pyzx import VertexType

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_zx import NodeId, NodeType
from qelebrimbor.vedo.azg_viewer import AugmentedZxGraphViewer

import logging

from qelebrimbor.vedo.zx_layout.manual import ManualLayout

console = logging.getLogger(__name__)
basicConfig(level=logging.CRITICAL)

logging.getLogger('qelebrimbor.vedo').setLevel(logging.CRITICAL)

def find_terminal_node(graph: zx.graph.base.BaseGraph, qubit: int) -> int:
    return max(
        filter(lambda vt: graph.qubit(vt) == qubit , graph.vertices())
    )

def add_steane_chunk(graph: zx.graph.base.BaseGraph, layer: int, target_qubits: list[int]):
    row = layer
    start = graph.add_vertex(ty = VertexType.X, row = row, qubit = 0)
    row += 2
    previous = start
    for target_qubit in target_qubits:
        terminal = find_terminal_node(graph, target_qubit)
        control = graph.add_vertex(ty = VertexType.Z, row = row, qubit = 0)
        target = graph.add_vertex(ty = VertexType.X, row = row, qubit = target_qubit)
        graph.add_edge( (control, target) )
        graph.add_edge((previous, control), zx.EdgeType.HADAMARD if previous == start else zx.EdgeType.SIMPLE)
        graph.add_edge((terminal, target), zx.EdgeType.SIMPLE)
        row += 1
        previous = control
    row += 1
    final = graph.add_vertex(ty = VertexType.X, row = row, qubit = 0)

    graph.add_edge( (previous, final), zx.EdgeType.HADAMARD)

    return row

if __name__ == "__main__":
    pyzx_graph = zx.Graph()

    layer = 0
    for q in range(4):
        pyzx_graph.add_vertex(ty = VertexType.X)

    for q in range(4):
        pyzx_graph.add_vertex(ty = VertexType.Z)

    for q in range(7):
        pyzx_graph.add_vertex(ty = VertexType.BOUNDARY)

    for edge in [(0,4), (0,7), (1,4), (1,5), (1,6), (2, 5), (2, 7), (3, 6), (3, 7), (0,8), (2, 9), (3, 10), (4, 11), (5, 12), (6, 13), (7, 14)]:
        pyzx_graph.add_edge(edge, zx.EdgeType.SIMPLE)

    with open("../assets/zx/steane-code-qubits7-volume12.json", 'w') as file:
        file.write(pyzx_graph.to_json())

    azx = AugmentedZxGraph.from_pyzx_graph(pyzx_graph)

    content = ""
    for node in azx.get_nodes(node_type = NodeType.Z):
        node_type = azx.get_node_type(node)
        content += f" {node}:{node_type}"
    print(f"Nodes-Z: {content}")
    content = ""
    for node in azx.get_nodes(node_type = NodeType.X):
        node_type = azx.get_node_type(node)
        content += f" {node}:{node_type}"
    print(f"Nodes-X: {content}")
    for edge in azx.edges:
        print(f"{edge}")

    placements: dict[NodeId, tuple[float, float]] = {}

    rho = 2.0
    phi = 0.0
    step = np.pi / 3.0
    placements[2]  = (0.0,  0.75)
    placements[9]  = (0.75,  0.5)
    placements[5]  = (0.0, -0.75)
    placements[12] = (-0.75, -0.5)
    # placements[9] = (0.7 * np.cos(step), 0.7 * np.sin(step))
    for node in [1,4,0,7,3,6]:
        x = rho * np.cos(phi)
        y = rho * np.sin(phi)
        placements[node] = (x,y)
        neighbouring_boundaries = list(filter(lambda bd: azx.has_edge(node, bd), azx.get_nodes(node_type=NodeType.O)))
        if len(neighbouring_boundaries) > 0:
            boundary = min(neighbouring_boundaries)
            bx = 1.4 * rho * np.cos(phi)
            by = 1.4 * rho * np.sin(phi)
            placements[boundary] = (bx, by)
        phi += step
    hexagon = ManualLayout(placements)

    viewer = AugmentedZxGraphViewer(azx, "steane-code-7", hexagon)
    viewer.display()