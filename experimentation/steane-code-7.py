import pyzx as zx
from pyzx import VertexType
from pyzx.basicrules import color_change
from pyzx.rules import spider


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
    for q in range(1,8):
        pyzx_graph.add_vertex(ty = VertexType.X, row = layer, qubit = q)

    layer += 1

    layer = add_steane_chunk(pyzx_graph, layer, target_qubits= [1, 2, 3, 4])

    layer += 1

    layer = add_steane_chunk(pyzx_graph, layer, target_qubits= [1, 2, 5, 6])

    layer += 1

    layer = add_steane_chunk(pyzx_graph, layer, target_qubits= [1, 3, 5, 7])

    layer += 1

    for q in range(1,8):
        terminal = find_terminal_node(pyzx_graph, q)
        boundary = pyzx_graph.add_vertex(ty = VertexType.BOUNDARY, row = layer, qubit = q)
        pyzx_graph.add_edge((terminal, boundary), zx.EdgeType.SIMPLE)

    zx.draw(pyzx_graph, labels = True)

    # Hadamard color-changes
    for vt in [ 7,16, 17, 26, 27, 36]:
        color_change(pyzx_graph, vt)

    # Spider fusion
    zx.simplify.spider_simp(pyzx_graph)

    # Identity rule
    zx.simplify.id_simp(pyzx_graph)

    zx.draw(pyzx_graph, labels = True)