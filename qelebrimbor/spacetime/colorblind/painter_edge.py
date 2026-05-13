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
from qelebrimbor.core.bg.path import Path
from qelebrimbor.core.zx.attributes import EdgeType
from qelebrimbor.core.colorless.path import ColorlessPath
from qelebrimbor.core.components import ZxEdge, BgCube
from qelebrimbor.core.metric.color_shufflings import ColorShuffling

from qelebrimbor.helpers.spacetime import SpacetimeHelper, Step

import logging
console = logging.getLogger(__name__)


class PainterZxEdge:
    @staticmethod
    def paintable(colorless: ColorlessPath, edge: ZxEdge) -> bool:
        start: BgCube = edge.source.realising_cube
        final: BgCube = edge.target.realising_cube

        # The ColorlessPath is not compatible if its endpoints' positions don't match those of start and final.
        if colorless.start != start.position or colorless.final != final.position:
            return False

        # The ColorlessPath is not compatible if its first step doesn't lie in the reach of start.
        if not start.reach.contains(Step(colorless.outgoing - start.position)):
            return False

        # The ColorlessPath is not compatible if its last step doesn't lie in the reach of final.
        if not final.reach.contains(Step(colorless.incoming - final.position)):
            return False

        overall: ColorShuffling = reduce(
            ColorShuffling.extend, map(ColorShuffling.convert, colorless.steps), ColorShuffling.identity()
        )

        # If the edge type considered is of type Hadamard, we apply a Hadamard on the ColorShuffling.
        if edge.type == EdgeType.HADAMARD:
            overall = overall.hadamard()

        # The ColorlessPath is compatible only if its overall ColorShuffling matches the colors of the endpoints.
        return overall.compatible(start.kind, final.kind)

    @staticmethod
    def paint(colorless: ColorlessPath, edge: ZxEdge) -> Path:
        """
        Paint a ColorlessPath of successive Coordinates into a Path made of BgCubes with CubeKind and Coordinates.
        The current strategy when dealing with Hadamard edges consists in making the first pipe into a Hadamard pipe.
        :param edge: The edge specifying how to paint the ColorlessPath
        :return:
        """
        start: BgCube = edge.source.realising_cube
        final: BgCube = edge.target.realising_cube

        if not PainterZxEdge.paintable(colorless, edge):
            raise ValueError(f"ColorlessPath provided cannot be painted for edge : {start} -{repr(edge.type)}- {final}")

        path = Path(start)
        last_cube: BgCube = start
        current_pipe_type: EdgeType = edge.type
        for position, reaches in zip(colorless.extras, colorless.as_reaches()):
            step = Step(position - last_cube.position)
            compatible_kinds = filter(
                lambda kind : CubeKind.compatible(last_cube.kind, kind, step, current_pipe_type) and kind.reach in reaches,
                CubeKind
            )

            selected = next(compatible_kinds)
            path.append(cube = BgCube(kind = selected, position = position), pipe = current_pipe_type)

            try:
                extra = f"[selected:{selected},alternative:{next(compatible_kinds)}]"
                console.warning(f"Ambiguity in inference of a CubeKind at {position} was arbitrarily resolved {extra}.")
            except StopIteration as si:
                pass

            last_cube = path.final
            current_pipe_type = EdgeType.IDENTITY

        path.append(final, pipe = current_pipe_type)
        return path