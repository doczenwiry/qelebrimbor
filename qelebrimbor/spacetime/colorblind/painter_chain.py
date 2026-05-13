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

from functools import reduce

from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.bg.strand import Strand
from qelebrimbor.core.metric.color_shufflings import ColorShuffling
from qelebrimbor.core.zx.attributes import EdgeType
from qelebrimbor.core.zx.chain import ZxChain
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.colorless.path import ColorlessPath

import logging

from qelebrimbor.helpers.spacetime import SpacetimeHelper, Step

console = logging.getLogger(__name__)


class PainterZxChain:
    @staticmethod
    def paintable(colorless: ColorlessPath, chain: ZxChain) -> bool:
        start: BgCube = chain.source.realising_cube
        final: BgCube = chain.target.realising_cube

        nodes = list(chain.nodes)
        edges = list(chain.edges)

        if colorless.start != start.position or colorless.final != final.position:
            return False

        # The ColorlessPath is not compatible if its first step doesn't lie in the reach of start.
        if not start.reach.contains(Step(colorless.outgoing - start.position)):
            return False

        # The ColorlessPath is not compatible if its last step doesn't lie in the reach of final.
        if not final.reach.contains(Step(colorless.incoming - final.position)):
            return False

        # The ColorlessPath is not paintable if it doesn't provide at least one BgCube per ZxNode
        if colorless.length < len(nodes):
            return False

        try:
            PainterZxChain.paint(colorless, chain)
        except ValueError as ve:
            return False

        return True

    @staticmethod
    # TODO: correct the determination of whether a ColorlessPath is paintable using a given ZxChain.
    def paint(colorless: ColorlessPath, chain: ZxChain) -> Strand:
        """
        Paint a ColorlessPath into a Strand of BgCubes with CubeKind and Coordinates based on the ZxNodes of a Chain.
        The current strategy when dealing with Hadamard edges consists in making the earliest pipe into a Hadamard pipe.
        :param colorless: ColorlessPath
        :param chain: The ZxChain which specifies how to paint this ColorlessPath.
        :return:
        """
        # if not self.paintable(chain):
        #     raise ValueError(f"ColorlessStrand provided cannot be painted with the chain : {chain}")

        start = chain.source.realising_cube
        final = chain.target.realising_cube
        nodes = list(chain.nodes)
        edges = list(chain.edges)

        console.info(f"Attempting to paint ColorlessPath : {colorless}")
        console.info(f"> Using ZxChain : {chain}")

        successive_shuffling = list(map(ColorShuffling.convert, colorless.steps))
        strand = Strand(start = start)

        console.debug(f"> Starting at {start}")

        last_match: int = 0
        last_kind: CubeKind = start.kind
        cube_index: int = 1
        for restriction in range(len(nodes)):
            current_edge_type = edges[restriction].type if cube_index == last_match + 1 else EdgeType.IDENTITY
            current_node_type = nodes[restriction].type

            console.debug(f"> Current link : --{edges[restriction].type}-- {nodes[restriction]}")

            preceding_shuffling = successive_shuffling[cube_index - 1]
            preceding_shuffling = preceding_shuffling.hadamard() if current_edge_type == EdgeType.HADAMARD else preceding_shuffling
            matched: bool = False
            while not matched and cube_index < colorless.length:
                assigned = colorless[cube_index]
                remaining_shuffling = reduce(ColorShuffling.extend, successive_shuffling[cube_index:], ColorShuffling.identity())

                console.debug(f">> Considering cube {cube_index}@{assigned} [{preceding_shuffling}/{remaining_shuffling}]")

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

                strand.append(cube = cube, pipe = current_edge_type)

                last_kind = selected
                preceding_shuffling = preceding_shuffling.extend(successive_shuffling[cube_index - 1])

            if not matched:
                raise ValueError(f"Cannot be painted")

        # TODO: append the last section towards final.
        current_edge_type = edges[-1].type
        preceding_shuffling = successive_shuffling[cube_index - 1]
        preceding_shuffling = preceding_shuffling.hadamard() if current_edge_type == EdgeType.HADAMARD else preceding_shuffling

        while cube_index < colorless.length:
            remaining_shuffling = reduce(ColorShuffling.extend, successive_shuffling[cube_index:], ColorShuffling.identity())

            assigned = colorless[cube_index]
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

            strand.append(cube=cube, pipe = current_edge_type)

            preceding_shuffling = preceding_shuffling.extend(successive_shuffling[cube_index - 1])

        # TODO: investigate the cases where pipe ought to be edges[..].type.
        strand.append(cube = final, pipe = EdgeType.IDENTITY)
        console.info(f"Colored Strand : {strand}")

        return strand