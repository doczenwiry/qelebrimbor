#   Copyright 2026 Seweryn Dynerowicz
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from math import sqrt
from typing import NamedTuple


class Coordinates(NamedTuple):
    x: float
    y: float
    z: float

    def __add__(self, other):
        return Coordinates(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Coordinates(self.x - other.x, self.y - other.y, self.z - other.z)

    def scale(self, scalar):
        if isinstance(scalar, (int, float)):
            return Coordinates(self.x * scalar, self.y * scalar, self.z * scalar)
        raise NotImplementedError("Scalar multiplication requires <int> or <float>.")

    def __mul__(self, scalar: int | float):
        if isinstance(scalar, (int, float)):
            return Coordinates(self.x * scalar, self.y * scalar, self.z * scalar)
        raise NotImplementedError("Scalar multiplication requires <int> or <float>.")
    __rmul__ = __mul__

    def __truediv__(self, scalar: float):
        return Coordinates(self.x / scalar, self.y / scalar, self.z / scalar)

    def normalized(self):
        return self / sqrt(self.dot(self))

    def dot(self, other) -> float:
        return sum([ s * o for s, o in zip(self, other) ])

    def cross(self, other):
        return Coordinates(self.y * other.z - self.z * other.y,
                           self.z * other.x - self.x * other.z,
                           self.x * other.y - self.y * other.x)

    def get_manhattan_distance(self, other):
        return sum([ abs(s - o) for s, o in zip(self, other) ])

    def __different_components(self, other):
        different_x = 1 if self.x != other.x else 0
        different_y = 1 if self.y != other.y else 0
        different_z = 1 if self.z != other.z else 0
        return different_x + different_y + different_z

    # The coordinates are colinear if they share one identical components
    def colinear(self, other) -> bool:
        return self.__different_components(other) == 1

    # The coordinates are coplanar if they share two identical components
    def coplanar(self, other) -> bool:
        return self.__different_components(other) == 2

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"({str(self.x).rjust(2, ' ')},{str(self.y).rjust(2, ' ')},{str(self.z).rjust(2, ' ')})"