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

import itertools
import logging
from functools import total_ordering
from typing import Iterator

from qelebrimbor.core.common import Port
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.zx.attributes import EdgeType
from qelebrimbor.helpers.blockgraph import BlockGraphHelper

console = logging.getLogger(__name__)


type Length = int


@total_ordering
class Path:
    def __init__(self, start: BgCube):
        self.cubes: list[BgCube] = [start]
        self.pipes: list[EdgeType] = []
        self.occupied: set[Coordinates] = {start.position}

    @property
    def start(self) -> BgCube:
        return self.cubes[0]

    @property
    def final(self) -> BgCube:
        return self.cubes[-1]

    @property
    def outgoing(self) -> Port:
        return self.final.position if self.length == 0 else self.cubes[-2].position

    @property
    def incoming(self) -> Port:
        return self.start.position if self.length == 0 else self.cubes[1].position

    @property
    def extras(self) -> Iterator[BgCube]:
        return itertools.islice(self.cubes, 1, self.length)

    def excess(self):
        return self.length - self.distance

    @property
    def length(self) -> int:
        return len(self.cubes) - 1

    @property
    def distance(self) -> int:
        return self.start.position.get_manhattan_distance(self.final.position)

    def occupies(self, position: Coordinates):
        return position in self.occupied

    def append(self, cube: BgCube, pipe: EdgeType):
        if not BlockGraphHelper.connectable(self.final, cube, pipe):
            raise Exception(
                f"Attempting to extend Path with incompatible pipe/cube [path:{self} -{pipe.name[0]}- {cube}]."
            )

        self.cubes.append(cube)
        self.pipes.append(pipe)
        self.occupied.add(cube.position)

    def extend(self, cube: BgCube, pipe_type: EdgeType):
        extended = Path(self.start)
        extended.cubes.extend(self.cubes[1:])
        extended.pipes.extend(self.pipes)
        extended.occupied.update(self.occupied)

        extended.append(cube, pipe_type)

        return extended

    def __lt__(self, other):
        return self.length.__lt__(other.length)

    def __str__(self):
        content = f"{self.start} "
        for index in range(1, len(self.cubes)):
            content += f" --{repr(self.pipes[index - 1])}-- {self.cubes[index]}"
        return content

    def __repr__(self):
        return str(self)
