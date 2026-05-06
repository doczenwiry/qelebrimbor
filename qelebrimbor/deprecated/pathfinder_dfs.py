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

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class PathFinderDFS:
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
        unrelaxed: list[tuple[Length, Path]] = []

        initial = Path(source)
        unrelaxed.append( (0, initial) )
        minimal_paths[ (source.kind, source.position) ] = initial

        manhattan_distance = source.position.get_manhattan_distance(target.position)

        maximal_distance = manhattan_distance + maximal_excess

        points_discovered = 0

        minimal_number_of_cubes = nt if nt % 2 == 0 else nt + 1
        maximal_volume = max(source.position.get_manhattan_distance(target.position), minimal_number_of_cubes) + maximal_excess + 2

        console.info(f"Searching for paths from {source} to {target} [{zx_nodes}].")
        console.info(f"> Maximal volume allowed : {maximal_volume}")

        while len(unrelaxed) > 0 and optimum is None:
            heapq.heapify(unrelaxed)
            length, current_path = heapq.heappop(unrelaxed)
            terminal = current_path.final

            minimal_length_possible: int = ManhattanCalculator.minimal_manhattan_length(terminal, target)
            manhattan_length_projected: int = current_path.manhattan_length() + minimal_length_possible

            # Branch-and-bound; discard current path if it cannot improve on our current knowledge
            if optimum and optimum.manhattan_length() <= manhattan_length_projected:
                continue

            length = current_path.manhattan_length()
            remaining_distance = terminal.position.get_manhattan_distance(target.position)
            console.debug(f"Current [{length}/{remaining_distance}]: {terminal} [mlp-rest:{minimal_length_possible},mlp-total:{manhattan_length_projected},path:{current_path}]")

            if BlockGraphHelper.connectable(terminal, target, EdgeType.IDENTITY) and len(current_path.extra_cubes) >= nt:
                # TODO: Fix EdgeType.IDENTITY to final_type_restriction
                console.debug(f"> Connectable to {target} : {BlockGraphHelper.connectable(terminal, target, EdgeType.IDENTITY)}")
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

                extended_path = current_path.extend(cube = neighbor, pipe_type = EdgeType.IDENTITY)
                extended_distance = extended_path.manhattan_length()

                if neighbor_point not in minimal_paths or extended_distance < minimal_paths[neighbor_point].manhattan_length():
                    # Update the unrelaxed queue
                    unrelaxed = [ vertex for vertex in unrelaxed if vertex[1].final != neighbor ]
                    # Compute the minimal manhattan length required to connect neighbor to target (heuristic).
                    minimum_manhattan_length = ManhattanCalculator.minimal_manhattan_length(neighbor, target)
                    unrelaxed.append( (minimum_manhattan_length, extended_path) )

                    points_discovered += 1

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

        return optimum