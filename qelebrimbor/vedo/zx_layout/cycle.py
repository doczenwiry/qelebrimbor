import numpy as np

from qelebrimbor.common.components import ZxNode
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout, Placement


class CycleLayout(ZxLayout):
    def __init__(self, ring: VolumetricZxGraph):
        self.placements: dict[ZxNode, Placement] = {}

        rho = 2.0
        step = (2.0 * np.pi) / ring.number_of_nodes()
        phi = np.pi - step / 2.0
        for nd in ring.get_zx_nodes():
            x = rho * np.cos(phi)
            y = rho * np.sin(phi)
            self.placements[nd] = (x, y)
            phi -= step

    def get_node_placement(self, node: ZxNode) -> Placement:
        return self.placements[node]