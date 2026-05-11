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

from qelebrimbor.core.bg.strand import Strand
from qelebrimbor.core.zx.chain import ZxChain
from qelebrimbor.core.zx.attributes import EdgeType
from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.metric.color_shufflings import ColorShuffling

import logging

from qelebrimbor.helpers.spacetime import Step, SpacetimeHelper

console = logging.getLogger(__name__)


@total_ordering
#TODO: replaces qelebrimbor.core.metric.colorless_path.py
class ColorlessStrand:
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

    @property
    def length(self):
        return len(self.__positions) - 1

    def visits(self, position: Coordinates):
        return position in self.__occupied

    def extend(self, position: Coordinates):
        if self.final.get_manhattan_distance(position) != 1:
            raise Exception(f"Attempting to extend Path {self} with non-adjacent position {position}.")

        if position in self.__occupied:
            raise Exception(f"Attempting to extend Path {self} with occupied position {position}.")

        cp = ColorlessStrand(self.start)
        cp.__positions.extend(self.__positions[1:])
        cp.__occupied.update(self.__occupied)
        cp.__successive_shuffling.extend(self.__successive_shuffling)

        cp.__positions.append(position)
        cp.__occupied.add(position)
        next_shuffling = ColorShuffling.convert(position - self.final)
        cp.__overall_shuffling = self.__overall_shuffling.extend( next_shuffling )
        cp.__successive_shuffling.append(next_shuffling)

        return cp

    def paintable(self, chain: ZxChain) -> bool:
        start = chain.source.realising_cube
        final = chain.target.realising_cube
        nodes = list(chain.nodes)
        edges = list(chain.edges)

        if start.position != self.__positions[0]:
            raise ValueError(f"ColorlessStrand is not connected to the source of the chain : {chain}")

        if final.position != self.__positions[-1]:
            raise ValueError(f"ColorlessStrand is not connected to the target of the chain : {chain}")

        # The ColorlessPath is not compatible if it doesn't line up with a port in the reach of the CubeKind of start.
        if not SpacetimeHelper.contains(start.kind.get_reach(), self.__positions[1] - start.position):
            return False

        # The ColorlessPath is not compatible if it doesn't line up with a port in the reach of the CubeKind of final.
        if not SpacetimeHelper.contains(final.kind.get_reach(), self.__positions[-2] - final.position):
            return False

        if self.length < len(nodes):
            return False

        try:
            self.painted(chain)
        except ValueError as ve:
            return False

        return True

    def painted(self, chain: ZxChain) -> Strand:
        """
        Paint a ColorlessStrand of successive Coordinates into a Strand made of BgCubes with CubeKind and Coordinates.
        The current strategy when dealing with Hadamard edges consists in making the first pipe into a Hadamard pipe.
        :param chain: The ZxChain which specifies how to paint this ColorlessStrand.
        :return:
        """
        # if not self.paintable(chain):
        #     raise ValueError(f"ColorlessStrand provided cannot be painted with the chain : {chain}")

        start = chain.source.realising_cube
        final = chain.target.realising_cube
        nodes = list(chain.nodes)
        edges = list(chain.edges)

        console.info(f"Attempting to paint ColorlessStrand {self}")
        console.info(f"> Using ZxChain : {chain}")

        strand = Strand(start = start)

        last_match: int = 0
        last_kind: CubeKind = start.kind
        cube_index: int = 1
        for restriction in range(len(nodes)):
            current_edge_type = edges[restriction].type if cube_index == last_match + 1 else EdgeType.IDENTITY
            current_node_type = nodes[restriction].type

            preceding_shuffling = self.__successive_shuffling[cube_index - 1]
            preceding_shuffling = preceding_shuffling.hadamard() if current_edge_type == EdgeType.HADAMARD else preceding_shuffling
            matched: bool = False
            while not matched:
                remaining_shuffling = reduce(ColorShuffling.extend, self.__successive_shuffling[cube_index:], ColorShuffling.identity())

                assigned = self.__positions[cube_index]
                selected: CubeKind | None = None
                for kind in CubeKind:
                    if not preceding_shuffling.compatible(last_kind, kind):
                        continue

                    if not remaining_shuffling.compatible(kind, final.kind):
                        continue

                    if selected is None or kind.get_type() == current_node_type:
                        selected = kind

                if selected is None:
                    console.debug(f"> Failure to paint cube @ {assigned}")
                    raise ValueError(f"No suitable kind found for next cube when painting Strand.")

                cube = BgCube(kind = selected, position = assigned)
                if selected.get_type() == current_node_type:
                    cube.realised_node = nodes[restriction]
                    matched = True
                console.debug(f"> Painted cube @ {assigned} : {cube}")

                cube_index += 1

                strand = strand.extend(cube=cube, pipe_type=current_edge_type)

                last_kind = selected
                preceding_shuffling = preceding_shuffling.extend(self.__successive_shuffling[cube_index - 1])

        # TODO: append the last section towards final.
        current_edge_type = edges[-1].type
        preceding_shuffling = self.__successive_shuffling[cube_index - 1]
        preceding_shuffling = preceding_shuffling.hadamard() if current_edge_type == EdgeType.HADAMARD else preceding_shuffling

        while cube_index < len(self.__positions) - 1:
            remaining_shuffling = reduce(ColorShuffling.extend, self.__successive_shuffling[cube_index:], ColorShuffling.identity())

            assigned = self.__positions[cube_index]
            selected: CubeKind | None = None
            for kind in CubeKind:
                if not preceding_shuffling.compatible(last_kind, kind):
                    continue

                if not remaining_shuffling.compatible(kind, final.kind):
                    continue

                if selected is None:
                    selected = kind
                else:
                    console.warning(f"Ambiguity in CubeKind at {assigned} arbitrarily resolved [selected={selected}, alternative={kind}]")

            if selected is None:
                raise ValueError(f"No suitable kind found for next cube when painting Strand.")

            cube = BgCube(kind=selected, position=assigned)
            cube_index += 1

            strand = strand.extend(cube=cube, pipe_type = current_edge_type)

            preceding_shuffling = preceding_shuffling.extend(self.__successive_shuffling[cube_index - 1])

        strand = strand.extend(cube = final, pipe_type = EdgeType.IDENTITY)
        console.info(f"Colored Strand : {strand}")

        return strand

    def __lt__(self, other):
        return self.length.__lt__(other.length)

    def __str__(self):
        content  = f"{self.start}"
        for index in range(1, len(self.__positions)):
            step = self.__positions[index] - self.__positions[index - 1]
            content += f" -> "
            if index < len(self.__positions) - 1:
                content += f"{Step(step).name}"
            else:
                content += f"{self.__positions[index]}"
        return content