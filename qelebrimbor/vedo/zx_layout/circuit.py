from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.attributes_zx import NodeId
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout


class CircuitLayout(ZxLayout):
    def __init__(self, vzx: VolumetricZxGraph, vertical: bool = True):
        self.placements = dict()

        qubits = len(vzx.get_qubits())
        layers = len(vzx.get_layers())
        for zx_node in vzx.get_zx_nodes():
            qubit = qubits - zx_node.qubit if qubits > 0 else 0
            layer = zx_node.layer if layers > 0 else 0

            self.placements[zx_node.id] = (qubit, layer) if vertical else (layer, qubit)

    def get_node_placement(self, node: NodeId) -> tuple[float, float]:
        return self.placements[node]