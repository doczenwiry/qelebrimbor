import numpy as np

from qelebrimbor.common.attributes_zx import NodeId, NodeType
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout

import logging
console = logging.getLogger(__name__)

class HexagonLayout(ZxLayout):
    def __init__(self, graph: VolumetricZxGraphViewer, nodes: list[NodeId], extras: dict[NodeId, tuple[float, float]]):
        self.placements: dict[NodeId, tuple[float, float]] = {}

        step = 2.0 * np.pi / 6.0
        for node in map(lambda nd: nd.id, graph.get_zx_nodes()):
            if node in nodes:
                rho = 2.0
                theta = nodes.index(node) * step
            elif node in extras:
                rho, phi = extras[node]
                theta = 2.0 * np.pi * phi
            else:
                continue
            x = rho * np.cos(theta)
            y = rho * np.sin(theta)
            self.placements[node] = (x,y)
            boundaries = list(filter(
                lambda bd: graph.has_edge(node, bd.id), graph.get_zx_nodes(node_type = NodeType.O)
            ))
            console.info(f"Node {node} has boundaries : {boundaries}")
            try:
                boundary = next(iter(boundaries))
                bx = (rho + 0.7) * np.cos(theta)
                by = (rho + 0.7) * np.sin(theta)
                self.placements[boundary.id] = (bx, by)
            except StopIteration:
                pass

    def get_node_placement(self, node: NodeId) -> tuple[float, float]:
        return self.placements[node] if node in self.placements else (0.0, 0.0)