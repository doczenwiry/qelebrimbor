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

from qelebrimbor.core.bg.ring import Ring
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.zx.attributes import EdgeType, NodeType
from qelebrimbor.core.components import BgCube

from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.calculator import ManhattanCalculator
from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.spacetime.fabric import SpacetimeFabric
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport, SpacetimeTracer
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)


class RingfinderDFS:
    def __init__(self,
            graph: VolumetricZxGraph = None,
            ports_tracker: OpenPortsTracker | None = None,
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
        self.__ports_tracker = ports_tracker if ports_tracker else OpenPortsTracker(self.__graph)
        self.__spacetime = graph.spacetime if graph else SpacetimeFabric()
        self.__branch_and_bound = branch_and_bound
        self.__tracing = tracing

    @staticmethod
    def heuristic(source: BgCube, target: BgCube, node_types: list[NodeType]):
        # TODO: this heuristic is not admissible ...
        # return len(node_types) + ManhattanCalculator.minimal_manhattan_length(source, target)
        # TODO: is this heuristic admissible ?
        return max(len(node_types), ManhattanCalculator.minimal_manhattan_length(source, target))

    def find_optimum(self, goal: ZxCycle, maximal_excess: int = None) -> Ring | None:
        node_restrictions = list(goal.nodes)
        edge_restrictions = list(goal.edges)
        number_of_restrictions = goal.length
        maximal_volume: int | None = goal.length + maximal_excess if maximal_excess is not None else None

        optimum: Ring | None = None
        unrelaxed: list[tuple[int, Ring]] = []

        # Prepare the anchor for the construct
        root = Ring(
            anchor = BgCube(
                kind = CubeKind.suitable_kinds(node_restrictions[0].type)[0],
                position = SpacetimeHelper.ORIGIN
            )
        )
        unrelaxed.append( (RingfinderDFS.heuristic(root.anchor, root.anchor, node_restrictions), root) )

        console.info(f"Searching for ring anchored at {root.anchor} [ringsize={number_of_restrictions}]")
        console.info(f"Node restrictions: {node_restrictions}")
        console.info(f"Edge restrictions: {edge_restrictions}")

        # Initialise a tracer if it is needed
        tracer: SpacetimeTracer[BgCube] | None = SpacetimeTracer(
            pruning = self.__branch_and_bound, reporting = self.__tracing) if self.__tracing else None
        if tracer:
            tracer.add_node(root.anchor, label = str(root.anchor))

        while len(unrelaxed) > 0 and (self.__branch_and_bound or optimum is None):
            heapq.heapify(unrelaxed)
            hv, partial_ring = heapq.heappop(unrelaxed)
            partial_volume = partial_ring.volume()

            console.debug(f"Current [volume={partial_volume}] : {partial_ring}")

            # Branch-and-bound
            if self.__branch_and_bound and optimum:
                heuristic_value: int = RingfinderDFS.heuristic(partial_ring.terminal, partial_ring.anchor, node_restrictions[partial_volume:])
                projected_volume: int = partial_ring.volume() + heuristic_value
                if optimum.volume() <= projected_volume:
                    if tracer:
                        tracer.prune_node(partial_ring.terminal)
                    continue

            # Check whether the ring satisfies the requirements and can be closed.
            distance = partial_ring.anchor.position.get_manhattan_distance(partial_ring.terminal.position)
            if partial_volume >= number_of_restrictions and distance == 1:
                final_pipe_type = edge_restrictions[-1].type if partial_volume == number_of_restrictions else EdgeType.IDENTITY
                console.info(f"Candidate found : {partial_ring} with {final_pipe_type}")
                if BlockGraphHelper.connectable(partial_ring.terminal, partial_ring.anchor, final_pipe_type):
                    ring = partial_ring.close(final_pipe_type)
                    console.debug(f"Completed ring : {ring}")

                    if tracer:
                        tracer.add_edge(partial_ring.terminal, partial_ring.anchor)

                    optimum = ring
                    break

            # Prepare the node/edge type restriction
            realised_nodes = partial_ring.volume()
            if realised_nodes < number_of_restrictions:
                node_type_required = { node_restrictions[realised_nodes].type }
            else:
                node_type_required = { NodeType.X, NodeType.Z }

            if realised_nodes <= number_of_restrictions:
                edge_type_required = edge_restrictions[realised_nodes - 1].type
            else:
                edge_type_required = EdgeType.IDENTITY

            # Prepare the constellation of candidates to be visited
            candidate_constellation = BlockGraphHelper.get_candidate_constellation(
                partial_ring.terminal, node_types= node_type_required, pipe_type = edge_type_required
            )

            for neighbor in candidate_constellation:
                if partial_ring.occupies(neighbor.position):
                    continue

                if self.__spacetime.occupied(neighbor.position):
                    continue

                # Tracing exploration
                if tracer:
                    tracer.add_node(neighbor)
                    tracer.add_edge(partial_ring.terminal, neighbor)

                # Extend the ring with the neighbor
                extended = partial_ring.extend(neighbor, edge_type_required)

                if not maximal_volume or extended.volume() <= maximal_volume:
                    # Update the unrelaxed queue
                    unrelaxed = [ vertex for vertex in unrelaxed if vertex[1].terminal != neighbor ]
                    # Compute the minimal manhattan length required to connect neighbor to target (heuristic).
                    unrelaxed.append(
                        (RingfinderDFS.heuristic(neighbor, root.anchor, node_restrictions[extended.volume():]), extended)
                    )

        console.info(f"Optimal ring found : {optimum}")

        if tracer:
            tracer.report()

        return optimum