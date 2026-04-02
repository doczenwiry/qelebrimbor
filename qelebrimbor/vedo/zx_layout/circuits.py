from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_zx import NodeId
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout


class CircuitLayout(ZxLayout):
    def __init__(self, azx: AugmentedZxGraph):
        self.placements = []

        for node in azx.nodes:
            self.placements.append( (azx.get_qubit(node), azx.get_node_layer(node)) )

    def get_node_placement(self, node: NodeId) -> tuple[int, int]:
        return self.placements[node]