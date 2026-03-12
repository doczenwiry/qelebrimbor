import logging
from typing import Iterable

console = logging.getLogger(__name__)

import numpy as np

from qelebrimbor.helpers.spacetime import Spacetime, Octant
from qelebrimbor.common.coordinates import Coordinates

class CoordinatesHelper:
    MOVE_XM_YP = Spacetime.XM + Spacetime.YP
    MOVE_XM_YM = Spacetime.XM + Spacetime.YM
    MOVE_XP_YM = Spacetime.XP + Spacetime.YM
    MOVE_XP_YP = Spacetime.XP + Spacetime.YP

    @staticmethod
    def get_octahedron(manhattan_distance: int) -> Iterable[Coordinates]:
        octahedron = []

        x = 0
        for z in range(- manhattan_distance, manhattan_distance + 1):
            current = Coordinates(x, 0, z)
            octahedron.append(current)
            for _ in range(x):
                current = current + CoordinatesHelper.MOVE_XM_YP
                octahedron.append(current)
            for _ in range(x):
                current = current + CoordinatesHelper.MOVE_XM_YM
                octahedron.append(current)
            for _ in range(x):
                current = current + CoordinatesHelper.MOVE_XP_YM
                octahedron.append(current)
            for _ in range(x-1):
                current = current + CoordinatesHelper.MOVE_XP_YP
                octahedron.append(current)
            x += +1 if np.sign(z) == -1 else -1

        return octahedron

    @staticmethod
    def get_octahedron_face(manhattan_distance: int, octant: Octant) -> Iterable[Coordinates]:
        return filter(
            lambda position : Spacetime.in_octant(position, octant),
            CoordinatesHelper.get_octahedron(manhattan_distance)
        )

    @staticmethod
    def get_hemi_octahedron(manhattan_distance: int, upper: bool = True) -> Iterable[Coordinates]:
        positions = [
            position for position in CoordinatesHelper.get_octahedron(manhattan_distance)
            if (+1 if upper else -1) * position.z >= 0
        ]

        return positions