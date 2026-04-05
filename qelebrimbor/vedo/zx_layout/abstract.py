from abc import ABC, abstractmethod

from qelebrimbor.common.components_zx import NodeId

Placement = tuple[float, float]

class ZxLayout(ABC):
    @abstractmethod
    def get_node_placement(self, node: NodeId) -> Placement:
        pass