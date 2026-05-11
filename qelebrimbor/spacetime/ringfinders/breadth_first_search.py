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

from qelebrimbor.core.components import BgCube
from qelebrimbor.core.zx.attributes import NodeType, EdgeType
from qelebrimbor.core.bg.attributes import CubeKind

from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.core.bg.ring import Ring
from qelebrimbor.spacetime.fabric import SpacetimeFabric
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker
from qelebrimbor.analysis.cycles import ZxCycle, CycleAnalyser

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)


class RingfinderBFS:
    def __init__(self,
            graph: VolumetricZxGraph = None,
            ports_tracker: OpenPortsTracker | None = None,
            tracing: SpacetimeTracingReport | None = None
    ):
        self.__graph = graph if graph else VolumetricZxGraph()
        self.__ports_tracker = ports_tracker if ports_tracker else OpenPortsTracker(self.__graph)
        self.__spacetime = graph.spacetime if graph else SpacetimeFabric()
        self.__tracing = tracing

    def find_optimum(self,
        cycle: ZxCycle,
        maximal_excess: int | None = None
    ) -> Ring | None:
        # Prepare the parameters for the search
        node_restrictions, edge_restrictions = zip(*cycle)
        number_of_restrictions = len(node_restrictions)
        maximal_volume: int | None = len(cycle) + maximal_excess if maximal_excess is not None else None

        optimum: Ring | None = None
        unrelaxed: list[Ring] = []

        # Prepare the anchor for the construct
        root = Ring(
            anchor = BgCube(
                kind = CubeKind.suitable_kinds(node_restrictions[0].type)[0],
                position = SpacetimeHelper.ORIGIN
            )
        )
        unrelaxed.append( root )

        console.info(f"Searching for ring anchored at {root.anchor} [ringsize={number_of_restrictions}]")
        console.info(f"> {str(cycle)}")

        # Initialise a tracer if it is needed
        tracer: SpacetimeTracer[BgCube] | None = SpacetimeTracer(reporting = self.__tracing) if self.__tracing else None
        if tracer:
            tracer.add_node(root.anchor, label = str(root.anchor))

        while len(unrelaxed) > 0 and optimum is None:
            heapq.heapify(unrelaxed)
            partial_ring = heapq.heappop(unrelaxed)
            partial_volume = partial_ring.volume()

            console.debug(f"Current [volume={partial_volume}] : {partial_ring}")

            # Check whether the ring satisfies the requirements and can be closed.
            distance = partial_ring.anchor.position.get_manhattan_distance(partial_ring.terminal.position)
            if partial_volume >= number_of_restrictions and distance == 1:
                final_pipe_type = edge_restrictions[-1].type if partial_volume == number_of_restrictions else EdgeType.IDENTITY
                console.info(f"Candidate found : {partial_ring} loop with {final_pipe_type}")
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
                    unrelaxed = [ vertex for vertex in unrelaxed if vertex.terminal != neighbor ]
                    # Compute the minimal manhattan length required to connect neighbor to target (heuristic).
                    unrelaxed.append(extended)

        console.info(f"Optimal ring found : {optimum}")

        # Tracing exploration
        if tracer:
            tracer.report()

        return optimum