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

from enum import Enum
from typing import Iterator

from qelebrimbor.core.coordinates import Coordinates


class Octant(Enum):
    PPP = Coordinates(+1, +1, +1)
    PPM = Coordinates(+1, +1, -1)
    PMP = Coordinates(+1, -1, +1)
    PMM = Coordinates(+1, -1, -1)
    MPP = Coordinates(-1, +1, +1)
    MPM = Coordinates(-1, +1, -1)
    MMP = Coordinates(-1, -1, +1)
    MMM = Coordinates(-1, -1, -1)

    def __getitem__(self, index):
        return self.value[index]


class Step(Enum):
    XP = Coordinates(+1, 0, 0)
    XM = Coordinates(-1, 0, 0)
    YP = Coordinates(0, +1, 0)
    YM = Coordinates(0, -1, 0)
    ZP = Coordinates(0, 0, +1)
    ZM = Coordinates(0, 0, -1)

    def dot(self, other: Step) -> int:
        return int(self.value.dot(other.value))

    def cross(self, other: Step) -> Step:
        return Step(self.value.cross(other.value))

    def __mul__(self, other) -> Step:
        return Step(self.value * other)

    def __rmul__(self, other) -> Step:
        return self * other

    def __neg__(self) -> Step:
        return Step(-self.value)

    def orthogonals(self) -> Iterator[Step]:
        return (step for step in Step if self.dot(step) == 0)

    __STEPS_LABELS = {XP: "+X", XM: "-X", YP: "+Y", YM: "-Y", ZP: "+Z", ZM: "-Z"}

    def __str__(self) -> str:
        return Step.__STEPS_LABELS[self.value]  # f"Step.{self.name}"

    def __repr__(self) -> str:
        return Step.__STEPS_LABELS[self.value]


class SpacetimeHelper:
    ORIGIN = Coordinates(0, 0, 0)

    XP = Coordinates(+1, 0, 0)
    XM = Coordinates(-1, 0, 0)
    YP = Coordinates(0, +1, 0)
    YM = Coordinates(0, -1, 0)
    ZP = Coordinates(0, 0, +1)
    ZM = Coordinates(0, 0, -1)

    XYZ = Coordinates(+1, +1, +1)
    XY = Coordinates(0, 0, +1)
    XZ = Coordinates(0, +1, 0)
    YZ = Coordinates(+1, 0, 0)

    STEPS = [XP, YP, ZP, XM, YM, ZM]
    PLANES = [XY, XZ, YZ]

    @staticmethod
    def contains(reach: Coordinates, step: Coordinates) -> bool:
        return reach.dot(step) == 0

    @staticmethod
    def get_direction(source: Coordinates, target: Coordinates) -> Coordinates:
        differences = [1 if cs != ct else 0 for cs, ct in zip(source, target)]

        if sum(differences) != 1:
            raise Exception(f"Coordinates are not co-linear and thus do not have a line-of-sight [{source}/{target}.")

        deltas = [+1 if cs - ct < 0 else -1 for cs, ct in zip(source, target)]

        line_of_sight = Coordinates(*(difference * delta for difference, delta in zip(differences, deltas)))

        if SpacetimeHelper.ORIGIN.get_manhattan_distance(line_of_sight) != 1:
            raise Exception(f"Erroneous computation of line of sight [{source}/{target} = {line_of_sight}].")

        return line_of_sight

    @staticmethod
    def get_step_constellation(reach: Coordinates) -> list[Coordinates]:
        return [step for step in SpacetimeHelper.STEPS if reach.dot(step) == 0]

    @staticmethod
    def get_constellation(position: Coordinates, restriction: Coordinates | None = None) -> list[Coordinates]:
        constellation = []
        for step in SpacetimeHelper.STEPS:
            if restriction is None or restriction.dot(step) == 0:
                constellation.append(position + step)
        return constellation

    @staticmethod
    def in_octant(position: Coordinates, octant: Octant = Octant.PPP) -> bool:
        return all(position[i] * octant[i] >= 0 for i in range(3))
