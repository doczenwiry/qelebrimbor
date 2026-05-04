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

from collections import defaultdict

from qelebrimbor.common.path import Path, Length
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.components import BgCube, ZxNode, ZxEdge

from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.calculator import ManhattanCalculator
from qelebrimbor.helpers.spacetime import SpacetimeHelper

import logging as lgr

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

console = lgr.getLogger(__name__)

class PathFinderDFS:
    @staticmethod
    def __retrieve_closest_unrelaxed(
            unrelaxed: dict[Length, list[BgCube]]
    ) -> tuple[BgCube, Length]:
        pass

    @staticmethod
    def __add_into_unrelaxed(cube: BgCube, distance: Length, unrelaxed: dict[Length, list[BgCube]]):
        if distance not in unrelaxed:
            unrelaxed[distance] = []
        unrelaxed[distance].append(cube)

    @staticmethod
    def __remove_from_unrelaxed(cube: BgCube, distance: Length, unrelaxed: dict[Length, list[BgCube]]):
        unrelaxed[distance].remove(cube)
        if len(unrelaxed[distance]) == 0:
            unrelaxed.pop(distance)

    @staticmethod
    def __extract_closest_point(unrelaxed: dict[Length, list[BgCube]]) -> BgCube:
        min_distance = min(unrelaxed.keys())
        current: BgCube = unrelaxed[min_distance][0]
        PathFinderDFS.__remove_from_unrelaxed(current, min_distance, unrelaxed)
        return current

    @staticmethod
    def __is_position_reserved(graph: VolumetricZxGraph, position: Coordinates, source: BgCube, target: BgCube):
        spacetime = graph.spacetime
        if spacetime.is_reserved(position):
            holder = spacetime.holder(position)
            # TODO: allow taking the reservations if it is not critical to the holder ?
            if holder != source and holder != target:
                # reserved_ports_positions = sum(1 for kv in reservations.items() if kv[1] == holder)
                # number_of_ports_required = sum(
                #     1 for nb in graph.get_zx_neighbors(holder.realised_node) if graph.get_zx_edge(holder.realised_node.id, nb.id).is_realised()
                # )
                # critical = number_of_ports_required >= reserved_ports_positions
                console.warning(f">> Position {position} requested is reserved by {holder}")
                return True

        return False

    @staticmethod
    def __has_enough_ports(graph: VolumetricZxGraph, reservations: dict[Coordinates, BgCube] | None, requester: BgCube, node: ZxNode):
        count_required_ports = graph.get_zx_degree(node.id)
        count_available_ports: int = sum(
            1 for pos in SpacetimeHelper.get_constellation(requester.position, requester.kind.get_reach())
            if graph.spacetime.available(pos) and pos not in reservations
        )

        if node.id == 24:
            raise Exception(f"__has_enough_ports({requester.position}) : {count_available_ports} {count_required_ports}")

        return count_available_ports - 1 >= count_required_ports

    @staticmethod
    def find_minimal_paths(
        source: BgCube, target: BgCube,
        zx_nodes: list[ZxNode] | None = None, zx_edges: list[ZxEdge] | None = None,
        graph: VolumetricZxGraph | None = None,
        maximal_excess: int = 6
    ) -> Path | None:
        node_type_restrictions: list[NodeType] = list(map(lambda zxn: zxn.type, zx_nodes)) if zx_nodes else []
        edge_type_restrictions: list[EdgeType] = list(map(lambda zxe: zxe.type, zx_edges)) if zx_edges else []

        console.debug(f"WORKING WITH {node_type_restrictions} {edge_type_restrictions}")

        if any(tr in {NodeType.O, NodeType.Y} for tr in node_type_restrictions):
            raise Exception(f"Path cannot contain cubes of NodeType.O or NodeType.Y.")

        nt = len(node_type_restrictions)
        et = len(edge_type_restrictions)

        optimum: Path | None = None

        minimal_length_achieved: int | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()
        unrelaxed: dict[Length, list[BgCube]] = defaultdict(list)
        PathFinderDFS.__add_into_unrelaxed(source, 0, unrelaxed)
        minimal_paths[ (source.kind, source.position) ] = Path(start = source)

        manhattan_distance = source.position.get_manhattan_distance(target.position)

        maximal_distance = manhattan_distance + maximal_excess

        points_discovered = 0

        minimal_number_of_cubes = nt if nt % 2 == 0 else nt + 1
        maximal_volume = max(source.position.get_manhattan_distance(target.position), minimal_number_of_cubes) + maximal_excess + 2

        console.info(f"Searching for paths from {source} to {target} [{zx_nodes}].")
        console.info(f"> Maximal volume allowed : {maximal_volume}")

        while len(unrelaxed) > 0 and optimum is None:
            current: BgCube = PathFinderDFS.__extract_closest_point(unrelaxed)
            current_point = (current.kind, current.position)
            current_path = minimal_paths[current_point]
            terminal = current_path.final

            minimal_length_possible: int = ManhattanCalculator.minimal_manhattan_length(terminal, target)
            manhattan_length_projected: int = current_path.manhattan_length() + minimal_length_possible

            # # Branch-and-bound
            # if minimal_length_achieved and minimal_length_achieved <= manhattan_length_projected:
            #     pruning_performed += 1
            #     continue

            length = current_path.manhattan_length()
            remaining_distance = current.position.get_manhattan_distance(target.position)
            console.debug(f"Current [{length}/{remaining_distance}]: {current} [mlp-rest:{minimal_length_possible},mlp-total:{manhattan_length_projected},path:{current_path}]")

            if BlockGraphHelper.connectable(current, target, EdgeType.IDENTITY) and len(current_path.extra_cubes) >= nt:
                console.debug(f"> Connectable to {target} : {BlockGraphHelper.connectable(current, target, EdgeType.IDENTITY)}")
                completed_path = current_path.extend(cube = target, pipe_type = EdgeType.IDENTITY)
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
                    continue

                # Ignore neighbor if it introduces a loop
                if neighbor.position in current_path.occupied:
                    continue

                if graph:
                    # Ignore neighbor if the position is already occupied in spacetime
                    if graph.spacetime.is_occupied(neighbor.position):
                        continue

                    # # Ignore neighbor if it would occupy a position that is reserved
                    # if PathFinderDFS.__is_position_reserved(graph, neighbor.position, source, target):
                    #     continue

                    # if not PathFinderDFS.__has_enough_ports(graph, reservations, candidate, zx_nodes[length-1]):
                    #     continue

                extended_path = current_path.extend(cube = neighbor, pipe_type = EdgeType.IDENTITY)
                extended_distance = extended_path.manhattan_length()

                if neighbor not in minimal_paths or extended_distance < minimal_paths[neighbor_point].manhattan_length():
                    # Update position of neighbor in unrelaxed as its distance is being updated
                    if neighbor in minimal_paths:
                        PathFinderDFS.__remove_from_unrelaxed(
                            neighbor, minimal_paths[neighbor_point].manhattan_length(), unrelaxed
                        )
                    PathFinderDFS.__add_into_unrelaxed(neighbor, ManhattanCalculator.minimal_manhattan_length(neighbor, target), unrelaxed)

                    points_discovered += 1

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

        return optimum