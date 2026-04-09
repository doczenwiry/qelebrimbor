from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.components_zx import NodeId
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout


class CircuitLayout(ZxLayout):
    def __init__(self, vzx: VolumetricZxGraph):
        self.placements = []

        for node in vzx.nodes:
            self.placements.append((vzx.get_qubit(node), vzx.get_node_layer(node)))

    def get_node_placement(self, node: NodeId) -> tuple[float, float]:
        return self.placements[node]