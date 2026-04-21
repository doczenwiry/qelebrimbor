import networkx as nx

from qelebrimbor.vedo.zx_layout.abstract import ZxLayout

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.attributes_zx import NodeId

class PlanarLayout(ZxLayout):
    def __init__(self, graph: VolumetricZxGraph, vertical: bool = True):
        self.placements: dict[NodeId, tuple[float, float]] = dict()
        for node, position in nx.planar_layout(graph, scale = 10).items():
            x, y = position
            self.placements[node] = (y, x)

    def get_node_placement(self, node: NodeId) -> tuple[float, float]:
        return self.placements[node]