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

from qelebrimbor.core.components import BgCube
from qelebrimbor.core.attributes_zx import EdgeType
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper

import logging
console = logging.getLogger(__name__)


type Length = int


@total_ordering
class Path:
    def __init__(self, start: BgCube):
        self.start: BgCube = start
        self.final: BgCube = start
        self.extra_cubes: list[BgCube] = []
        self.pipes_types: list[EdgeType] = []
        self.occupied: set[Coordinates] = { start.position }

    @property
    def start_port(self):
        return self.final.position if len(self.extra_cubes) == 0 else self.extra_cubes[0].position

    @property
    def final_port(self):
        return self.start.position if len(self.extra_cubes) == 0 else self.extra_cubes[-1].position

    def overhead(self):
        return self.manhattan_length() - self.start.position.get_manhattan_distance(self.final.position)

    def manhattan_length(self) -> int:
        return len(self.extra_cubes) + 1 if self.start != self.final else 0

    def occupies(self, position: Coordinates):
        return position in self.occupied

    def extend(self, cube: BgCube, pipe_type: EdgeType):
        if not BlockGraphHelper.connectable(self.final, cube, pipe_type):
            raise Exception(f"Attempting to extend Path with incompatible pipe/cube [path:{self} -{pipe_type.name[0]}- {cube}].")

        console.debug(f"Extending path : {self} -{pipe_type.name[0]}- {cube}")

        extended = Path(self.start)
        extended.extra_cubes.extend(self.extra_cubes)

        if self.start != self.final:
            extended.extra_cubes.append(self.final)

        extended.pipes_types.extend(self.pipes_types)
        extended.pipes_types.append(pipe_type)

        extended.final = cube

        extended.occupied.update(self.occupied)
        extended.occupied.add(cube.position)

        return extended

    def __lt__(self, other):
        return self.manhattan_length().__lt__(other.manhattan_length())

    def __str__(self):
        content = f"{self.start}"
        if self.start == self.final:
            content += " {self-loop}"
        else:
            if len(self.extra_cubes) != 0:
                content += f" -> {self.extra_cubes}"
            content += f" -> {self.final}"
        return content

    def string(self):
        content = f"{self.start} --{repr(self.pipes_types[0])}-- "

        for index in range(len(self.extra_cubes)):
            cube = self.extra_cubes[index]
            pipe = self.pipes_types[index+1]
            content += f"{str(cube)} --{repr(pipe)}-- "

        content += f"{self.final}"

        return content


    def __repr__(self):
        return str(self)