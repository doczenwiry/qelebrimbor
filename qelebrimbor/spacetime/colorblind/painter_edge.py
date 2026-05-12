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

from qelebrimbor.helpers.spacetime import SpacetimeHelper

import logging
console = logging.getLogger(__name__)


class PainterZxEdge:
    @staticmethod
    def paintable(path: ColorlessPath, edge: ZxEdge) -> bool:
        start: BgCube = edge.source.realising_cube
        final: BgCube = edge.target.realising_cube

        # The ColorlessPath is not compatible if its endpoints' positions don't match those of start and final.
        if path.start != start.position or path.final != final.position:
            return False

        # The ColorlessPath is not compatible if it doesn't line up with a port in the reach of the CubeKind of start.
        if not SpacetimeHelper.contains(start.kind.get_reach(), path.outgoing_port - start.position):
            return False

        # The ColorlessPath is not compatible if it doesn't line up with a port in the reach of the CubeKind of final.
        if not SpacetimeHelper.contains(final.kind.get_reach(), path.incoming_port - final.position):
            return False

        overall: ColorShuffling = reduce(
            ColorShuffling.extend, map(ColorShuffling.convert, path.steps), ColorShuffling.identity())

        if edge.type == EdgeType.HADAMARD:
            overall = overall.hadamard()

        return overall.compatible(start.kind, final.kind)

    @staticmethod
    def paint(proposal: ColorlessPath, edge: ZxEdge) -> Path:
        """
        Paint a ColorlessPath of successive Coordinates into a Path made of BgCubes with CubeKind and Coordinates.
        The current strategy when dealing with Hadamard edges consists in making the first pipe into a Hadamard pipe.
        :param edge: The edge specifying how to paint the ColorlessPath
        :return:
        """
        start: BgCube = edge.source.realising_cube
        final: BgCube = edge.target.realising_cube

        if not PainterZxEdge.paintable(proposal, edge):
            raise ValueError(f"ColorlessPath provided cannot be painted for edge : {start} -{repr(edge.type)}- {final}")

        successive_shuffling = list(map(ColorShuffling.convert, proposal.steps))

        path = Path(start)
        current: CubeKind = start.kind
        for index in range(1, proposal.length):
            assigned = proposal[index]
            current_pipe_type = edge.type if index == 1 else EdgeType.IDENTITY
            preceding_shuffling = successive_shuffling[index - 1]
            preceding_shuffling = preceding_shuffling.hadamard() if current_pipe_type == EdgeType.HADAMARD else preceding_shuffling

            remaining_shuffling = reduce(ColorShuffling.extend, successive_shuffling[index:], ColorShuffling.identity())
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

        current_pipe_type = edge.type if proposal.length == 2 else EdgeType.IDENTITY
        path = path.extend(final, pipe_type = current_pipe_type)
        return path