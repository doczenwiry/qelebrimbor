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
from typing import Iterator

from qelebrimbor.core.components import BgCube
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.zx.attributes import EdgeType

console = logging.getLogger(__name__)


@total_ordering
class Ring:
    def __init__(self, anchor: BgCube | None = None):
        self.__cubes: list[BgCube] = []
        self.__pipes: list[EdgeType] = []
        self.__occupied: set[Coordinates] = set()

        if anchor is not None:
            self.__cubes.append(anchor)
            self.__occupied.add(anchor.position)

    @property
    def anchor(self) -> BgCube:
        return self.__cubes[0]

    @property
    def terminal(self) -> BgCube:
        return self.__cubes[-1]

    @property
    def last_cube(self) -> BgCube:
        return self.__cubes[-1]

    @property
    def last_pipe(self) -> EdgeType:
        return self.__pipes[-1]

    @property
    def cubes(self) -> Iterator[BgCube]:
        return iter(self.__cubes)

    @property
    def pipes(self) -> Iterator[EdgeType]:
        return iter(self.__pipes)

    def manhattan_distance_anchor(self) -> int:
        return self.__cubes[0].position.get_manhattan_distance(self.__cubes[-1].position)

    def volume(self) -> int:
        return len(self.__cubes)

    def occupies(self, position: Coordinates):
        return position in self.__occupied

    def is_closed(self):
        return len(self.__cubes) == len(self.__pipes)

    def __copy(self):
        cp = Ring(anchor=self.__cubes[0])
        cp.__cubes.extend(self.__cubes[1:])
        cp.__pipes.extend(self.__pipes)
        cp.__occupied.update(self.__occupied)
        return cp

    def close(self, pipe: EdgeType) -> Ring:
        closed = self.__copy()
        closed.__pipes.append(pipe)
        return closed

    def extended(self, cube: BgCube, pipe: EdgeType) -> Ring:
        extended = Ring()
        extended.__cubes.extend(self.__cubes)
        extended.__pipes.extend(self.__pipes)
        extended.__occupied.update(self.__occupied)
        extended.append(cube, pipe)
        return extended

    def extend(self, cube: BgCube, pipe: EdgeType) -> Ring:
        extended = self.__copy()
        extended.__cubes.append(cube)
        extended.__pipes.append(pipe)
        extended.__occupied.add(cube.position)
        return extended

    def append(self, cube: BgCube, pipe: EdgeType) -> None:
        self.__cubes.append(cube)
        self.__pipes.append(pipe)
        self.__occupied.add(cube.position)

    def copy(self):
        cp = Ring(self.__cubes[0])
        cp.__cubes.extend(self.__cubes[1:].copy())
        cp.__occupied = set(self.__occupied.copy())
        return cp

    def __lt__(self, other):
        return self.volume().__lt__(other.volume())

    def __str__(self):
        content = f"{self.__cubes[0]}"

        for index in range(1, len(self.__cubes)):
            cube, pipe = self.__cubes[index], self.__pipes[index - 1]
            content += f" --{repr(pipe)}-- {str(cube)}"

        if self.is_closed():
            content += f" --{repr(self.__pipes[-1])}-- {self.anchor}"

        return content

    def __repr__(self):
        return str(self)
