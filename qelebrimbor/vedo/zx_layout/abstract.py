from abc import ABC, abstractmethod

from qelebrimbor.common.components import ZxNode

Placement = tuple[float, float]

class ZxLayout(ABC):
    @abstractmethod
    def get_node_placement(self, node: ZxNode) -> Placement:
        pass