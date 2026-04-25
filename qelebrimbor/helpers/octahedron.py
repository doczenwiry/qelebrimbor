import logging
console = logging.getLogger(__name__)

from typing import Iterable
import numpy as np

from qelebrimbor.helpers.spacetime import SpacetimeHelper, Octant
from qelebrimbor.common.coordinates import Coordinates

class OctahedronHelper:
    MOVE_XM_YP = SpacetimeHelper.XM + SpacetimeHelper.YP
    MOVE_XM_YM = SpacetimeHelper.XM + SpacetimeHelper.YM
    MOVE_XP_YM = SpacetimeHelper.XP + SpacetimeHelper.YM
    MOVE_XP_YP = SpacetimeHelper.XP + SpacetimeHelper.YP

    @staticmethod
    def get_positions(manhattan_distance: int) -> Iterable[Coordinates]:
        octahedron = []

        x = 0
        for z in range(- manhattan_distance, manhattan_distance + 1):
            current = Coordinates(x, 0, z)
            octahedron.append(current)
            for _ in range(x):
                current = current + OctahedronHelper.MOVE_XM_YP
                octahedron.append(current)
            for _ in range(x):
                current = current + OctahedronHelper.MOVE_XM_YM
                octahedron.append(current)
            for _ in range(x):
                current = current + OctahedronHelper.MOVE_XP_YM
                octahedron.append(current)
            for _ in range(x-1):
                current = current + OctahedronHelper.MOVE_XP_YP
                octahedron.append(current)
            x += +1 if np.sign(z) == -1 else -1

        return octahedron

    @staticmethod
    def get_face_positions(manhattan_distance: int, octant: Octant) -> Iterable[Coordinates]:
        return filter(
            lambda position : SpacetimeHelper.in_octant(position, octant),
            OctahedronHelper.get_positions(manhattan_distance)
        )

    @staticmethod
    def get_hemi_positions(manhattan_distance: int, upper: bool = True) -> Iterable[Coordinates]:
        hemi = +1 if upper else -1
        positions = [
            position for position in OctahedronHelper.get_positions(manhattan_distance)
            if hemi * position.z >= 0
        ]

        return positions