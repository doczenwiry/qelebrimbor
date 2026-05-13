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

import logging
from functools import total_ordering

from qelebrimbor.core.components import BgCube
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.zx.attributes import EdgeType

console = logging.getLogger(__name__)


@total_ordering
class Ring:
    def __init__(self, anchor: BgCube):
        self.cubes: list[BgCube] = [anchor]
        self.pipes: list[EdgeType] = []
        self.occupied = {anchor.position}

    @property
    def anchor(self) -> BgCube:
        return self.cubes[0]

    @property
    def terminal(self) -> BgCube:
        return self.cubes[-1]

    def manhattan_distance_anchor(self) -> int:
        return self.cubes[0].position.get_manhattan_distance(self.cubes[-1].position)

    def volume(self) -> int:
        return len(self.cubes)

    def occupies(self, position: Coordinates):
        return position in self.occupied

    def is_closed(self):
        return len(self.cubes) == len(self.pipes)

    def __copy(self):
        cp = Ring(anchor=self.cubes[0])
        cp.cubes.extend(self.cubes[1:])
        cp.pipes.extend(self.pipes)
        cp.occupied.update(self.occupied)
        return cp

    def close(self, pipe: EdgeType) -> Ring:
        closed = self.__copy()
        closed.pipes.append(pipe)
        return closed

    def extend(self, cube: BgCube, pipe: EdgeType) -> Ring:
        extended = self.__copy()
        extended.cubes.append(cube)
        extended.pipes.append(pipe)
        extended.occupied.add(cube.position)
        return extended

    def append(self, cube: BgCube):
        self.cubes.append(cube)
        self.occupied.add(cube.position)

    def copy(self):
        cp = Ring(self.cubes[0])
        cp.cubes.extend(self.cubes[1:].copy())
        cp.occupied = set(self.occupied.copy())
        return cp

    def __lt__(self, other):
        return self.volume().__lt__(other.volume())

    def __str__(self):
        content = f"{self.cubes[0]}"

        for index in range(1, len(self.cubes)):
            cube, pipe = self.cubes[index], self.pipes[index - 1]
            content += f" --{repr(pipe)}-- {str(cube)}"

        if self.is_closed():
            content += f" --{repr(self.pipes[-1])}-- {self.anchor}"

        return content

    def __repr__(self):
        return str(self)
