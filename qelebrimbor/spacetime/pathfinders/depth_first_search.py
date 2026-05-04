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

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.components import BgCube, ZxNode

from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.calculator import ManhattanCalculator
from qelebrimbor.common.path import Length, Path
from qelebrimbor.spacetime.tracer import SpacetimeTracer

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class PathfinderDFS:
    def __init__(self,
             graph: VolumetricZxGraph = None, reservations: dict[Coordinates, ZxNode] = None,
             branch_and_bound: bool = False, tracing: bool = False
    ):
        """
        Create a PathfinderDFS to search for optimal paths between cubes in spacetime.
        :param graph: The VolumetricZxGraph serving as the context for the search.
        :param reservations: The reserved positions in spacetime.
        :param branch_and_bound: Controls whether a Branch-and-Bound is performed to improve the first path found.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        Proof of the possibility would be nice. Refutation thereof would be better.
        :param tracing:
        """
        self.__graph = graph if graph else VolumetricZxGraph()
        self.__reservations = reservations if reservations else dict()
        self.__branch_and_bound = branch_and_bound
        self.__tracing = tracing

    def __is_position_reserved(self, requester: ZxNode, target: ZxNode | None, position: Coordinates):
        if position in self.__reservations:
            holder = self.__reservations[position]
            # TODO: allow taking the reservations if it is not critical to the holder ?
            if holder != requester and (not target or holder != target):
                reserved_ports_positions = sum(1 for kv in self.__reservations.items() if kv[1] == holder)
                number_of_ports_required = sum(
                    1 for nb in self.__graph.get_zx_neighbors(holder) if self.__graph.get_zx_edge(holder.id, nb.id).is_realised()
                )
                critical = number_of_ports_required >= reserved_ports_positions
                console.warning(f">> Position {position} reserved by {holder} [critical={critical}]")
                return True

        return False

    def find_optimal_paths(self, source: BgCube, target: BgCube, maximal_excess: int | None = None) -> Path | None:
        """
        Perform path-finding using a Depth-First Search approach.
        :param source: The cube from which to start.
        :param target: The cube towards which to go.
        :param maximal_excess: The maximum number of additional cubes permitted on top of the Manhattan Length.
        :return: A Path or None if no path is found.
        """
        optimum: Path | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()

        unrelaxed: list[tuple[Length, Path]] = []
        minimal_length_achieved: int | None = None

        initial = Path(start = source)
        minimal_paths[ (source.kind, source.position) ] = initial

        vertex: tuple[Length, Path] = (ManhattanCalculator.minimal_manhattan_length(source, target), initial)
        heapq.heappush(unrelaxed, vertex)

        if maximal_excess:
            maximal_distance = source.position.get_manhattan_distance(target.position) + maximal_excess
            extra = f"[max distance={maximal_distance}]"
        else:
            maximal_distance = None
            extra = ""
        console.info(f"Searching for path from {source} to {target} {extra}")

        interconnect = { NodeType.X, NodeType.Z }

        pruning_performed = 0

        tracer: SpacetimeTracer | None = SpacetimeTracer() if self.__tracing else None
        if tracer:
            tracer.add_node(source)

        while len(unrelaxed) != 0 and (self.__branch_and_bound or optimum is None):
            heapq.heapify(unrelaxed)
            vertex: tuple[Length, Path] = heapq.heappop(unrelaxed)
            manhattan_length_remaining, current = vertex

            terminal = current.final

            manhattan_length_projected = current.manhattan_length() + manhattan_length_remaining

            # Branch-and-bound
            if minimal_length_achieved and minimal_length_achieved <= manhattan_length_projected:
                pruning_performed += 1
                continue

            console.debug(f"{'>' * (current.manhattan_length()+1)} Current [mlp:{manhattan_length_projected}] : {current}")

            if BlockGraphHelper.connectable(terminal, target, EdgeType.IDENTITY):
                console.debug(f"> Connectable to {target} : {BlockGraphHelper.connectable(terminal, target, EdgeType.IDENTITY)}")
                completed_path = current.extend(cube = target, pipe_type = EdgeType.IDENTITY)

                # Tracing exploration
                if tracer:
                    tracer.add_node(target)
                    tracer.add_edge(terminal, target)

                if not minimal_length_achieved or completed_path.manhattan_length() < minimal_length_achieved:
                    minimal_length_achieved = completed_path.manhattan_length()
                    optimum = completed_path

            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal, node_types = interconnect):
                neighbor_point = (neighbor.kind, neighbor.position)

                if maximal_distance and maximal_distance < source.position.get_manhattan_distance(neighbor.position):
                    continue

                # Ignore neighbor if it introduces a loop
                if neighbor.position in current.occupied:
                    continue

                if self.__graph:
                    # Ignore neighbor if its position is already occupied
                    if neighbor.position in self.__graph.occupied:
                        continue

                    # Ignore neighbor if it would occupy a position that is reserved
                    if self.__is_position_reserved(source.realised_node, target.realised_node, neighbor.position):
                        continue

                # Tracing exploration
                if tracer:
                    tracer.add_node(neighbor)
                    tracer.add_edge(terminal, neighbor)

                extended_path = current.extend(cube = neighbor, pipe_type = EdgeType.IDENTITY)
                extended_distance = extended_path.manhattan_length()

                if neighbor_point not in minimal_paths or extended_distance < minimal_paths[neighbor_point].manhattan_length():
                    # Filtering out the neighbor from unrelaxed
                    unrelaxed = [ vertex for vertex in unrelaxed if vertex[1].final != neighbor ]

                    # Compute the minimal manhattan length required to connect neighbor to target (heuristic).
                    manhattan_length_remaining: int = ManhattanCalculator.minimal_manhattan_length(neighbor, target)
                    unrelaxed.append( (manhattan_length_remaining, extended_path) )

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

        # Tracing exploration
        if tracer:
            tracer.report(cubes_to_label= [source, target])

        if self.__branch_and_bound:
            console.info(f"Number of pruning performed : {pruning_performed}")

        return optimum