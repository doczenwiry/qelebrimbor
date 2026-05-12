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

from qelebrimbor.core.coordinates import Coordinates

import logging

from qelebrimbor.helpers.spacetime import SpacetimeHelper

console = logging.getLogger(__name__)


class ColorlessRing:
    def __init__(self, anchor: Coordinates):
        self.__positions: list[Coordinates] = [ anchor ]
        self.__occupied: set[Coordinates] = { anchor }

    @property
    def anchor(self) -> Coordinates:
        return self.__positions[0]

    @property
    def terminal(self) -> Coordinates:
        return self.__positions[-1]

    @property
    def volume(self) -> int:
        return len(self.__positions)

    @property
    def distance(self) -> int:
        return self.anchor.get_manhattan_distance(self.terminal)

    def occupies(self, position: Coordinates) -> bool:
        return position in self.__occupied

    def closed(self):
        return self.volume >= 4 and self.distance == 1

    def append(self, position: Coordinates):
        if position in self.__occupied:
            raise Exception(f"Position {position} already occupied by ColorlessRing.")

        self.__positions.append(position)
        self.__occupied.add(position)

    def extend(self, position: Coordinates) -> ColorlessRing:
        cp = ColorlessRing(self.anchor)
        cp.__positions.extend(self.__positions[1:])
        cp.__occupied.update(self.__occupied)
        cp.append(position)
        return cp

    def __lt__(self, other: ColorlessRing) -> bool:
        return self.volume.__lt__(other.volume)

    def __str__(self) -> str:
        content = f"{self.anchor}"

        for index in range(1, len(self.__positions)):
            content += f" -- {str(self.__positions[index])}"

        if self.closed():
            content += f" -- {self.anchor}"
        else:
            content += f" -- [OPEN]"

        return content