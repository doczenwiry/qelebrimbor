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


import heapq
import logging

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
    def all_painted(colorless: ColorlessRing, cycle: ZxCycle) -> list[Ring]:
        painted: list[Ring] = list()
        # TODO: not all shifts are needed (e.g. YP, XP, YM, YM, XM, YP has only three essentially different ones)
        # for shift in range(colorless.volume):
        #     painted.extend(PainterZxCycle.__all_painted(colorless.rotated(shift), cycle))
        painted.extend(PainterZxCycle.__all_painted(colorless, cycle))
        return painted

    @staticmethod
    def __all_painted(colorless: ColorlessRing, cycle: ZxCycle) -> list[Ring]:
        rings: list[Ring] = list()
        unrelaxed: list[tuple[Ring, int]] = list()

        node_restrictions: list[ZxNode] = list(cycle.nodes)
        edge_restrictions: list[ZxEdge] = list(cycle.edges)
        colorless_cubes = list(zip(colorless.positions, colorless.as_reaches()))
        colorless_steps: list[Step] = colorless.steps

        node_count: int = 0
        current_node: ZxNode | None = node_restrictions[node_count] if node_count < len(node_restrictions) else None

        if current_node is None:
            return rings

        node_count += 1
        current_cube: tuple[Coordinates, set[Reach]] = colorless_cubes[0]

        position, reaches = current_cube
        console.debug(f"current_node : {current_node} ? {current_cube}")
        initial = Ring(
            anchor=BgCube(kind=CubeKind.convert(current_node.type, next(iter(reaches)).value), position=position)
        )
        initial.anchor.realised_node = current_node
        heapq.heappush(unrelaxed, (initial, node_count))

        # TODO: go over all ways to match the nodes of the cycle to the cubes of the colorless ring.
        # At every stage, decide whether to EITHER match the current node/edge with the current cube/pipe
        # OR make the current pipe an IDENTITY with the matching current cube and move on.
        # IF the number of nodes > number of cubes, PRUNE

        while len(unrelaxed) > 0:
            heapq.heapify(unrelaxed)
            partial, node_count = heapq.heappop(unrelaxed)
            current_node = node_restrictions[node_count] if node_count < len(node_restrictions) else None

            console.debug(f"Current [N:{node_count},V:{partial.volume()}] : {partial}")

            if partial.volume() == colorless.volume:
                console.debug(f"Candidate for closure [{node_count}/{len(node_restrictions)}] : {partial}")
                if node_count < len(node_restrictions):
                    continue

                # The ColorlessPath is not compatible if the last cube cannot be connected to the final
                pipe_type = edge_restrictions[-1].type
                step = Step(partial.anchor.position - partial.terminal.position)
                if CubeKind.compatible(partial.terminal.kind, partial.anchor.kind, step, pipe_type):
                    rings.append(partial.close(pipe_type))

                continue

            position, reaches = colorless_cubes[partial.volume()]
            step = colorless_steps[partial.volume() - 1]

            selected: CubeKind | None = None
            for kind in CubeKind:
                if not CubeKind.compatible(partial.terminal.kind, kind, step, EdgeType.IDENTITY):
                    continue

                if kind.reach not in reaches:
                    continue

                if selected is None:
                    selected = kind

            # Handle internal error of logic.
            if selected is None:
                console.error(f"> Failure to paint cube at {position} w/ {reaches}")
                raise Exception("No suitable kind found for next colorless cube when painting ColorlessPath.")

            # Construct a colored cube and assign it to the current node if the kind is suitable for the type.
            cube = BgCube(kind=selected, position=position)

            console.debug(f"> painted_cube : {cube}")
            extended = partial.extend(cube, EdgeType.IDENTITY)
            heapq.heappush(unrelaxed, (extended, node_count))

            if current_node is not None:
                pipe_type = edge_restrictions[node_count - 1].type

                selected = None
                for kind in CubeKind:
                    if not CubeKind.compatible(partial.terminal.kind, kind, step, pipe_type):
                        continue

                    if kind.reach not in reaches:
                        continue

                    if selected is None or kind.get_type() == current_node.type:
                        selected = kind

                # Handle internal error of logic.
                if selected is None:
                    console.error(f"> Failure to paint cube at {position} w/ {reaches}")
                    raise Exception("No suitable kind found for next colorless cube when painting ColorlessPath.")

                # Construct a colored cube and assign it to the current node if the kind is suitable for the type.
                cube = BgCube(kind=selected, position=position)
                if current_node is not None and selected.get_type() == current_node.type:
                    cube.realised_node = current_node
                    node_count += 1

                    console.debug(f"> painted_cube : {cube}")
                    extended = partial.extend(cube, pipe_type)
                    heapq.heappush(unrelaxed, (extended, node_count))

        return rings

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

        # The ColorlessRing must have at least 4 positions.
        if colorless.volume < 4:
            console.debug("A ColorlessRing must have 4 positions.")
            return None

        # The ColorlessRing is not paintable if it doesn't provide at least one BgCube per ZxNode
        if colorless.volume < cycle.length:
            console.debug("A ColorlessRing must offer at least as many positions as there are nodes in the cycle.")
            return None

        node_restrictions: list[ZxNode] = list(cycle.nodes)
        edge_restrictions: list[ZxEdge] = list(cycle.edges)
        colorless_cubes = list(zip(colorless.positions, colorless.as_reaches()))

        node_count: int = 0
        current_node: ZxNode | None = node_restrictions[node_count] if node_count < len(node_restrictions) else None

        if current_node is None:
            return None

        node_count += 1
        current_cube: tuple[Coordinates, set[Reach]] | None = colorless_cubes[0]

        if current_cube is None:
            return None

        position, reaches = current_cube
        console.debug(f"current_node : {current_node} ? {current_cube}")
        # TODO: deal with both cases when multiple reaches are available.
        # TODO: the next(iter(reaches)) is a source of non-determinism. RESOLVE !
        ring = Ring(
            anchor=BgCube(kind=CubeKind.convert(current_node.type, next(iter(reaches)).value), position=position)
        )
        ring.anchor.realised_node = current_node
        console.debug(f"> painted_cube : {ring.anchor}")

        current_node = node_restrictions[node_count] if node_count < len(node_restrictions) else None
        preceding_edge = edge_restrictions[node_count - 1].type
        while ring.volume() < colorless.volume:
            current_cube = colorless_cubes[ring.volume()]
            console.debug(f"current_node : {current_node} ? {current_cube} [{preceding_edge}]")
            console.debug(f"> ring.terminal : {ring.terminal}")
            position, reaches = current_cube
            step = Step(position - ring.terminal.position)

            selected: CubeKind | None = None
            for kind in CubeKind:
                if not CubeKind.compatible(ring.terminal.kind, kind, step, preceding_edge):
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
                node_count += 1

            console.debug(f"> painted_cube : {cube}")
            ring.append(cube, preceding_edge)

            if current_node is not None and selected.get_type() == current_node.type:
                current_node = node_restrictions[node_count] if node_count < len(node_restrictions) else None
                preceding_edge = edge_restrictions[node_count - 1].type
            else:
                preceding_edge = EdgeType.IDENTITY

        # The ColorlessPath is not compatible if it doesn't provide enough colorless cubes to be painted with the nodes.
        if current_node is not None:
            return None

        # The ColorlessPath is not compatible if the last cube cannot be connected to the final
        step = Step(ring.anchor.position - ring.terminal.position)
        if not CubeKind.compatible(ring.terminal.kind, ring.anchor.kind, step, preceding_edge):
            return None

        ring = ring.close(preceding_edge)

        return ring
