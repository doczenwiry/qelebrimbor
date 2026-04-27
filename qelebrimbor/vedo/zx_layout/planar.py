import networkx as nx

from qelebrimbor.common.components import ZxNode
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

class PlanarLayout(ZxLayout):
    def __init__(self, graph: VolumetricZxGraph, scale: int = 10):
        self.placements: dict[ZxNode, tuple[float, float]] = dict()
        for node_id, position in nx.planar_layout(graph, scale = scale).items():
            x, y = position
            self.placements[graph.get_zx_node(node_id)] = (y, x)

    def get_node_placement(self, node: ZxNode) -> tuple[float, float]:
        return self.placements[node]