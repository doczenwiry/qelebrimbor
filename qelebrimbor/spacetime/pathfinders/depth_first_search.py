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

from qelebrimbor.core.attributes_bg import CubeKind
from qelebrimbor.core.attributes_zx import NodeType, EdgeType
from qelebrimbor.core.components import BgCube

from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.calculator import ManhattanCalculator
from qelebrimbor.core.path import Length, Path
from qelebrimbor.spacetime.fabric import SpacetimeFabric
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class PathfinderDFS:
    def __init__(self,
            graph: VolumetricZxGraph = None,
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
        self.__branch_and_bound = branch_and_bound
        self.__tracing = tracing

    @staticmethod
    def heuristic(source: BgCube, target: BgCube):
        return ManhattanCalculator.minimal_manhattan_length(source, target)

    def find_optimum(
            self, source: BgCube, target: BgCube, edge_type: EdgeType, maximal_excess: int | None = None
    ) -> Path | None:
        """
        Search for a path connecting cubes source and target.
        :param source: The cube from which to start.
        :param target: The cube towards which to go.
        :param edge_type: The type that the Path found ought to have.
        :param maximal_excess: The maximum number of additional cubes permitted on top of the Manhattan Length.
        N.B. maximal_excess = None forces the PathfinderDFS to search until it finds a Path.
        :return: A Path or None if no path was found.
        """
        optimum: Path | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()

        unrelaxed: list[tuple[Length, Path]] = []

        initial = Path(start = source)
        minimal_paths[ (source.kind, source.position) ] = initial

        heapq.heappush(unrelaxed, (PathfinderDFS.heuristic(source, target), initial))

        if maximal_excess:
            maximal_length = source.position.get_manhattan_distance(target.position) + maximal_excess
            extra = f"[max length={maximal_length}]"
        else:
            maximal_length = None
            extra = ""

        console.info(f"Searching for path from {source} to {target} {extra}")

        interconnect = { NodeType.X, NodeType.Z }

        pruning_performed = 0

        tracer: SpacetimeTracer | None = SpacetimeTracer(reporting = self.__tracing) if self.__tracing else None
        if tracer:
            tracer.add_node(source)

        while len(unrelaxed) > 0 and (self.__branch_and_bound or optimum is None):
            # Restore the heap invariant
            heapq.heapify(unrelaxed)
            vertex: tuple[Length, Path] = heapq.heappop(unrelaxed)

            manhattan_length_remaining, current_path = vertex
            next_pipe_type = edge_type if current_path.manhattan_length() == 0 else EdgeType.IDENTITY
            terminal = current_path.final

            # Discard the current_path if it is longer than what was requested.
            if maximal_length and maximal_length < current_path.manhattan_length():
                continue

            # Branch-and-bound
            if self.__branch_and_bound and optimum:
                manhattan_length_projected = current_path.manhattan_length() + manhattan_length_remaining
                if optimum.manhattan_length() <= manhattan_length_projected:
                    pruning_performed += 1
                    continue

            console.debug(f"{'>' * (current_path.manhattan_length()+1)} Current : {current_path}")

            if BlockGraphHelper.connectable(terminal, target, next_pipe_type) and not self.__graph.has_bg_pipe(terminal, target):
                console.debug(f"> Connectable to {target} : {BlockGraphHelper.connectable(terminal, target, next_pipe_type)}")
                completed_path = current_path.extend(cube = target, pipe_type = next_pipe_type)

                # Tracing exploration
                if tracer:
                    tracer.add_node(target)
                    tracer.add_edge(terminal, target)

                # Update the optimum only if it improves our current knowledge
                if optimum is None or completed_path.manhattan_length() < optimum.manhattan_length():
                    optimum = completed_path

            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal, node_types = interconnect):
                neighbor_point = (neighbor.kind, neighbor.position)

                # Ignore neighbor if it introduces a loop
                if current_path.occupies(neighbor.position):
                    continue

                # Ignore neighbor if its position is already occupied in spacetime
                if self.__spacetime.is_occupied(neighbor.position):
                    continue

                # Tracing exploration
                if tracer:
                    tracer.add_node(neighbor)
                    tracer.add_edge(terminal, neighbor)

                extended_path = current_path.extend(cube = neighbor, pipe_type = EdgeType.IDENTITY)
                extended_distance = extended_path.manhattan_length()

                if neighbor_point not in minimal_paths or extended_distance < minimal_paths[neighbor_point].manhattan_length():
                    # Filtering out the neighbor from unrelaxed
                    unrelaxed = [ vertex for vertex in unrelaxed if vertex[1].final != neighbor ]

                    # Compute the minimal manhattan length required to connect neighbor to target (HEURISTIC).
                    unrelaxed.append( (PathfinderDFS.heuristic(neighbor, target), extended_path) )

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

        # Tracing exploration
        if tracer:
            tracer.report(cubes_to_label= [source, target])

        if self.__branch_and_bound:
            console.info(f"Number of pruning performed : {pruning_performed}")

        return optimum