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

from qelebrimbor.core.path import Path
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.attributes_zx import EdgeType
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.colorless_path import ColorlessPath

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
    def heuristic(source: Coordinates, target: Coordinates) -> int:
        return source.get_manhattan_distance(target)

    def find_optimum(
            self, source: BgCube, target: BgCube, edge_type: EdgeType, maximal_excess: int | None = None
    ) -> Path | None:
        """
        Search for a path connecting cubes source and target.
        WARNING: if there exists no colorless path in spacetime between the source and the target; infinite loop.
        :param source: The cube from which to start.
        :param target: The cube towards which to go.
        :param edge_type: The type that the Path found ought to have.
        :param maximal_excess: The maximum number of additional cubes permitted on top of the Manhattan Length.
        N.B. maximal_excess = None forces the PathfinderDFS to search until it finds a Path.
        :return: A Path or None if no path was found.
        """
        optimum: Path | None = None

        unrelaxed: list[tuple[int, ColorlessPath]] = []

        initial = ColorlessPath(start = source.position)

        heapq.heappush(unrelaxed, (PathfinderColorblindDFS.heuristic(source.position, target.position), initial))

        if maximal_excess:
            maximal_length = PathfinderColorblindDFS.heuristic(source.position, target.position) + maximal_excess
            extra = f"[max length={maximal_length}]"
        else:
            maximal_length = None
            extra = ""

        console.info(f"Searching for path from {source} to {target} {extra}")

        tracer: SpacetimeTracer | None = SpacetimeTracer(
            pruning = self.__branch_and_bound, reporting = self.__tracing
        ) if self.__tracing else None
        if tracer:
            tracer.add_node(source.position)

        while len(unrelaxed) > 0 and (self.__branch_and_bound or optimum is None):
            # Restore the heap invariant
            heapq.heapify(unrelaxed)
            remaining, current_path = heapq.heappop(unrelaxed)

            terminal = current_path.final

            # Discard the current_path if it is longer than what was requested.
            if maximal_length and maximal_length < current_path.manhattan_length():
                continue

            # Branch-and-bound
            if self.__branch_and_bound and optimum is not None:
                manhattan_length_projected = current_path.manhattan_length() + remaining
                if optimum.manhattan_length() <= manhattan_length_projected:
                    if tracer:
                        tracer.prune_node(terminal)
                    continue

            console.debug(f"{'>' * (current_path.manhattan_length()+1)} Current : {current_path}")

            if terminal.get_manhattan_distance(target.position) == 1:
                #TODO: check the path is consistent for the kinds of the source and the target.
                completed_path = current_path.extend(target.position)
                console.info(f"Candidate : {completed_path} {completed_path.compatible(source.kind, target.kind)}")
                if completed_path.compatible(source.kind, target.kind):
                    # Tracing exploration
                    if tracer:
                        tracer.add_node(target.position)
                        tracer.add_edge(terminal, target.position)

                    # Update the optimum only if it improves our current knowledge
                    if optimum is None or completed_path.manhattan_length() < optimum.manhattan_length():
                        optimum = completed_path.painted(source, target, edge_type)

            console.debug(f"{'>' * (current_path.manhattan_length()+2)} Constellation : {SpacetimeHelper.get_constellation(terminal)}")
            for adjacent in SpacetimeHelper.get_constellation(terminal):
                # Ignore neighbor if it introduces a loop
                if current_path.visits(adjacent):
                    continue

                # Ignore neighbor if its position is already occupied in spacetime
                if self.__spacetime.occupied(adjacent):
                    continue

                # Ignore neighbor if occluding the position breaks connectivity
                if not self.__connectivity.preserved(source, target, adjacent):
                    continue

                # Tracing exploration
                if tracer:
                    tracer.add_node(adjacent)
                    tracer.add_edge(terminal, adjacent)

                extended = current_path.extend(adjacent)

                # Filtering out the neighbor from unrelaxed
                unrelaxed = [ vertex for vertex in unrelaxed if vertex[1].final != adjacent ]

                # Compute the minimal manhattan length required to connect neighbor to target (HEURISTIC).
                unrelaxed.append((PathfinderColorblindDFS.heuristic(adjacent, target.position), extended))

        console.info(f"Optimum found ? {optimum}")

        # Tracing exploration
        if tracer:
            cubes_to_label = [ source.position ]
            if optimum is not None:
                cubes_to_label.append( target.position )
            tracer.report(cubes_to_label = cubes_to_label)

        return optimum
