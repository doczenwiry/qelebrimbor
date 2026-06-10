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
from qelebrimbor.core.reach import Reach
from qelebrimbor.helpers.spacetime import Step


class FrenetTwisting(Enum):
    ZERO = 0  # Represents a 0 degree twisting (LL, RR, UU, DD)
    QT_P = 1  # Represents a quarter of a twisting in the positive direction (LU, RD, UR, DL)
    QT_M = 2  # Represents a quarter of a twisting in the negative direction (LD, RU, UL, DR)
    FULL = 3  # Represents a reverse twisting (LR, RL, UD, DU)


class FrenetRing:
    __INITIAL: tuple[Coordinates, Coordinates] = Coordinates(0, 0, 0), Reach.XY.value

    def __init__(self):
        self.__terminal: tuple[Coordinates, Coordinates] = FrenetRing.__INITIAL
        self.__positions: set[Coordinates] = {Coordinates(0, 0, 0)}
        self.__steps: list[Step] = [Step.XP]

    @property
    def length(self) -> int:
        return len(self.__positions)

    @property
    def terminal_step(self) -> Step:
        return self.__steps[-1]

    def occupies(self, position: Coordinates) -> bool:
        return position in self.__positions

    def append(self, twist: FrenetTwisting):
        terminal_position, terminal_reach = self.__terminal

        following_reach = terminal_reach
        if twist == FrenetTwisting.QT_P or twist == FrenetTwisting.QT_M:
            following_reach = terminal_reach.cross(self.terminal_step.value)
            if twist == FrenetTwisting.QT_M:
                following_reach = -following_reach

        following_step = following_reach.cross(self.terminal_step.value)
        if twist == FrenetTwisting.FULL:
            following_step = -following_step

        following_position = terminal_position + following_step

        if following_position in self.__positions:
            raise Exception(f"Position {following_position} already occupied by ColorlessRing.")

        self.__positions.add(following_position)
        self.__steps.append(following_step)
        self.__terminal = following_position, following_reach

    def extend(self, twist: FrenetTwisting) -> FrenetRing:
        extended = FrenetRing()
        extended.__terminal = self.__terminal
        extended.__positions.update(self.__positions)
        extended.__steps.extend(self.__steps[1:])
        extended.append(twist)
        return extended

    def __lt__(self, other: FrenetRing) -> bool:
        return self.length.__lt__(other.length)
