from qelebrimbor.common.components import BgCube
from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.attributes_bg import CubeId

from logging import getLogger
console = getLogger(__name__)

class PathSpecification:
    def __init__(self, source_cube: CubeId, target_cube: CubeId,
                 extras: list[BgCube] | None = None,
                 pipes: list[EdgeType] | None = None
                 ):
        self.source_cube = source_cube
        self.target_cube = target_cube
        self.extras = extras if extras is not None else []
        self.pipes = pipes if pipes is not None else [ EdgeType.IDENTITY ]

    def __str__(self):
        return f"#{self.source_cube} - {self.extras} - #{self.target_cube}"

    def __repr__(self):
        return str(self)

    def weight(self):
        return len(self.extras) + 1