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

from qelebrimbor.core.colorless.ring import ColorlessRing
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.reach import Reach
from qelebrimbor.helpers.spacetime import Step


class FrenetTwisting(Enum):
    NONE = 0  # Represents the absence of a turn (i.e. straight line)
    ZERO = 1  # Represents a 0 degree twisting (LL, RR, UU, DD)
    QT_P = 2  # Represents a quarter of a twisting in the positive direction (LU, RD, UR, DL)
    QT_M = 3  # Represents a quarter of a twisting in the negative direction (LD, RU, UL, DR)
    FULL = 4  # Represents a reverse twisting (LR, RL, UD, DU)

    def mirrored(self) -> FrenetTwisting:
        if self == FrenetTwisting.QT_P:
            return FrenetTwisting.QT_M
        elif self == FrenetTwisting.QT_M:
            return FrenetTwisting.QT_P
        else:
            return self

    __REPRESENTATIONS = ["N", "0", "+", "-", "π"]

    def __repr__(self) -> str:
        return FrenetTwisting.__REPRESENTATIONS[self.value]


class FrenetRing:
    __INITIAL: tuple[Coordinates, Coordinates, Step] = Coordinates(0, 0, 0), Reach.XY.value, Step.XP

    def __init__(self):
        self.__terminal: tuple[Coordinates, Coordinates, Step] = FrenetRing.__INITIAL
        self.__positions: list[Coordinates] = list()
        self.__steps: list[Step] = list()
        self.__twists: list[FrenetTwisting] = list()

    @property
    def length(self) -> int:
        return len(self.__twists)

    @property
    def positions(self) -> list[Coordinates]:
        return self.__positions

    def colorless_ring(self) -> ColorlessRing:
        ring = ColorlessRing()
        for index in range(self.length):
            ring.append(self.__positions[(index - 1) % self.length])
        return ring

    @property
    def steps(self) -> list[Step]:
        return self.__steps

    def closed(self) -> bool:
        return self.__terminal == FrenetRing.__INITIAL

    def occupies(self, position: Coordinates) -> bool:
        return position in self.__positions

    def append(self, twist: FrenetTwisting):
        terminal_position, terminal_reach, terminal_step = self.__terminal

        following_reach = terminal_reach
        if twist == FrenetTwisting.QT_P or twist == FrenetTwisting.QT_M:
            following_reach = following_reach.cross(terminal_step.value)
            if twist == FrenetTwisting.QT_M:
                following_reach = -following_reach

        following_step = following_reach.cross(terminal_step.value)
        if twist == FrenetTwisting.FULL:
            following_step = -following_step

        following_position = terminal_position + following_step

        if following_position in self.__positions:
            raise ValueError(f"Position {following_position} already occupied by ColorlessRing.")

        self.__positions.append(following_position)
        self.__twists.append(twist)
        self.__steps.append(Step(following_step))
        self.__terminal = following_position, following_reach, Step(following_step)

    def extend(self, *twists: FrenetTwisting) -> FrenetRing:
        extended = FrenetRing()
        extended.__terminal = self.__terminal
        extended.__positions.extend(self.__positions)
        extended.__steps.extend(self.__steps)
        extended.__twists.extend(self.__twists)
        for twist in twists:
            extended.append(twist)
        return extended

    def mirrors(self, other: FrenetRing) -> bool:
        return all(self.__twists[idx] == other.__twists[idx].mirrored() for idx in range(self.length))

    def rotates(self, other: FrenetRing) -> bool:
        if self.length != other.length:
            return False

        return any(
            all(
                self.__twists[(idx + shift) % self.length] == other.__twists[(idx + shift) % self.length]
                for idx in range(self.length)
            )
            for shift in range(self.length)
        )

    def __lt__(self, other: FrenetRing) -> bool:
        return self.length.__lt__(other.length)

    def __str__(self) -> str:
        return str(self.__twists)
