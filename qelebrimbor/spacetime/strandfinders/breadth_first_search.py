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
from qelebrimbor.core.bg.strand import Strand
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType, NodeType
from qelebrimbor.core.zx.chain import ZxChain
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker
from qelebrimbor.spacetime.connectivity.default import DefaultConnectivityTracker
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

console = logging.getLogger(__name__)


class StrandfinderBFS:
    def __init__(
        self,
        graph: VolumetricZxGraph | None = None,
        connectivity: ConnectivityTracker | None = None,
        branch_and_bound: bool = False,
        tracing: SpacetimeTracingReport | None = None,
    ):
        """
        Create a PathfinderDFS to search for optimal paths between cubes in spacetime.
        :param graph: The VolumetricZxGraph serving as the context for the search.
        :param branch_and_bound: Controls whether a Branch-and-Bound is performed to improve the first path found.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        Proof of the possibility would be nice. Refutation thereof would be better.
        :param tracing: Controls whether a tracing/reporting of all vertices explored is performed.
        """
        self.__graph = graph or VolumetricZxGraph()
        self.__connectivity = connectivity or DefaultConnectivityTracker()
        self.__branch_and_bound = branch_and_bound
        self.__tracing = tracing

    def find_optimum(self, goal: ZxChain, maximal_excess: int | None = None) -> Strand | None:
        optimum: Strand | None = None
        unrelaxed: list[Strand] = []
        minimal_paths: dict[tuple[CubeKind, Coordinates], Strand] = dict()

        start = goal.source.realising_cube
        final = goal.target.realising_cube

        nodes = list(goal.nodes)
        edges = list(goal.edges)

        node_types = list(map(lambda node: node.color, nodes))
        edge_types = list(map(lambda edge: edge.color, edges))

        if any(nt == NodeType.O or nt == NodeType.Y for nt in node_types):
            raise Exception("Node restrictions cannot contain NodeType.O or NodeType.Y.")

        if len(edge_types) != len(node_types) + 1:
            raise Exception("A chain must have <n> node restriction and <n+1> edge restrictions.")

        node_type_nr = len(node_types)
        edge_type_nr = len(edge_types)

        if maximal_excess:
            maximal_length = start.position.get_manhattan_distance(final.position) + maximal_excess
            extra = f"max length={maximal_length}/"
        else:
            maximal_length = None
            extra = ""

        tracer: SpacetimeTracer[BgCube] | None = (
            SpacetimeTracer(pruning=self.__branch_and_bound, reporting=self.__tracing) if self.__tracing else None
        )
        if tracer:
            tracer.add_node(start, label=str(start))

        initial = Strand(start=start)
        minimal_paths[(start.kind, start.position)] = initial

        heapq.heappush(unrelaxed, initial)

        console.info(f"Searching for chain from {start} to {final} [{extra}{node_types}/{edge_types}]")

        while len(unrelaxed) > 0 and (self.__branch_and_bound or optimum is None):
            # Restore the heap invariant
            heapq.heapify(unrelaxed)
            current: Strand = heapq.heappop(unrelaxed)
            terminal = current.final

            if maximal_length and maximal_length < current.length:
                continue

            console.debug(f"Current [{terminal}] : {current}")

            # Check whether the goal has been accomplished
            if current.length >= node_type_nr:
                final_pipe_type = edge_types[-1] if edge_types else EdgeType.IDENTITY
                if BlockGraphHelper.connectable(terminal, final, final_pipe_type):
                    completed_path = current.extend(cube=final, pipe=final_pipe_type)
                    console.debug(f"> Completed path : {completed_path}")

                    # Tracing exploration
                    if tracer:
                        tracer.add_node(final, label=str(final))
                        tracer.add_edge(terminal, final)

                    # Update the optimum only if it improves our current knowledge
                    if optimum is None or completed_path.length < optimum.length:
                        optimum = completed_path

            if current.length < node_type_nr:
                node_type_required = {node_types[current.length]}
            else:
                node_type_required = {NodeType.X, NodeType.Z}
            if current.length < edge_type_nr:
                next_pipe_type = edge_types[current.length]
            else:
                next_pipe_type = EdgeType.IDENTITY
            console.debug(f"> Restriction on node/edge : {node_type_required} / {next_pipe_type}")

            for neighbor in BlockGraphHelper.get_candidate_constellation(
                terminal, node_types=node_type_required, pipe_type=next_pipe_type
            ):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")

                # Ignore neighbor if it introduces a loop
                if current.occupies(neighbor.position):
                    continue

                # Ignore neighbor if the position is already occupied in spacetime
                if self.__graph.spacetime.occupied(neighbor.position):
                    continue

                # Ignore neighbor if the position is already reserved in spacetime
                if self.__connectivity and not self.__connectivity.preserved(start, final, neighbor.position):
                    continue

                if current.length < node_type_nr:
                    neighbor.realised_node = nodes[current.length]
                extended = current.extend(cube=neighbor, pipe=next_pipe_type)

                # Tracing exploration
                if tracer:
                    tracer.add_node(neighbor)
                    tracer.add_edge(terminal, neighbor)

                if neighbor_point not in minimal_paths or extended.length < minimal_paths[neighbor_point].length:
                    # Filtering out the neighbor from unrelaxed
                    unrelaxed = [vertex for vertex in unrelaxed if vertex.final != neighbor]
                    # Compute the minimal manhattan length required to connect neighbor to target (heuristic).
                    unrelaxed.append(extended)

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended

        console.info(f"Optimum strand found : {optimum}")

        # Tracing exploration
        if tracer:
            tracer.report()

        return optimum
