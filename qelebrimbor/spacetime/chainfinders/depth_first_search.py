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

from qelebrimbor.common.path import Path, Length
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.components import BgCube, ZxNode, ZxEdge

from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.calculator import ManhattanCalculator
from qelebrimbor.spacetime.fabric import SpacetimeFabric
from qelebrimbor.spacetime.tracer import SpacetimeTracer

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class ChainfinderDFS:
    def __init__(self, graph: VolumetricZxGraph = None, branch_and_bound: bool = False, tracing: bool = False):
        """
        Create a PathfinderDFS to search for optimal paths between cubes in spacetime.
        :param graph: The VolumetricZxGraph serving as the context for the search.
        :param branch_and_bound: Controls whether a Branch-and-Bound is performed to improve the first path found.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        Proof of the possibility would be nice. Refutation thereof would be better.
        :param tracing:
        """
        self.__graph = graph if graph else VolumetricZxGraph()
        self.__spacetime = graph.spacetime if graph else SpacetimeFabric()
        self.__branch_and_bound = branch_and_bound
        self.__tracing = tracing

    def find_optimum(self,
            source: BgCube, target: BgCube,
            restrictions: list[tuple[NodeType, EdgeType]] | None = None,
            maximal_excess: int = None
    ) -> Path | None:
        chain_restrictions = restrictions if restrictions else []

        if any(tr[0] == NodeType.O or tr[0] == NodeType.Y for tr in chain_restrictions):
            raise Exception(f"Restrictions cannot contain NodeType.O or NodeType.Y.")
        number_of_restrictions = len(chain_restrictions)

        optimum: Path | None = None

        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()

        initial = Path(start=source)
        minimal_paths[(source.kind, source.position)] = initial

        unrelaxed: list[tuple[Length, Path]] = []
        heapq.heappush(
            unrelaxed,
            (ManhattanCalculator.minimal_manhattan_chain(source, target, chain_restrictions), initial)
        )

        maximal_distance = source.position.get_manhattan_distance(target.position) + maximal_excess if maximal_excess else None

        tracer: SpacetimeTracer | None = SpacetimeTracer() if self.__tracing else None
        if tracer:
            tracer.add_node(source)

        console.info(f"Searching for paths from {source} to {target} [restrictions:{chain_restrictions}].")

        while len(unrelaxed) > 0 and (self.__branch_and_bound or optimum is None):
            heapq.heapify(unrelaxed)
            ml, current_path = heapq.heappop(unrelaxed)
            terminal = current_path.final

            manhattan_length = current_path.manhattan_length()

            # Branch-and-bound
            if self.__branch_and_bound and optimum:
                manhattan_length_projected: int = current_path.manhattan_length() + ManhattanCalculator.minimal_manhattan_chain(
                    source = terminal, target = target, restrictions = chain_restrictions[manhattan_length:]
                )
                if optimum.manhattan_length() <= manhattan_length_projected:
                    continue

            console.debug(f"Current [{terminal}] : {current_path}")

            if current_path.manhattan_length() > number_of_restrictions:
                if BlockGraphHelper.connectable(terminal, target, EdgeType.IDENTITY):
                    completed_path = current_path.extend(cube = target, pipe_type = EdgeType.IDENTITY)
                    console.debug(f"> Completed path : {completed_path}")

                    # Tracing exploration
                    if tracer:
                        tracer.add_node(target)
                        tracer.add_edge(terminal, target)

                    # Update the optimum only if it improves our current knowledge
                    if optimum is None or completed_path.manhattan_length() < optimum.manhattan_length():
                        optimum = completed_path

            if manhattan_length < number_of_restrictions:
                node_type_restriction, pipe_type_restriction = chain_restrictions[manhattan_length]
                node_type_required = { node_type_restriction }
                pipe_type_required = pipe_type_restriction
            else:
                node_type_required = { NodeType.X, NodeType.Z }
                pipe_type_required = EdgeType.IDENTITY
            console.debug(f"> Types required : {node_type_required}")
            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal, node_types = node_type_required, pipe_type = pipe_type_required):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")

                if maximal_distance and maximal_distance < source.position.get_manhattan_distance(neighbor.position):
                    continue

                # Ignore neighbor if it introduces a loop
                if current_path.occupies(neighbor.position):
                    continue

                # Ignore neighbor if the position is already occupied in spacetime
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

                    # Compute the minimal manhattan length required to connect neighbor to target (heuristic).
                    manhattan_length_remaining: int = ManhattanCalculator.minimal_manhattan_chain(
                        source = neighbor, target = target,
                        restrictions = chain_restrictions[extended_distance:],
                    )
                    unrelaxed.append( (manhattan_length_remaining, extended_path) )

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

        # Tracing exploration
        if tracer:
            tracer.report(cubes_to_label= [source, target])

        return optimum