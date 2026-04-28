from qelebrimbor.common.components import BgCube
from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.attributes_bg import CubeId

from logging import getLogger
console = getLogger(__name__)

class PathSpecification:
    def __init__(
            self, source_cube: BgCube, target_cube: BgCube,
            extras: list[BgCube] | None = None,
            pipes: list[EdgeType] | None = None
    ):
        self.source_cube = source_cube
        self.target_cube = target_cube
        self.extras = extras if extras is not None else []
        self.pipes = pipes if pipes is not None else [ EdgeType.IDENTITY ]

    def __str__(self):
        content = f"{self.source_cube} -{self.pipes[0].name[0]}-"
        for e in range(len(self.extras)):
            content += f" {self.extras[e]} -{self.pipes[e+1].name[0]}-"
        content += f" {self.target_cube}"
        return content

    def __repr__(self):
        return str(self)

    def weight(self):
        return len(self.extras) + 1