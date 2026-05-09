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

from qelebrimbor.core.common import ZxChain
from qelebrimbor.core.path import Path, Length
from qelebrimbor.core.attributes_zx import NodeType, EdgeType
from qelebrimbor.core.attributes_bg import CubeKind
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.components import BgCube

from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.calculator import ManhattanCalculator
from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker
from qelebrimbor.spacetime.fabric import SpacetimeFabric
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)


class SubringfinderDFS:
    def __init__(self,
            graph: VolumetricZxGraph = None,
            connectivity: ConnectivityTracker | None = None,
            branch_and_bound: bool = False,
            tracing: SpacetimeTracingReport | None = None
    ):
        """
        Create a PathfinderDFS to search for optimal paths between cubes in spacetime.
        :param graph: The VolumetricZxGraph serving as the context for the search.
        :param branch_and_bound: Controls whether a Branch-and-Bound is performed to improve the first path found.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        Proof of the possibility would be nice. Refutation thereof would be better.
        :param tracing: Controls whether a tracing/reporting of all vertices explored is performed.
        """
        self.__graph = graph if graph else VolumetricZxGraph()
        self.__spacetime = graph.spacetime if graph else SpacetimeFabric()
        self.__connectivity = connectivity
        self.__branch_and_bound = branch_and_bound
        self.__tracing = tracing

    @staticmethod
    def heuristic(source: BgCube, target: BgCube, node_types: list[NodeType]):
        # Deprecated PathFinderDFS used this:
        # return ManhattanCalculator.minimal_manhattan_chain(source, target, node_types)
        # return ManhattanCalculator.minimal_manhattan_length(source, target)
        # TODO: this heuristic is not admissible ...
        # return len(node_types) + ManhattanCalculator.minimal_manhattan_length(source, target)
        # TODO: is this heuristic admissible ?
        return max(len(node_types), ManhattanCalculator.minimal_manhattan_length(source, target))

    def find_optimum(self, chain: ZxChain, maximal_excess: int = None) -> Path | None:
        optimum: Path | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()
        unrelaxed: list[tuple[Length, Path]] = []

        source, nodes, edges, target = chain
        start = source.realising_cube
        final = target.realising_cube

        node_types = list(map(lambda node: node.type, nodes))
        edge_types = list(map(lambda edge: edge.type, edges))

        if any(nt == NodeType.O or nt == NodeType.Y for nt in node_types):
            raise Exception(f"Node restrictions cannot contain NodeType.O or NodeType.Y.")

        if len(edge_types) != len(node_types) + 1:
            raise Exception(f"A chain must have <n> node restriction and <n+1> edge restrictions.")

        node_type_nr = len(node_types)
        edge_type_nr = len(edge_types)

        if maximal_excess:
            maximal_length = start.position.get_manhattan_distance(final.position) + maximal_excess
            extra = f"max length={maximal_length}/"
        else:
            maximal_length = None
            extra = ""

        tracer: SpacetimeTracer | None = SpacetimeTracer(
            pruning = self.__branch_and_bound, reporting = self.__tracing
        ) if self.__tracing else None
        if tracer:
            tracer.add_node(start)

        initial = Path(start=start)
        minimal_paths[(start.kind, start.position)] = initial

        vertex = (SubringfinderDFS.heuristic(start, final, node_types), initial)
        heapq.heappush(unrelaxed, vertex )

        console.info(f"Searching for chain from {start} to {final} [{extra}{node_types}/{edge_types}]")

        while len(unrelaxed) > 0 and (self.__branch_and_bound or optimum is None):
            # Restore the heap invariant
            heapq.heapify(unrelaxed)
            hv, current_path = heapq.heappop(unrelaxed)
            terminal = current_path.final

            manhattan_length = current_path.manhattan_length()

            if maximal_length and maximal_length < manhattan_length:
                continue

            # Branch-and-bound
            if self.__branch_and_bound and optimum:
                manhattan_length_projected: int = current_path.manhattan_length() + SubringfinderDFS.heuristic(terminal, final, node_types[manhattan_length:])
                if optimum.manhattan_length() <= manhattan_length_projected:
                    if tracer:
                        tracer.prune_node(terminal)
                    continue

            console.debug(f"Current [{terminal}] : {current_path}")

            # Check whether the goal has been accomplished
            if current_path.manhattan_length() > node_type_nr:
                final_pipe_type = edge_types[-1] if edge_types else EdgeType.IDENTITY
                if BlockGraphHelper.connectable(terminal, final, final_pipe_type):
                    completed_path = current_path.extend(cube = final, pipe_type = final_pipe_type)
                    console.debug(f"> Completed path : {completed_path}")

                    # Tracing exploration
                    if tracer:
                        tracer.add_node(final)
                        tracer.add_edge(terminal, final)

                    # Update the optimum only if it improves our current knowledge
                    if optimum is None or completed_path.manhattan_length() < optimum.manhattan_length():
                        optimum = completed_path

            if manhattan_length < node_type_nr:
                node_type_required = { node_types[manhattan_length] }
            else:
                node_type_required = { NodeType.X, NodeType.Z }
            if manhattan_length < edge_type_nr:
                pipe_type_required = edge_types[manhattan_length]
            else:
                pipe_type_required = EdgeType.IDENTITY
            console.debug(f"> Restriction on node/edge : {node_type_required} / {pipe_type_required}")

            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal, node_types = node_type_required, pipe_type = pipe_type_required):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")

                # Ignore neighbor if it introduces a loop
                if current_path.occupies(neighbor.position):
                    continue

                # Ignore neighbor if the position is already occupied in spacetime
                if self.__spacetime.occupied(neighbor.position):
                    continue

                # Ignore neighbor if the position is already reserved in spacetime
                if self.__connectivity and not self.__connectivity.preserved(start, final, neighbor.position):
                    continue

                extended_path = current_path.extend(cube = neighbor, pipe_type = EdgeType.IDENTITY)
                extended_distance = extended_path.manhattan_length()

                # Tracing exploration
                if tracer:
                    tracer.add_node(neighbor)
                    tracer.add_edge(terminal, neighbor)

                if neighbor_point not in minimal_paths or extended_distance < minimal_paths[neighbor_point].manhattan_length():
                    # Filtering out the neighbor from unrelaxed
                    unrelaxed = [ vertex for vertex in unrelaxed if vertex[1].final != neighbor ]
                    # Compute the minimal manhattan length required to connect neighbor to target (heuristic).
                    unrelaxed.append((SubringfinderDFS.heuristic(neighbor, final, node_types[extended_distance:]), extended_path))

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

        # Tracing exploration
        if tracer:
            tracer.report(cubes_to_label= [start, final])

        return optimum