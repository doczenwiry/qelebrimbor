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
from typing import Iterable

from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.bg.strand import Strand
from qelebrimbor.core.colorless.path import ColorlessPath
from qelebrimbor.core.components import BgCube, ZxEdge, ZxNode
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
    def all_painted(
        colorless: ColorlessPath, chain: ZxChain, starts: Iterable[BgCube], finals: Iterable[BgCube]
    ) -> list[Strand]:
        strands: list[Strand] = []
        # TODO: produce all painted Strand to be able to choose preferred ones; where the number of unfusable nodes
        #       - is equal to the length of the chain ?

        # TODO: this should be matching edges to pipes instead of nodes to cubes !!
        # TODO: for every pipe, decide whether to paint it with the current edge (and cube with target) or an identity.
        # TODO: if current edge is an identity, single case.

        # Identify the start and final cube corresponding to the endpoints of the chain.
        start = next((s for s in starts if s.position == colorless.start), None)
        final = next((f for f in finals if f.position == colorless.final), None)

        console.debug(f"Attempting to all_paint {colorless} using {chain}")
        console.debug(f"> Start: {start}, Final: {final}, Extras: {colorless.extras_count}")

        if start is None or final is None:
            return strands

        # The ColorlessPath is not compatible if its first step doesn't lie in the reach of the start cube.
        if not start.reach.contains(Step(colorless.outgoing - start.position)):
            return strands

        # The ColorlessPath is not compatible if its last step doesn't lie in the reach of the final cube.
        if not final.reach.contains(Step(colorless.incoming - final.position)):
            return strands

        node_restrictions: list[ZxNode] = list(chain.unrealised)
        edge_restrictions: list[ZxEdge] = list(chain.edges)
        colorless_cubes = list(colorless.extra_cubes)
        colorless_steps: list[Coordinates] = list(colorless.steps)

        unrelaxed: list[tuple[Strand, int, int]] = list()

        heapq.heappush(unrelaxed, (Strand(start=start), 0, 0))

        partial: Strand
        node_count: int
        edge_count: int
        current_step: Step
        current_node: ZxNode | None
        while len(unrelaxed) > 0:
            heapq.heapify(unrelaxed)
            partial, node_count, edge_count = heapq.heappop(unrelaxed)
            current_step = Step(colorless_steps[partial.length])
            console.debug(f"Current strand [E:{edge_count},L:{partial.length},C:{colorless.length}] : {partial}")

            # TODO: check completion of Strand
            if partial.length == colorless.length - 1:
                if node_count < len(node_restrictions) or edge_count < len(edge_restrictions) - 1:
                    continue

                console.debug(f"Candidate for closure [{partial.length}] : {partial}")

                if edge_count < len(edge_restrictions):
                    current_pipe = edge_restrictions[edge_count].type
                else:
                    current_pipe = EdgeType.IDENTITY

                # Add completed Strand if it is acceptable
                if CubeKind.compatible(partial.final.kind, final.kind, current_step, current_pipe):
                    completed = partial.extend(final, current_pipe)
                    if completed.number_of_unfusable_nodes() == chain.length + 1:
                        strands.append(completed)
                continue

            position, reaches = colorless_cubes[partial.length]
            current_step = Step(colorless_steps[partial.length])

            # TODO: derive the kinds rather than filter them.
            for kind in CubeKind:
                if not CubeKind.compatible(partial.final.kind, kind, current_step, EdgeType.IDENTITY):
                    continue

                if kind.reach not in reaches:
                    continue

                # Construct a colored cube and assign it to the current node if the kind is suitable for the type.
                cube = BgCube(kind=kind, position=position)

                console.debug(f"> painted_cube : {cube}")
                extended = partial.extend(cube, EdgeType.IDENTITY)
                heapq.heappush(unrelaxed, (extended, node_count, edge_count))

            # Attempt extending by cube matching current_node, if any are unrealised.

            if edge_count < len(edge_restrictions):
                current_pipe = edge_restrictions[edge_count].type
            else:
                current_pipe = EdgeType.IDENTITY
            if current_pipe is not None:
                current_node = node_restrictions[node_count] if node_count < len(node_restrictions) else None

                console.debug(f"> colorless cube : {position} / {reaches}")
                for kind in CubeKind:
                    if not CubeKind.compatible(partial.final.kind, kind, current_step, current_pipe):
                        continue

                    if kind.reach not in reaches:
                        continue

                    if current_node is not None and kind.get_type() != current_node.type:
                        continue

                    cube = BgCube(kind=kind, position=position)
                    if current_node is not None:
                        cube.realised_node = current_node

                    console.debug(f"> painted_cube : {cube}")
                    extended = partial.extend(cube, current_pipe)

                    if current_node is not None:
                        heapq.heappush(unrelaxed, (extended, node_count + 1, edge_count + 1))
                    else:
                        heapq.heappush(unrelaxed, (extended, node_count, edge_count + 1))

                # Handle internal error of logic.
                # if selected is None:
                #     console.error(f"> Failure to paint cube at {position} w/ {reaches}")
                #     raise Exception("No suitable kind found for next colorless cube when painting ColorlessPath.")

                # Construct a colored cube and assign it to the current node if the kind is suitable for the type.
                # cube = BgCube(kind=selected, position=position)
                # if current_node is not None and selected.get_type() == current_node.type:
                #     cube.realised_node = current_node
                #     edge_count += 1
                #
                #     console.debug(f"> painted_cube : {cube}")
                #     extended = strand.extend(cube, pipe_type)
                #     heapq.heappush(unrelaxed, (extended, edge_count))

        return strands

    @staticmethod
    def paint(
        colorless: ColorlessPath, chain: ZxChain, starts: Iterable[BgCube], finals: Iterable[BgCube]
    ) -> Strand | None:
        all_painted = PainterZxChainFusion.all_painted(colorless, chain, starts, finals)
        return all_painted[0] if len(all_painted) > 0 else None

        console.debug(f"Attempting to paint {colorless} using {chain} with {starts}/{finals}")

        # Identify the start and final cube corresponding to the endpoints of the chain.
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
        remaining_nodes = chain.unrealised

        current_node: ZxNode | None = next(remaining_nodes, None)
        preceding_pipe: EdgeType = next(remaining_edges).type

        last_cube: BgCube = start
        colorless_cubes = colorless.extra_cubes
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

                # Prefer a kind that is compatible with the type of the current node.
                if selected is None or (current_node is not None and kind.get_type() == current_node.type):
                    selected = kind
                # Fallback on the last cube kind otherwise
                elif kind == last_cube.kind:
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
