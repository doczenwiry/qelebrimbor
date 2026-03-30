from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.components_zx import NodeId, EdgeType

from logging import getLogger
console = getLogger(__name__)

class PathSpecification:
    def __init__(self,
        source: NodeId, target: NodeId,
        extras: list[tuple[CubeKind, Coordinates]], pipes: list[EdgeType]
    ):
        self.source = source
        self.target = target
        self.extras = extras if extras is not None else []
        self.pipes = pipes if pipes is not None else [ EdgeType.IDENTITY ]

    def weight(self):
        return len(self.extras) + 1