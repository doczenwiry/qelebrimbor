from qelebrimbor.common.components_zx import NodeId
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout


class ManualLayout(ZxLayout):
    def __init__(self, placements: dict[NodeId, tuple[float, float]]):
        self.placements = placements

    def get_node_placement(self, node: NodeId) -> tuple[float, float]:
        return self.placements[node]