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

from qelebrimbor.core.bg.path import Path
from qelebrimbor.core.components import BgCube, ZxEdge
from qelebrimbor.core.zx.attributes import EdgeType
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.colorless_path import ColorlessPath
from qelebrimbor.helpers.calculator import ManhattanCalculator

from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker
from qelebrimbor.spacetime.connectivity.default import DefaultConnectivityTracker
from qelebrimbor.spacetime.fabric import SpacetimeFabric
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class PathfinderColorblindDFS:
    def __init__(self,
            graph: VolumetricZxGraph = None,
            connectivity: ConnectivityTracker | None = None,
            branch_and_bound: bool = False,
            tracing: SpacetimeTracingReport | None = None
    ):
        """
        Instantiate a PathfinderDFS to search for shortest valid paths between cubes in spacetime.
        :param graph: The VolumetricZxGraph serving as the context for the searches.
        :param branch_and_bound: Controls whether a Branch-and-Bound is performed to improve the first path found.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        Proof of the possibility would be nice. Refutation thereof would be better.
        :param tracing: Controls whether the PathfinderDFS performs tracing of its searches and outputs its plot.
        """
        self.__graph = graph if graph else VolumetricZxGraph()
        self.__spacetime = graph.spacetime if graph else SpacetimeFabric()
        self.__connectivity: ConnectivityTracker = connectivity or DefaultConnectivityTracker()

        self.__branch_and_bound = branch_and_bound
        self.__tracing = tracing

    @staticmethod
    def initial(edge: ZxEdge) -> ColorlessPath:
        return ColorlessPath(start = edge.source.realising_cube.position)

    @staticmethod
    def heuristic(source: Coordinates, target: Coordinates) -> int:
        return source.get_manhattan_distance(target)

    def find_optimum(self, goal: ZxEdge, maximal_excess: int | None = None) -> Path | None:
        """
        Search for a path connecting cubes source and target.
        WARNING: if there exists no colorless path in spacetime between the source and the target; infinite loop.
        :param goal: The edge specifying a path that must be searched for.
        :param maximal_excess: The maximum number of additional cubes permitted on top of the Manhattan Length.
        N.B. maximal_excess = None forces the PathfinderDFS to search until it finds a Path.
        :return: A Path or None if no path was found.
        """
        optimum: Path | None = None
        unrelaxed: list[tuple[int, ColorlessPath]] = []

        start = goal.source.realising_cube
        final = goal.target.realising_cube

        initial = PathfinderColorblindDFS.initial(goal)

        heapq.heappush(unrelaxed, (PathfinderColorblindDFS.heuristic(start.position, final.position), initial))

        if maximal_excess:
            maximal_length = ManhattanCalculator.manhattan_distance(start, final) + maximal_excess
            extra = f"[max length={maximal_length}]"
        else:
            maximal_length = None
            extra = ""

        console.info(f"Searching for path from {start} to {final} {extra}")

        tracer: SpacetimeTracer | None = SpacetimeTracer(
            pruning = self.__branch_and_bound, reporting = self.__tracing
        ) if self.__tracing else None
        if tracer:
            tracer.add_node(start.position, label = str(start.position))

        while len(unrelaxed) > 0 and (self.__branch_and_bound or optimum is None):
            # Restore the heap invariant
            heapq.heapify(unrelaxed)
            remaining: int
            current: ColorlessPath
            remaining, current = heapq.heappop(unrelaxed)

            terminal = current.final

            # Discard the current_path if it is longer than what is acceptable.
            if maximal_length and maximal_length < current.manhattan_length():
                continue

            # Branch-and-bound
            if self.__branch_and_bound and optimum is not None:
                manhattan_length_projected = current.manhattan_length() + remaining
                if optimum.manhattan_length() <= manhattan_length_projected:
                    if tracer:
                        tracer.prune_node(terminal)
                    continue

            console.debug(f"{'>' * (current.manhattan_length()+1)} Current : {current}")

            # Check whether the goal has been reached
            if terminal.get_manhattan_distance(final.position) == 1:
                # Ignore the incoming path if it doesn't line up with a port of the final cube.
                if not SpacetimeHelper.contains(final.kind.get_reach(), final.position - terminal):
                    continue

                completed_path = current.extend(final.position)
                console.info(f"Candidate : {completed_path} {completed_path.compatible(goal)}")
                if completed_path.compatible(goal):
                    # Tracing exploration
                    if tracer:
                        tracer.add_node(final.position, label = str(final.position))
                        tracer.add_edge(terminal, final.position)

                    # Update the optimum only if it improves our current knowledge
                    if optimum is None or completed_path.manhattan_length() < optimum.manhattan_length():
                        optimum = completed_path.painted(goal)

            # Restrict the outgoing paths to lie in the reach of the CubeKind of the start.
            constellation = SpacetimeHelper.get_constellation(
                position = terminal, restriction = start.kind.get_reach() if current.manhattan_length() == 0 else None
            )

            console.debug(f"{'>' * (current.manhattan_length()+2)} : {constellation}")
            for adjacent in constellation:
                # Ignore neighbor if it introduces a loop
                if current.visits(adjacent):
                    continue

                # Ignore neighbor if its position is already occupied in spacetime
                if self.__spacetime.occupied(adjacent):
                    continue

                # Ignore neighbor if occluding the position breaks connectivity
                if not self.__connectivity.preserved(start, final, adjacent):
                    continue

                # Tracing exploration
                if tracer:
                    tracer.add_node(adjacent)
                    tracer.add_edge(terminal, adjacent)

                extended = current.extend(adjacent)

                # Filtering out the neighbor from unrelaxed
                unrelaxed = [ vertex for vertex in unrelaxed if vertex[1].final != adjacent ]

                # Compute the minimal manhattan length required to connect neighbor to target (HEURISTIC).
                unrelaxed.append((PathfinderColorblindDFS.heuristic(adjacent, final.position), extended))

        console.info(f"Optimum found ? {optimum}")

        # Tracing exploration
        if tracer:
            tracer.report()

        return optimum
