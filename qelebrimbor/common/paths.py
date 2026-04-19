from qelebrimbor.common.attributes_bg import CubeId
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.attributes_zx import EdgeType

from logging import getLogger
console = getLogger(__name__)

class PathSpecification:
    def __init__(self, source: CubeId, target: CubeId,
        extras: list[BgCube] | None = None,
        pipes: list[EdgeType] | None = None
    ):
        self.source_cube = source
        self.target_cube = target
        self.extras = extras if extras is not None else []
        self.pipes = pipes if pipes is not None else [ EdgeType.IDENTITY ]

    def weight(self):
        return len(self.extras) + 1