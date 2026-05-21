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
from typing import Iterable

from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.bg.strand import Strand
from qelebrimbor.core.colorless.path import ColorlessPath
from qelebrimbor.core.components import BgCube, ZxNode
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.reach import Reach
from qelebrimbor.core.zx.attributes import EdgeType
from qelebrimbor.core.zx.chain import ZxChain
from qelebrimbor.helpers.spacetime import Step

console = logging.getLogger(__name__)


class PainterZxChainFusion:
    @staticmethod
    def paintable(colorless: ColorlessPath, chain: ZxChain, starts: Iterable[BgCube], finals: Iterable[BgCube]) -> bool:
        return PainterZxChainFusion.paint(colorless, chain, starts, finals) is not None

    @staticmethod
    def paint(
        colorless: ColorlessPath, chain: ZxChain, starts: Iterable[BgCube], finals: Iterable[BgCube]
    ) -> Strand | None:
        console.debug(f"Attempting to paint {colorless} using {chain} with {starts}/{finals}")

        start = next((s for s in starts if s.position == colorless.start), None)
        final = next((f for f in finals if f.position == colorless.final), None)

        if start is None or final is None:
            return None

        # The ColorlessPath is not compatible if its first step doesn't lie in the reach of start.
        if not start.reach.contains(Step(colorless.outgoing - start.position)):
            return None

        # The ColorlessPath is not compatible if its last step doesn't lie in the reach of final.
        if not final.reach.contains(Step(colorless.incoming - final.position)):
            return None

        strand = Strand(start=start)

        remaining_edges = chain.edges
        remaining_nodes = chain.nodes

        current_node: ZxNode | None = next(remaining_nodes, None)
        preceding_pipe: EdgeType = next(remaining_edges).type

        last_cube: BgCube = start
        colorless_cubes = zip(colorless.extras, colorless.as_reaches())
        current_cube: tuple[Coordinates, set[Reach]] | None = next(colorless_cubes, None)

        while current_cube is not None:
            console.debug(f"current_node : {current_node} ? {current_cube}")

            position, reaches = current_cube
            step = Step(position - last_cube.position)
            # Find a kind compatible with the current colorless cube, preferably suitable for the current node type.
            selected: CubeKind | None = None
            for kind in CubeKind:
                if not CubeKind.compatible(last_cube.kind, kind, step, preceding_pipe):
                    continue

                if kind.reach not in reaches:
                    continue

                if selected is None or (current_node is not None and kind.get_type() == current_node.type):
                    selected = kind

            # Handle internal error of logic.
            if selected is None:
                console.error(f"> Failure to paint cube at {position} w/ {reaches}")
                raise Exception("No suitable kind found for next colorless cube when painting ColorlessPath.")

            # Construct a colored cube and assign it to the current node if the kind is suitable for the type.
            cube = BgCube(kind=selected, position=position)
            if current_node is not None and selected.get_type() == current_node.type:
                cube.realised_node = current_node

            console.debug(f"> painted_cube : {cube}")
            strand.append(cube, preceding_pipe)

            if current_node is not None and selected.get_type() == current_node.type:
                current_node = next(remaining_nodes, None)
                preceding_pipe = next(remaining_edges).type
            else:
                preceding_pipe = EdgeType.IDENTITY

            current_cube = next(colorless_cubes, None)
            last_cube = cube

        # The ColorlessPath is not compatible if it doesn't provide enough colorless cubes to be painted with the nodes.
        if current_node is not None:
            return None

        # The ColorlessPath is not compatible if the last cube cannot be connected to the final
        step = Step(final.position - last_cube.position)
        if not CubeKind.compatible(last_cube.kind, final.kind, step, preceding_pipe):
            return None

        strand.append(final, preceding_pipe)

        return strand
