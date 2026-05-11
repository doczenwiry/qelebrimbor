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

from functools import total_ordering, reduce

from qelebrimbor.core.zx.attributes import EdgeType
from qelebrimbor.core.components import BgCube, ZxEdge
from qelebrimbor.core.bg.path import Path
from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.metric.color_shufflings import ColorShuffling

import logging

from qelebrimbor.helpers.spacetime import SpacetimeHelper

console = logging.getLogger(__name__)


@total_ordering
#TODO: replaces qelebrimbor.core.metric.colorless_path.py
class ColorlessPath:
    def __init__(self, start: Coordinates):
        self.__positions: list[Coordinates] = [ start ]
        self.__occupied: set[Coordinates] = { start }
        self.__overall_shuffling: ColorShuffling = ColorShuffling.identity()
        self.__successive_shuffling: list[ColorShuffling] = []

    @property
    def start(self):
        return self.__positions[0]

    @property
    def final(self):
        return self.__positions[-1]

    def manhattan_length(self) -> int:
        return len(self.__positions) - 1

    def visits(self, position: Coordinates):
        return position in self.__occupied

    def extend(self, position: Coordinates):
        if self.final.get_manhattan_distance(position) != 1:
            raise Exception(f"Attempting to extend Path {self} with non-adjacent position {position}.")

        if position in self.__occupied:
            raise Exception(f"Attempting to extend Path {self} with occupied position {position}.")

        cp = ColorlessPath(self.start)
        cp.__positions.extend(self.__positions[1:])
        cp.__occupied.update(self.__occupied)
        cp.__successive_shuffling.extend(self.__successive_shuffling)

        cp.__positions.append(position)
        cp.__occupied.add(position)
        next_shuffling = ColorShuffling.convert(position - self.final)
        cp.__overall_shuffling = self.__overall_shuffling.extend( next_shuffling )
        cp.__successive_shuffling.append(next_shuffling)

        return cp

    def compatible(self, edge: ZxEdge) -> bool:
        start: BgCube = edge.source.realising_cube
        final: BgCube = edge.target.realising_cube

        # The ColorlessPath is not compatible if its endpoints' positions don't match those of start and final.
        if self.start != start.position or self.final != final.position:
            return False

        # The ColorlessPath is not compatible if it doesn't line up with a port in the reach of the CubeKind of start.
        if not SpacetimeHelper.contains(start.kind.get_reach(), self.__positions[1] - start.position):
            return False

        # The ColorlessPath is not compatible if it doesn't line up with a port in the reach of the CubeKind of final.
        if not SpacetimeHelper.contains(final.kind.get_reach(), self.__positions[-2] - final.position):
            return False

        if edge.type == EdgeType.IDENTITY:
            return self.__overall_shuffling.compatible(start.kind, final.kind)
        else:
            return self.__overall_shuffling.hadamard().compatible(start.kind, final.kind)

    def painted(self, edge: ZxEdge) -> Path:
        """
        Paint a ColorlessPath of successive Coordinates into a Path made of BgCubes with CubeKind and Coordinates.
        The current strategy when dealing with Hadamard edges consists in making the first pipe into a Hadamard pipe.
        :param edge: The edge specifying how to paint the ColorlessPath
        :return:
        """
        start: BgCube = edge.source.realising_cube
        final: BgCube = edge.target.realising_cube
        if not self.compatible(edge):
            raise ValueError(f"ColorlessPath provided cannot be painted for edge : {start} -{repr(edge.type)}- {final}")

        path = Path(start)
        current: CubeKind = start.kind
        for index in range(1, len(self.__positions) - 1):
            assigned = self.__positions[index]
            current_pipe_type = edge.type if index == 1 else EdgeType.IDENTITY
            preceding_shuffling = self.__successive_shuffling[index - 1]
            preceding_shuffling = preceding_shuffling.hadamard() if current_pipe_type == EdgeType.HADAMARD else preceding_shuffling

            remaining_shuffling = reduce(ColorShuffling.extend, self.__successive_shuffling[index:], ColorShuffling.identity())
            compatibles = filter(
                lambda kind: preceding_shuffling.compatible(current, kind) and remaining_shuffling.compatible(kind, final.kind),
                CubeKind
            )
            selected = next(compatibles)
            path = path.extend(
                cube = BgCube(kind = selected, position = assigned), pipe_type = current_pipe_type
            )
            current = selected

            try:
                extra = f"[selected:{selected},alternative:{next(compatibles)}]"
                console.warning(f"Ambiguity in inference of a CubeKind at {assigned} was arbitrarily resolved {extra}.")
            except StopIteration as si:
                pass

        current_pipe_type = edge.type if len(self.__positions) == 2 else EdgeType.IDENTITY
        path = path.extend(final, pipe_type = current_pipe_type)
        return path

    def __lt__(self, other):
        return len(self.__positions).__lt__(len(other.__positions))

    def __str__(self):
        return " -> ".join(map(str, self.__positions))