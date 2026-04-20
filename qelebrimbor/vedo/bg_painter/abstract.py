from abc import ABC, abstractmethod
from typing import Any

from qelebrimbor.common.components import BgCube

class BlockGraphPainter(ABC):
    @staticmethod
    @abstractmethod
    def get_cube_colors(cube: BgCube):
        pass

    @staticmethod
    @abstractmethod
    def get_pipe_colors(source: BgCube, target: BgCube):
        pass