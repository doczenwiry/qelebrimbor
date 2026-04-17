from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.components_zx import NodeId
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout


class CircuitLayout(ZxLayout):
    def __init__(self, vzx: VolumetricZxGraph):
        self.placements = dict()

        qubits = len(vzx.get_qubits())
        layers = len(vzx.get_layers())
        for node in vzx.nodes:
            qubit = qubits - vzx.get_node_qubit(node) if qubits > 0 else 0
            layer = vzx.get_node_layer(node) if layers > 0 else 0

            self.placements[node] = (layer, qubit)

    def get_node_placement(self, node: NodeId) -> tuple[float, float]:
        return self.placements[node]