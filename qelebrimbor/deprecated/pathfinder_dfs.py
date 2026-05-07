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
from qelebrimbor.spacetime.connectivity.sufficient_ports import OpenPortsTracker
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class PathFinderDFS:
    def __init__(self,
        graph: VolumetricZxGraph | None = None,
        ports_tracker: OpenPortsTracker | None = None,
        branch_and_bound: bool = False,
        tracing: SpacetimeTracingReport | None = None
    ) -> None:
        self.__graph: VolumetricZxGraph = graph or VolumetricZxGraph()
        self.__ports_tracker: OpenPortsTracker = ports_tracker or OpenPortsTracker(self.__graph)
        self.__branch_and_bound = branch_and_bound
        self.__tracing = tracing

    def find_minimal_paths(self,
        source: BgCube, target: BgCube,
        zx_nodes: list[ZxNode] | None = None, zx_edges: list[ZxEdge] | None = None,
        maximal_excess: int = 6
    ) -> Path | None:
        node_type_restrictions: list[NodeType] = list(map(lambda zxn: zxn.type, zx_nodes)) if zx_nodes else []
        edge_type_restrictions: list[EdgeType] = list(map(lambda zxe: zxe.type, zx_edges)) if zx_edges else []
        restrictions = (node_type_restrictions, edge_type_restrictions)

        return self.find_optimum(source, target, restrictions, maximal_excess)

    def find_optimum(self,
        source: BgCube, target: BgCube,
        restrictions: tuple[list[NodeType], list[EdgeType]],
        maximal_excess: int = 6
    ) -> Path | None:
        node_type_restrictions, edge_type_restrictions = restrictions

        if any(tr in {NodeType.O, NodeType.Y} for tr in node_type_restrictions):
            raise Exception(f"Path cannot contain cubes of NodeType.O or NodeType.Y.")

        nt = len(node_type_restrictions)
        et = len(edge_type_restrictions)

        optimum: Path | None = None
        minimal_length_achieved: int | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()
        unrelaxed: list[tuple[Length, Path]] = []

        initial = Path(source)
        unrelaxed.append( (0, initial) )
        minimal_paths[ (source.kind, source.position) ] = initial

        manhattan_distance = source.position.get_manhattan_distance(target.position)

        maximal_distance = manhattan_distance + maximal_excess

        minimal_number_of_cubes = nt if nt % 2 == 0 else nt + 1
        maximal_volume = max(source.position.get_manhattan_distance(target.position), minimal_number_of_cubes) + maximal_excess + 2

        console.info(f"Searching for paths from {source} to {target}")
        console.info(f"> Node restrictions: {node_type_restrictions}")
        console.info(f"> Edge restrictions: {edge_type_restrictions}")
        console.info(f"> Maximal volume allowed : {maximal_volume}")

        # Tracing exploration
        pruning_performed = 0
        tracer: SpacetimeTracer | None = SpacetimeTracer(reporting = self.__tracing) if self.__tracing else None
        if tracer:
            tracer.add_node(source)

        while len(unrelaxed) > 0 and (self.__branch_and_bound or optimum is None):
            heapq.heapify(unrelaxed)
            length, current_path = heapq.heappop(unrelaxed)
            terminal = current_path.final

            minimal_length_possible: int = ManhattanCalculator.minimal_manhattan_length(terminal, target)
            manhattan_length_projected: int = current_path.manhattan_length() + minimal_length_possible

            # Branch-and-bound; discard current path if it cannot improve on our current knowledge
            if self.__branch_and_bound and optimum:
                if optimum.manhattan_length() <= manhattan_length_projected:
                    pruning_performed += 1
                    continue

            length = current_path.manhattan_length()
            remaining_distance = terminal.position.get_manhattan_distance(target.position)
            console.debug(f"Current [{length}/{remaining_distance}]: {terminal} [mlp-rest:{minimal_length_possible},mlp-total:{manhattan_length_projected},path:{current_path}]")

            if BlockGraphHelper.connectable(terminal, target, EdgeType.IDENTITY) and len(current_path.extra_cubes) >= nt:
                # TODO: Fix EdgeType.IDENTITY to final_type_restriction
                console.debug(f"> Connectable to {target} : {BlockGraphHelper.connectable(terminal, target, EdgeType.IDENTITY)}")
                completed_path = current_path.extend(cube = target, pipe_type = EdgeType.IDENTITY)

                # Tracing exploration
                if tracer:
                    tracer.add_node(target)
                    tracer.add_edge(terminal, target)

                if not minimal_length_achieved or completed_path.manhattan_length() < minimal_length_achieved:
                    minimal_length_achieved = completed_path.manhattan_length()
                    optimum = completed_path

            node_type_required = { node_type_restrictions[length] } if length < nt else { NodeType.X, NodeType.Z }
            pipe_type_required =   edge_type_restrictions[length]   if length < et else EdgeType.IDENTITY
            console.debug(f"> Types required : {node_type_required}")
            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal, node_types = node_type_required, pipe_type = pipe_type_required):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")

                if maximal_distance < source.position.get_manhattan_distance(neighbor.position):
                    console.debug(f"Manhattan distance beyond maximal distance: {source} - {neighbor.position}")
                    continue

                # Ignore neighbor if it introduces a loop
                if current_path.occupies(neighbor.position):
                    console.debug(f"Position is occupied by path: {neighbor.position}")
                    continue

                # # Ignore neighbor if the current path has reserved its position
                # if current_path.is_reserved(neighbor.position):
                #     console.debug(f"Position is reserved by path: {neighbor.position}")
                #     continue

                # Ignore neighbor if the position is already occupied in spacetime
                if self.__graph.spacetime.is_occupied(neighbor.position):
                    console.debug(f"Position is occupied: {neighbor.position}")
                    continue

                # Ignore neighbor if the position is already reserved in spacetime
                if self.__graph.spacetime.is_reserved(neighbor.position):
                    console.debug(f"Position is reserved : {neighbor.position}")
                    holder = self.__graph.spacetime.holder(neighbor.position)
                    if self.__ports_tracker.is_critical(holder, neighbor.position):
                        console.debug(f"Reservation is critical : {neighbor.position}")
                        continue
                    # continue

                # # TODO: account for ports reserved by the partial path itself ...
                # if length < nt and node_type_restrictions is not None:
                #     ports_required = graph.get_zx_degree(zx_nodes[length].id) - 1
                #     console.debug(f"ZX-Node {zx_nodes[length]} requires {ports_required} : {neighbor.position} has {graph.spacetime.ports_offered(neighbor.position, neighbor.kind.get_reach())}")
                #     if graph.spacetime.ports_offered(neighbor.position, neighbor.kind.get_reach()) < ports_required:
                #         continue

                console.debug(f"Extending candidate path : {current_path}")

                # Tracing exploration
                if tracer:
                    tracer.add_node(neighbor)
                    tracer.add_edge(terminal, neighbor)

                extended_path = current_path.extend(cube = neighbor, pipe_type = EdgeType.IDENTITY)
                extended_distance = extended_path.manhattan_length()

                if neighbor_point not in minimal_paths or extended_distance < minimal_paths[neighbor_point].manhattan_length():
                    # Update the unrelaxed queue
                    unrelaxed = [ vertex for vertex in unrelaxed if vertex[1].final != neighbor ]
                    # Compute the minimal manhattan length required to connect neighbor to target (heuristic).
                    minimum_manhattan_length = ManhattanCalculator.minimal_manhattan_length(neighbor, target)
                    unrelaxed.append( (minimum_manhattan_length, extended_path) )

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

        # Tracing exploration
        if tracer:
            tracer.report(cubes_to_label= [source, target])

        if self.__branch_and_bound:
            console.info(f"Number of pruning performed : {pruning_performed}")

        return optimum