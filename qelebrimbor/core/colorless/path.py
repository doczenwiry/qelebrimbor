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

from functools import total_ordering
from typing import Iterator

from qelebrimbor.core.coordinates import Coordinates

import logging
console = logging.getLogger(__name__)


@total_ordering
#TODO: replaces qelebrimbor.core.metric.colorless_path.py
class ColorlessPath:
    def __init__(self, start: Coordinates):
        self.__positions: list[Coordinates] = [ start ]
        self.__occupied: set[Coordinates] = { start }

    @property
    def start(self):
        return self.__positions[0]

    @property
    def final(self):
        return self.__positions[-1]

    @property
    def outgoing_port(self):
        return self.__positions[1] if len(self.__positions) > 2 else self.final

    @property
    def incoming_port(self):
        return self.__positions[-2] if len(self.__positions) > 2 else self.start

    @property
    def length(self) -> int:
        return len(self.__positions) - 1

    @property
    def distance(self) -> int:
        return self.start.get_manhattan_distance(self.final)

    def __getitem__(self, index: int) -> Coordinates:
        return self.__positions[index]

    @property
    def steps(self) -> Iterator[Coordinates]:
        return iter(self.__positions[index] - self.__positions[index - 1] for index in range(1, len(self.__positions)))

    def visits(self, position: Coordinates):
        return position in self.__occupied

    def append(self, position: Coordinates):
        if self.final.get_manhattan_distance(position) != 1:
            raise Exception(f"Attempting to extend Path {self} with non-adjacent position {position}.")

        if position in self.__occupied:
            raise Exception(f"Attempting to extend Path {self} with occupied position {position}.")

        self.__positions.append(position)
        self.__occupied.add(position)

    def extend(self, position: Coordinates):
        cp = ColorlessPath(self.start)
        cp.__positions.extend(self.__positions[1:])
        cp.__occupied.update(self.__occupied)

        cp.append(position)

        return cp

    def __lt__(self, other):
        return self.length.__lt__(other.length)

    def __str__(self):
        return " -> ".join(map(str, self.__positions))