from abc import ABC, abstractmethod

from qelebrimbor.common.components_zx import NodeId

class ZxLayout(ABC):
    @abstractmethod
    def get_node_placement(self, node: NodeId) -> tuple[float, float]:
        pass