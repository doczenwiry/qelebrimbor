from qelebrimbor.common.components import ZxNode
from qelebrimbor.common.attributes_zx import NodeId
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph


class ManualLayout(ZxLayout):
    def __init__(self, graph: VolumetricZxGraph, placements: dict[NodeId, tuple[float, float]]):
        self.placements: dict[ZxNode, tuple[float, float]] = dict()
        for node_id in placements:
            self.placements[graph.get_zx_node(node_id)] = placements[node_id]

    def get_node_placement(self, node: ZxNode) -> tuple[float, float]:
        return self.placements[node]