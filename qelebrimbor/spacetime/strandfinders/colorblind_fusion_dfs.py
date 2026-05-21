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

from qelebrimbor.core.bg.strand import Strand
from qelebrimbor.core.colorless.path import ColorlessPath
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import NodeType
from qelebrimbor.core.zx.chain import ZxChain
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.spacetime.colorblind.painter_chain_fusion import PainterZxChainFusion
from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker
from qelebrimbor.spacetime.connectivity.default import DefaultConnectivityTracker
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

console = logging.getLogger(__name__)


class StrandfinderColorblindFusionDFS:
    def __init__(
        self,
        graph: VolumetricZxGraph | None = None,
        connectivity: ConnectivityTracker | None = None,
        branch_and_bound: bool = False,
        reporting: SpacetimeTracingReport | None = None,
    ):
        """
        Instantiate a PathfinderDFS to search for shortest valid paths between cubes in spacetime.
        :param graph: The VolumetricZxGraph serving as the context for the searches.
        :param branch_and_bound: Controls whether a Branch-and-Bound is performed to improve the first path found.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        Proof of the possibility would be nice. Refutation thereof would be better.
        :param reporting: Controls whether the PathfinderDFS performs tracing of its searches and outputs its plot.
        """
        self.__graph = graph or VolumetricZxGraph()
        self.__connectivity: ConnectivityTracker = connectivity or DefaultConnectivityTracker()

        self.__branch_and_bound = branch_and_bound
        self.__reporting = reporting

    @staticmethod
    def initial(chain: ZxChain) -> ColorlessPath:
        return ColorlessPath(start=chain.source.realising_cube.position)

    @staticmethod
    def heuristic(source: Coordinates, target: Coordinates, node_types: list[NodeType]) -> int:
        # return source.get_manhattan_distance(target)
        return max(len(node_types), source.get_manhattan_distance(target))

    def find_optimum(self, goal: ZxChain, maximal_excess: int | None = None) -> Strand | None:
        """
        Search for a Strand connecting the source and target of a Chain with the intermediate nodes along the way.
        WARNING: if there exists no ColorlessPath in spacetime between the source and the target; infinite loop.
        :param goal: The Chain specifying a Strand that must be searched for.
        :param maximal_excess: The maximum number of additional cubes permitted on top of the Manhattan Distance.
        N.B. maximal_excess = None forces the PathfinderDFS to search until it finds a Path.
        :return: A Path or None if no path was found.
        """
        # Prepare the parameters for the search
        start = goal.source.realising_cube
        finals: Iterable[BgCube] = self.__graph.get_equivalent_bg_cubes(goal.target.realising_cube)

        nodes = list(goal.nodes)
        edges = list(goal.edges)

        node_types = list(map(lambda node: node.type, nodes))
        edge_types = list(map(lambda edge: edge.type, edges))

        if any(nt == NodeType.O or nt == NodeType.Y for nt in node_types):
            raise Exception("Node restrictions cannot contain NodeType.O or NodeType.Y.")

        if len(edge_types) != len(node_types) + 1:
            raise Exception("A chain must have <n> node restriction and <n+1> edge restrictions.")

        node_type_nr = len(node_types)

        # Maximal length of acceptable strands
        closest_cube = min(finals, key=lambda fnl: start.position.get_manhattan_distance(fnl.position))
        maximal_length = (
            max(goal.length, start.position.get_manhattan_distance(closest_cube.position)) + maximal_excess
            if maximal_excess is not None
            else None
        )
        extra = f"[max length={maximal_length}]" if maximal_length is not None else ""

        # Initialize a tracer if tracing has been requested
        tracer: SpacetimeTracer | None = (
            SpacetimeTracer(pruning=self.__branch_and_bound, reporting=self.__reporting) if self.__reporting else None
        )
        if tracer:
            tracer.add_node(start.position, label=str(start.position))

        # Main variables of the DFS
        optimum: Strand | None = None
        unrelaxed: list[tuple[int, ColorlessPath]] = []

        initial = ColorlessPath(start=start.position)
        heapq.heappush(
            unrelaxed,
            (
                StrandfinderColorblindFusionDFS.heuristic(start.position, closest_cube.position, node_types),
                initial,
            ),
        )

        console.info(f"Searching for strand for {start} -> {nodes} -> {closest_cube} {extra}")

        while len(unrelaxed) > 0 and (self.__branch_and_bound or optimum is None):
            # Restore the heap invariant
            heapq.heapify(unrelaxed)
            remaining_distance: int
            current: ColorlessPath
            remaining_distance, current = heapq.heappop(unrelaxed)

            terminal = current.final

            # Discard the current_path if it is longer than what is acceptable.
            if maximal_length and maximal_length < current.length:
                continue

            # Branch-and-bound
            if self.__branch_and_bound and optimum is not None:
                # Compute the project length based on the heuristic
                projected_length = current.length + remaining_distance
                console.debug(f"Pruning {current} ? {optimum.length} <= {current.length} + {remaining_distance} ?")
                if optimum.length <= projected_length:
                    if tracer:
                        tracer.prune_node(terminal)
                    continue

            console.debug(f"{'>' * (current.length + 1)} Current : {current}")

            # Check whether the goal has been accomplished
            if current.length >= node_type_nr:
                console.debug(f"Testing candidate : {current} [{finals}]")
                for final in finals:
                    if terminal.get_manhattan_distance(final.position) != 1:
                        continue

                    # Ignore the incoming path if it doesn't line up with a port of the final cube.
                    if not SpacetimeHelper.contains(final.kind.get_reach(), final.position - terminal):
                        continue

                    candidate: ColorlessPath = current.extend(final.position, ignore_occupied=True)
                    console.debug(f"Candidate ColorlessStrand [final:{final}] : {candidate}")

                    strand = PainterZxChainFusion.paint(candidate, goal, final)
                    console.debug(f"> Paint result : {strand}")

                    if strand is not None:
                        # Tracing exploration
                        if tracer:
                            tracer.add_node(final, label=str(final))
                            tracer.add_edge(terminal, final)

                        # Update the optimum only if it improves our current knowledge
                        if optimum is None or strand.length < optimum.length:
                            console.debug(f">> Replaced optimum [{strand.length}] ! {strand}")
                            optimum = strand
                console.debug(f">> Turned into optimum ? {optimum}")

            # Restrict the outgoing paths to lie in the reach of the CubeKind of the start.
            constellation = SpacetimeHelper.get_constellation(
                position=terminal,
                restriction=start.kind.get_reach() if current.length == 0 else None,
            )

            console.debug(f"{'>' * (current.length + 2)} {terminal} has constellation : {constellation}")

            for adjacent in constellation:
                # Ignore neighbor if it introduces a loop
                if current.visits(adjacent):
                    continue

                # Ignore neighbor if its position is already occupied in spacetime
                if self.__graph.spacetime.occupied(adjacent):
                    continue

                # # Ignore neighbor if occluding the position breaks connectivity
                # if any(not self.__connectivity.preserved(start, final, adjacent) for final in finals):
                #     continue

                # Tracing exploration
                if tracer:
                    tracer.add_node(adjacent)
                    tracer.add_edge(terminal, adjacent)

                extended = current.extend(adjacent)
                console.debug(f"{'>' * (current.length + 2)} {terminal} extended : {extended}")

                # Filtering out the neighbor from unrelaxed
                # unrelaxed = [vertex for vertex in unrelaxed if vertex[1].final != adjacent]

                # Compute the minimal manhattan length required to connect neighbor to target (HEURISTIC).
                closest_cube = min(finals, key=lambda fnl: adjacent.get_manhattan_distance(fnl.position))
                unrelaxed.append(
                    (
                        StrandfinderColorblindFusionDFS.heuristic(
                            adjacent, closest_cube.position, node_types[extended.length :]
                        ),
                        extended,
                    )
                )

        console.info(f"Optimum found : {optimum}")

        # Tracing exploration
        if tracer:
            tracer.report()

        return optimum
