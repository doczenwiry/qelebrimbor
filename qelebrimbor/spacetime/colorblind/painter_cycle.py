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
from typing import Iterator

from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.bg.ring import Ring
from qelebrimbor.core.colorless.ring import ColorlessRing
from qelebrimbor.core.components import BgCube, ZxEdge, ZxNode
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.reach import Reach
from qelebrimbor.core.zx.attributes import EdgeType
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.helpers.spacetime import Step

console = logging.getLogger(__name__)


class PainterZxCycle:
    @staticmethod
    def paintable(colorless: ColorlessRing, cycle: ZxCycle) -> bool:
        return PainterZxCycle.paint(colorless, cycle) is not None

    @staticmethod
    # TODO: correct the determination of whether a ColorlessRing is paintable using a given ZxCycle.
    def paint(colorless: ColorlessRing, cycle: ZxCycle) -> Ring | None:
        """
        Paint a ColorlessRing into a Ring of BgCubes with CubeKind and Coordinates based on the ZxNodes of a ZxCycle.
        The current strategy when dealing with Hadamard edges consists in making the earliest pipe into a Hadamard pipe.
        :param colorless: The ColorlessRing to be painted
        :param cycle: The ZxCycle which specifies how to paint the ColorlessRing.
        :return:
        """

        # The ColorlessRing is not paintable if it doesn't provide at least one BgCube per ZxNode
        if colorless.volume < cycle.length:
            return None

        remaining_nodes: Iterator[ZxNode] = cycle.nodes
        remaining_edges: Iterator[ZxEdge] = cycle.edges
        colorless_cubes = zip(colorless.positions, colorless.as_reaches())

        current_node: ZxNode | None = next(remaining_nodes, None)
        current_cube: tuple[Coordinates, set[Reach]] | None = next(colorless_cubes, None)

        if current_node is None or current_cube is None:
            return None

        position, reaches = current_cube
        console.debug(f"current_node : {current_node} ? {current_cube}")
        # TODO: deal with both cases when multiple reaches are available.
        ring = Ring(
            anchor=BgCube(kind=CubeKind.convert(current_node.type, next(iter(reaches)).value), position=position)
        )
        ring.anchor.realised_node = current_node
        console.debug(f"> painted_cube : {ring.anchor}")

        preceding_pipe: EdgeType = next(remaining_edges).type

        last_cube: BgCube = ring.anchor
        current_node = next(remaining_nodes, None)
        current_cube = next(colorless_cubes, None)
        while current_cube is not None:
            console.debug(f"current_node : {current_node} ? {current_cube} [{preceding_pipe}]")
            position, reaches = current_cube
            step = Step(position - last_cube.position)

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
            ring.append(cube, preceding_pipe)

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
        step = Step(ring.anchor.position - last_cube.position)
        if not CubeKind.compatible(last_cube.kind, ring.anchor.kind, step, preceding_pipe):
            return None

        ring = ring.close(preceding_pipe)

        return ring
