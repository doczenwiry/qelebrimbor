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

from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import Step


class Reach(Enum):
    XYZ = Coordinates(+1, +1, +1)
    XY = Coordinates(0, 0, +1)
    XZ = Coordinates(0, +1, 0)
    YZ = Coordinates(+1, 0, 0)

    def contains(self, step: Step) -> bool:
        return self.value.dot(step.value) == 0

    def get_constellation(self, position: Coordinates = Coordinates(0, 0, 0)) -> list[Coordinates]:
        constellation = []
        for step in Step:
            if self.contains(step):
                constellation.append(position + step)
        return constellation

    @staticmethod
    def from_steps(step1: Step, step2: Step) -> set[Reach]:
        reaches = set()
        if step1.value.dot(step2.value) == 0:
            reaches.add(Reach(step1.value.cross(step2.value).abs()))
        else:
            for index, value in enumerate(Reach.XYZ.value - step1.value.abs()):
                if value != 0:
                    if index == 0:
                        reaches.add(Reach.YZ)
                    elif index == 1:
                        reaches.add(Reach.XZ)
                    else:
                        reaches.add(Reach.XY)
        return reaches

    @staticmethod
    def from_moves(start: Coordinates, inter: Coordinates, final: Coordinates) -> set[Reach]:
        return Reach.from_steps(Step(inter - start), Step(final - inter))

    def __str__(self):
        return f"Reach.{self.name}"

    def __repr__(self):
        return str(self)
