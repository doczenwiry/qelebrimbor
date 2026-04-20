import pyzx
import numpy as np

from qelebrimbor.utilities.least_cycle_analyser import MinimalCycleBasisAnalyser
from qelebrimbor.utilities.ring_making import find_realisation, find_completion, extend_unrealised
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.attributes_zx import NodeId, NodeType
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout

from qelebrimbor.vedo.zx_layout.manual import ManualLayout

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.helpers.blockgraph').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders.pathfinder_dfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.ringfinders.ringfinder_bfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.utilities.ring_making').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.vedo').setLevel(logging.CRITICAL)

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
        boundary = min(
            map(lambda bd: bd.id,
                filter(lambda bd: vzx.has_edge(node, bd.id), vzx.get_zx_nodes(node_type=NodeType.O)))
        )
        bx = 1.4 * rho * np.cos(phi)
        by = 1.4 * rho * np.sin(phi)
        placements[boundary] = (bx, by)
        phi += step
    return ManualLayout(placements)

if __name__ == "__main__":
    pyzx_graph = pyzx.Graph()

    layer = 0
    for q in range(1,8):
        pyzx_graph.add_vertex(ty = pyzx.VertexType.X, row = layer, qubit = q)

    layer += 1
    layer = add_steane_chunk(pyzx_graph, layer, target_qubits= [1, 2, 3, 4])
    layer += 1
    layer = add_steane_chunk(pyzx_graph, layer, target_qubits= [1, 2, 5, 6])
    layer += 1
    layer = add_steane_chunk(pyzx_graph, layer, target_qubits= [1, 3, 5, 7])
    layer += 1

    for q in range(1,8):
        terminal = find_terminal_node(pyzx_graph, q)
        boundary = pyzx_graph.add_vertex(ty = pyzx.VertexType.BOUNDARY, row = layer, qubit = q)
        pyzx_graph.add_edge((terminal, boundary), pyzx.EdgeType.SIMPLE)

    # Hadamard color-changes
    for vt in [ 7, 16, 17, 26, 27, 36]:
        pyzx.basicrules.color_change(pyzx_graph, vt)

    # Spider fusion
    pyzx.simplify.spider_simp(pyzx_graph)

    # Identity rule
    pyzx.simplify.id_simp(pyzx_graph)

    with open("../assets/pyzx/steane-code-qubits7-volume14.json", 'w') as file:
        file.write(pyzx_graph.to_json())

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_graph)

    MinimalCycleBasisAnalyser.analyse(vzx)
    cycles = MinimalCycleBasisAnalyser.decompose_nodes(vzx)

    index = 0
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_realisation(vzx, cycle, maximal_overhead = 4)

    index = 1
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 4)

    index = 2
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_completion(vzx, cycle, maximal_overhead = 10)

    # TODO: adapt find_completion to identify unrealised edges when all spiders are already realised

    # extend_unrealised(vzx)

    vzx.log_report()

    hexagon = prepare_layout()
    viewer = VolumetricZxGraphViewer(graph= vzx, label ="steane-code-7", layout = hexagon)
    viewer.display()