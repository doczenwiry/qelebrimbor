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
from qelebrimbor.core.bg.path import Length, Path
from qelebrimbor.core.components import BgCube, ZxEdge
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType, NodeType
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.calculator import ManhattanCalculator
from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker
from qelebrimbor.spacetime.connectivity.default import DefaultConnectivityTracker
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

console = logging.getLogger(__name__)


class PathfinderDFS:
    def __init__(
        self,
        graph: VolumetricZxGraph | None = None,
        connectivity: ConnectivityTracker | None = None,
        branch_and_bound: bool = False,
        tracing: SpacetimeTracingReport | None = None,
    ):
        """
        Instantiate a PathfinderDFS to search for shortest valid paths between cubes in spacetime.
        :param graph: The VolumetricZxGraph serving as the context for the searches.
        :param branch_and_bound: Controls whether a Branch-and-Bound is performed to improve the first path found.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        Proof of the possibility would be nice. Refutation thereof would be better.
        :param tracing: Controls whether the PathfinderDFS performs tracing of its searches and outputs its plot.
        """
        self.__graph = graph or VolumetricZxGraph()
        self.__connectivity: ConnectivityTracker = connectivity or DefaultConnectivityTracker()

        self.__branch_and_bound = branch_and_bound
        self.__tracing = tracing

    @staticmethod
    def heuristic(source: BgCube, target: BgCube):
        return ManhattanCalculator.minimal_manhattan_length(source, target)

    __INTERCONNECTING_TYPES = {NodeType.X, NodeType.Z}

    def find_optimum(self, goal: ZxEdge, maximal_excess: int | None = None) -> Path | None:
        """
        Search for a path connecting cubes source and target.
        :param goal: The ZxEdge specifying the path that is to be searched for.
        :param maximal_excess: The maximum number of additional cubes permitted on top of the Manhattan Length.
        N.B. maximal_excess = None forces the PathfinderDFS to search until it finds a Path (e.g. infinite loop).
        :return: A Path or None
        """
        optimum: Path | None = None
        unrelaxed: list[tuple[Length, Path]] = []
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()

        start = goal.source.realising_cube
        final = goal.target.realising_cube

        initial = Path(start=start)
        minimal_paths[(start.kind, start.position)] = initial

        heapq.heappush(unrelaxed, (PathfinderDFS.heuristic(start, final), initial))

        if maximal_excess:
            maximal_length = start.position.get_manhattan_distance(final.position) + maximal_excess
            extra = f"[max length={maximal_length}]"
        else:
            maximal_length = None
            extra = ""

        console.info(f"Searching for {goal.type} path from {start} to {final} {extra}")

        tracer: SpacetimeTracer[BgCube] | None = (
            SpacetimeTracer(pruning=self.__branch_and_bound, reporting=self.__tracing) if self.__tracing else None
        )
        if tracer:
            tracer.add_node(start, label=str(start))

        while len(unrelaxed) > 0 and (self.__branch_and_bound or optimum is None):
            # Restore the heap invariant
            heapq.heapify(unrelaxed)
            remaining: int
            current: Path
            remaining, current = heapq.heappop(unrelaxed)

            next_pipe_type = goal.type if current.length == 0 else EdgeType.IDENTITY
            terminal = current.final

            # Discard the current_path if it is longer than what was requested.
            if maximal_length and maximal_length < current.length:
                continue

            # Branch-and-bound
            if self.__branch_and_bound and optimum:
                manhattan_length_projected = current.length + remaining
                if optimum.length <= manhattan_length_projected:
                    if tracer:
                        tracer.prune_node(terminal)
                    continue

            console.debug(f"{'>' * (current.length + 1)} Current : {current}")

            if BlockGraphHelper.connectable(terminal, final, next_pipe_type) and not self.__graph.has_bg_pipe(
                terminal, final
            ):
                console.debug(
                    f"> Connectable to {final} : {BlockGraphHelper.connectable(terminal, final, next_pipe_type)}"
                )
                completed_path = current.extend(cube=final, pipe_type=next_pipe_type)

                # Tracing exploration
                if tracer:
                    tracer.add_node(final, label=str(final))
                    tracer.add_edge(terminal, final)

                # Update the optimum only if it improves our current knowledge
                if optimum is None or completed_path.length < optimum.length:
                    optimum = completed_path

            constellation = BlockGraphHelper.get_candidate_constellation(
                origin=terminal,
                node_types=PathfinderDFS.__INTERCONNECTING_TYPES,
                pipe_type=next_pipe_type,
            )

            for neighbor in constellation:
                neighbor_point = (neighbor.kind, neighbor.position)

                # Ignore neighbor if it introduces a loop
                if current.occupies(neighbor.position):
                    continue

                # Ignore neighbor if its position is already occupied in spacetime
                if self.__graph.spacetime.occupied(neighbor.position):
                    continue

                # Ignore neighbor if occluding the position breaks connectivity
                if not self.__connectivity.preserved(start, final, neighbor.position):
                    continue

                # Tracing exploration
                if tracer:
                    tracer.add_node(neighbor)
                    tracer.add_edge(terminal, neighbor)

                extended = current.extend(cube=neighbor, pipe_type=next_pipe_type)

                if neighbor_point not in minimal_paths or extended.length < minimal_paths[neighbor_point].length:
                    # Filtering out the neighbor from unrelaxed
                    unrelaxed = [vertex for vertex in unrelaxed if vertex[1].final != neighbor]

                    # Compute the minimal manhattan length required to connect neighbor to target (HEURISTIC).
                    unrelaxed.append((PathfinderDFS.heuristic(neighbor, final), extended))

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended

        console.info(f"Optimum path found : {optimum}")

        # Tracing exploration
        if tracer:
            tracer.report()

        return optimum
