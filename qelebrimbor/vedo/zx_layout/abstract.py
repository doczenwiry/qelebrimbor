from abc import ABC, abstractmethod

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_zx import NodeId

class ZxLayout(ABC):
    @abstractmethod
    def __init__(self, azx: AugmentedZxGraph):
        pass

    @abstractmethod
    def get_node_placement(self, node: NodeId) -> tuple[int, int]:
        pass