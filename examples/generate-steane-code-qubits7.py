import pyzx
from pyzx.local_search.congruences import unfuse

from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.hexagon import HexagonLayout
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def find_terminal_node(graph: pyzx.graph.base.BaseGraph, qubit: int) -> int:
    return max(
        filter(lambda vt: graph.qubit(vt) == qubit , graph.vertices())
    )

def add_steane_chunk(graph: pyzx.graph.base.BaseGraph, layer: int, target_qubits: list[int]):
    row = layer
    start = graph.add_vertex(ty = pyzx.VertexType.X, row = row, qubit = 0)
    row += 2
    previous = start
    for target_qubit in target_qubits:
        terminal = find_terminal_node(graph, target_qubit)
        control = graph.add_vertex(ty = pyzx.VertexType.Z, row = row, qubit = 0)
        target = graph.add_vertex(ty = pyzx.VertexType.X, row = row, qubit = target_qubit)
        graph.add_edge( (control, target) )
        graph.add_edge((previous, control), pyzx.EdgeType.HADAMARD if previous == start else pyzx.EdgeType.SIMPLE)
        graph.add_edge((terminal, target), pyzx.EdgeType.SIMPLE)
        row += 1
        previous = control
    row += 1
    final = graph.add_vertex(ty = pyzx.VertexType.X, row = row, qubit = 0)

    graph.add_edge((previous, final), pyzx.EdgeType.HADAMARD)

    return row

if __name__ == "__main__":

    circuit = "steane-code-qubits7-spiders7"
    spiders7 = pyzx.Graph()

    layer = 0
    for q in range(1,8):
        spiders7.add_vertex(ty = pyzx.VertexType.X, row = layer, qubit = q)
    layer += 1
    layer = add_steane_chunk(spiders7, layer, target_qubits= [1, 2, 3, 4])
    layer += 1
    layer = add_steane_chunk(spiders7, layer, target_qubits= [1, 2, 5, 6])
    layer += 1
    layer = add_steane_chunk(spiders7, layer, target_qubits= [1, 3, 5, 7])
    layer += 1

    for q in range(1,8):
        terminal = find_terminal_node(spiders7, q)
        boundary = spiders7.add_vertex(ty = pyzx.VertexType.BOUNDARY, row = layer, qubit = q)
        spiders7.add_edge((terminal, boundary), pyzx.EdgeType.SIMPLE)

    # Hadamard color-changes
    for vt in [ 7, 16, 17, 26, 27, 36]:
        pyzx.color_change(spiders7, vt)

    # Spider fusion
    pyzx.simplify.spider_simp(spiders7)

    # Identity rule
    pyzx.simplify.id_simp(spiders7)

    # Re-number vertices
    spiders7 = spiders7.copy()

    with open(f"../assets/pyzx/{circuit}.json", 'w') as file:
        file.write(spiders7.to_json())

    circuit = "steane-code-qubits7-spiders8"
    spiders8 = pyzx.Graph()

    layer = 0
    for q in range(4):
        spiders8.add_vertex(ty=pyzx.VertexType.X)

    for q in range(4):
        spiders8.add_vertex(ty=pyzx.VertexType.Z)

    for q in range(7):
        spiders8.add_vertex(ty=pyzx.VertexType.BOUNDARY)

    for edge in [(0, 4), (0, 7), (1, 4), (1, 5), (1, 6), (2, 5), (2, 7), (3, 6), (3, 7), (0, 8), (2, 9), (3, 10),
                 (4, 11), (5, 12), (6, 13), (7, 14)]:
        spiders8.add_edge(edge, pyzx.EdgeType.SIMPLE)

    with open(f"../assets/pyzx/{circuit}.json", 'w') as file:
        file.write(spiders8.to_json())