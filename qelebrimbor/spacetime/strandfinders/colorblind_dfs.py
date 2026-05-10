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

from qelebrimbor.core.strand import Strand
from qelebrimbor.core.common import ZxChain
from qelebrimbor.core.attributes_zx import NodeType
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.colorless_strand import ColorlessStrand
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker
from qelebrimbor.spacetime.connectivity.default import DefaultConnectivityTracker
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

import logging
console = logging.getLogger(__name__)

class StrandfinderColorblindDFS:
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
        self.__graph = graph or VolumetricZxGraph()
        self.__connectivity: ConnectivityTracker = connectivity or DefaultConnectivityTracker()

        self.__branch_and_bound = branch_and_bound
        self.__tracing = tracing

    @staticmethod
    def initial(chain: ZxChain) -> ColorlessStrand:
        source, _, _, _ = chain
        return ColorlessStrand(start = source.realising_cube.position)

    @staticmethod
    def heuristic(source: Coordinates, target: Coordinates) -> int:
        return source.get_manhattan_distance(target)

    def find_optimum(self, goal: ZxChain, maximal_excess: int | None = None) -> Strand | None:
        """
        Search for a path connecting cubes source and target.
        WARNING: if there exists no colorless strand in spacetime between the source and the target; infinite loop.
        :param goal: The chain specifying a strand that must be searched for.
        :param maximal_excess: The maximum number of additional cubes permitted on top of the Manhattan Distance.
        N.B. maximal_excess = None forces the PathfinderDFS to search until it finds a Path.
        :return: A Path or None if no path was found.
        """
        # Prepare the parameters for the search
        source, nodes, edges, target = goal
        start = source.realising_cube
        final = target.realising_cube

        node_types = list(map(lambda node: node.type, nodes))
        edge_types = list(map(lambda edge: edge.type, edges))

        if any(nt == NodeType.O or nt == NodeType.Y for nt in node_types):
            raise Exception(f"Node restrictions cannot contain NodeType.O or NodeType.Y.")

        if len(edge_types) != len(node_types) + 1:
            raise Exception(f"A chain must have <n> node restriction and <n+1> edge restrictions.")

        node_type_nr = len(node_types)

        # Maximal length of acceptable paths
        if maximal_excess:
            maximal_length = StrandfinderColorblindDFS.heuristic(start.position, final.position) + maximal_excess
            extra = f"[max length={maximal_length}]"
        else:
            maximal_length = None
            extra = ""

        # Initialize a tracer if tracing has been requested
        tracer: SpacetimeTracer | None = SpacetimeTracer(
            pruning = self.__branch_and_bound, reporting = self.__tracing
        ) if self.__tracing else None
        if tracer:
            tracer.add_node(start.position, label = str(start.position))

        # Main variables of the DFS
        optimum: Strand | None = None
        unrelaxed: list[tuple[int, ColorlessStrand]] = []

        initial = ColorlessStrand(start = start.position)
        heapq.heappush(unrelaxed, (StrandfinderColorblindDFS.heuristic(start.position, final.position), initial))

        console.info(f"Searching for strand for {start} -> {nodes} -> {final} {extra}")

        while len(unrelaxed) > 0 and (self.__branch_and_bound or optimum is None):
            # Restore the heap invariant
            heapq.heapify(unrelaxed)
            hvalue: int
            current: ColorlessStrand
            hvalue, current = heapq.heappop(unrelaxed)

            terminal = current.final

            # Discard the current_path if it is longer than what is acceptable.
            if maximal_length and maximal_length < current.manhattan_length():
                continue

            # Branch-and-bound
            if self.__branch_and_bound and optimum is not None:
                # Compute the project length based on the heuristic
                manhattan_length_projected = current.manhattan_length() + hvalue
                if optimum.manhattan_length() <= manhattan_length_projected:
                    if tracer:
                        tracer.prune_node(terminal)
                    continue

            console.debug(f"{'>' * (current.manhattan_length()+1)} Current : {current}")

            # Check whether the goal has been accomplished
            if terminal.get_manhattan_distance(final.position) == 1 and current.manhattan_length() > node_type_nr:
                candidate: ColorlessStrand = current.extend(final.position)
                console.info(f"Candidate ColorlessStrand : {candidate}")

                if candidate.paintable(goal):
                    # Tracing exploration
                    if tracer:
                        tracer.add_node(final, label = str(final))
                        tracer.add_edge(terminal, final)

                    # Update the optimum only if it improves our current knowledge
                    if optimum is None or candidate.manhattan_length() < optimum.manhattan_length():
                        optimum = candidate.painted(goal)

            console.debug(f"{'>' * (current.manhattan_length()+2)} Constellation : {SpacetimeHelper.get_constellation(terminal)}")
            for adjacent in SpacetimeHelper.get_constellation(terminal):
                # Ignore neighbor if it introduces a loop
                if current.visits(adjacent):
                    continue

                # Ignore neighbor if its position is already occupied in spacetime
                if self.__graph.spacetime.occupied(adjacent):
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
                unrelaxed.append((StrandfinderColorblindDFS.heuristic(adjacent, final.position), extended))

        console.info(f"Optimum found ? {optimum}")

        # Tracing exploration
        if tracer:
            tracer.report()

        return optimum
