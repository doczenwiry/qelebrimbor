import numpy as np

from qelebrimbor.common.components_zx import NodeId
from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout, Placement


class CycleLayout(ZxLayout):
    def __init__(self, ring: AugmentedZxGraph):
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