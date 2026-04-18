import numpy as np

from qelebrimbor.common.attributes_zx import NodeId
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout, Placement


class CycleLayout(ZxLayout):
    def __init__(self, ring: VolumetricZxGraph):
        self.placements: dict[NodeId, Placement] = {}

        rho = 2.0
        step = (2.0 * np.pi) / ring.number_of_nodes()
        phi = np.pi - step / 2.0
        for nd in ring.nodes:
            x = rho * np.cos(phi)
            y = rho * np.sin(phi)
            self.placements[nd] = (x, y)
            phi -= step

    def get_node_placement(self, node: NodeId) -> Placement:
        return self.placements[node]