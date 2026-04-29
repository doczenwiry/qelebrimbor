from qelebrimbor.common.components import ZxNode
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.vedo.zx_layout.abstract import ZxLayout


class CircuitLayout(ZxLayout):
    def __init__(self, vzx: VolumetricZxGraph, vertical: bool = True):
        self.placements = dict()

        for node in vzx.get_zx_nodes():
            qubit = node.qubit
            layer = node.layer

            self.placements[node] = (qubit, layer) if vertical else (layer, qubit)

    def get_node_placement(self, node: ZxNode) -> tuple[float, float]:
        return self.placements[node]