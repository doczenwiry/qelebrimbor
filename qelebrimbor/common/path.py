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

import numpy as np
from functools import total_ordering

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import SpacetimeHelper

import logging
console = logging.getLogger(__name__)


type Length = int


@total_ordering
class Path:
    def __init__(self, start: BgCube):
        self.start = start
        self.final = start
        self.extra_cubes: list[BgCube] = []
        self.pipes_types: list[EdgeType] = []
        self.occupied = { start.position }

    def overhead(self):
        return self.manhattan_length() - self.start.position.get_manhattan_distance(self.final.position)

    @staticmethod
    def minimal_volume_possible(start: BgCube, final: BgCube, count_endpoints: bool = True) -> int:
        return Path.minimal_length_possible(start, final) + (+1 if count_endpoints else -1)

    @staticmethod
    def minimal_length_possible(source: BgCube, target: BgCube) -> Length:
        return source.position.get_manhattan_distance(target.position) + Path.minimal_excess_possible(source, target)

    @staticmethod
    def minimal_excess_possible(start: BgCube, final: BgCube) -> Length:
        if start.kind in [CubeKind.OOO , CubeKind.YYY] or final.kind in [CubeKind.OOO , CubeKind.YYY]:
            return 0

        overhead = 0

        start_reach = start.kind.get_reach()
        final_reach = final.kind.get_reach()

        manhattan = start.position.get_manhattan_distance(final.position)
        relative = final.position - start.position

        if np.sign( start_reach.dot(relative) ) == -1:
            start_reach *= -1

        if np.sign( final_reach.dot(relative) ) == -1:
            final_reach *= -1

        # TODO: work out the formalisation and justification of the cases for all the overhead values.
        if start.kind == final.kind:
            if manhattan >= 1 and relative == start_reach.scale(manhattan):
                overhead += 2

            if manhattan >= 2:
                if any(relative == start_reach.scale(manhattan - 1) + step
                       for step in SpacetimeHelper.get_step_constellation(start_reach)
                ):
                    overhead += 2

            if manhattan >= 3:
                if any(relative == start_reach.scale(manhattan-2) + step + start_reach.cross(step)
                       for step in SpacetimeHelper.get_step_constellation(start_reach)
                ):
                    overhead += 2
        else:
            differences = start.kind.differences(final.kind)
            overhead += sum(2 for i in range(3) if differences[i] == 1 and relative[i] == 0)
            if manhattan == 1:
                if start.kind.get_type() == final.kind.get_type():
                    overhead += 2
                elif start_reach == final_reach != relative:
                    overhead += 2
            elif manhattan == 2 and start.kind.get_type() != final.kind.get_type():
                if start_reach == final_reach != relative and start_reach.dot(relative) == 0 and relative.dot(relative) != 4:
                    overhead += 2

        return overhead

    def manhattan_length(self):
        return len(self.extra_cubes) + 1

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
        # if len(self.extra_cubes) != 0:
        content += f" -> {self.extra_cubes}"
        content += f" -> {self.final}"
        return content

    def __repr__(self):
        return str(self)