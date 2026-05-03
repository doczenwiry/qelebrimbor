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

from collections import deque

from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.components import BgCube, ZxNode

from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.common.path import Path
from qelebrimbor.spacetime.tracer import SpacetimeTracer

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class PlacementFinderBFS:
    @staticmethod
    def __is_position_reserved(graph: VolumetricZxGraph, reservations: dict[Coordinates, ZxNode] | None, requester: ZxNode, target: ZxNode | None, position: Coordinates):
        if reservations is None:
            return False

        if position in reservations:
            holder = reservations[position]
            # TODO: allow taking the reservations if it is not critical to the holder ?
            if holder != requester and (not target or holder != target):
                reserved_ports_positions = sum(1 for kv in reservations.items() if kv[1] == holder)
                number_of_ports_required = sum(
                    1 for nb in graph.get_zx_neighbors(holder) if graph.get_zx_edge(holder.id, nb.id).is_realised()
                )
                critical = number_of_ports_required >= reserved_ports_positions
                console.warning(f">> Position {position} reserved by {holder} [critical={critical}]")
                return True

        return False

    # TODO: consider the type of Edge between source and target (IDENTITY or HADAMARD)
    @staticmethod
    def find_closest_realisation(
            graph: VolumetricZxGraph, source: BgCube, target: ZxNode,
            reservations: dict[Coordinates, ZxNode] = None,
            maximal_distance: int = None,
            tracing: bool = False
    ) -> Path | None:
        optimum: Path | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()
        unrelaxed: deque[Path] = deque()
        initial = Path(start = source)
        unrelaxed.append( initial )
        minimal_paths[ (source.kind, source.position) ] = initial

        number_of_ports_required = graph.get_zx_degree(target.id)
        console.info(f"Searching for placement from {source} to {target}. [ports required:{number_of_ports_required}]")

        target_suitable_kinds: list[CubeKind] = CubeKind.suitable_kinds(target.type)

        pruning_performed = 0
        points_discovered = 0
        points_considered = 0

        # Tracing exploration
        tracer: SpacetimeTracer | None = SpacetimeTracer() if tracing else None
        if tracer:
            tracer.add_node(source)

        while len(unrelaxed) != 0 and optimum is None:
            current_path = unrelaxed.pop()
            terminal = current_path.final

            console.debug(f"Current : {current_path}")

            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")

                if maximal_distance and maximal_distance < source.position.get_manhattan_distance(neighbor.position):
                    continue

                # Ignore neighbor if it introduces a loop
                if neighbor.position in current_path.occupied or neighbor.position in graph.occupied:
                    console.debug(f">> Position occupied : {neighbor.position}")
                    continue

                # Ignore neighbor if it occupies a position that is reserved
                if PlacementFinderBFS.__is_position_reserved(graph, reservations, source.realised_node, None, neighbor.position):
                    continue

                extended_path = current_path.extend(cube = neighbor, pipe_type = EdgeType.IDENTITY)
                console.debug(f"> Extended Path : {extended_path}")

                # If a suitable Cube has been reached for the target, consider it further
                console.debug(f"> Neighbor has kind {neighbor.kind} in {target_suitable_kinds} ?")
                if neighbor.kind in target_suitable_kinds:
                    open_ports = list(filter(
                        lambda pos : pos not in extended_path.occupied and pos not in graph.occupied and (not reservations or pos not in reservations),
                        SpacetimeHelper.get_constellation(neighbor.position, neighbor.kind.get_reach())
                    ))
                    number_of_open_ports = len(open_ports)
                    # If the position offers enough open ports, consider it as the optimum
                    console.debug(f"> Open ports found for {neighbor} : {open_ports} [req.{number_of_ports_required}]")
                    if number_of_ports_required <= number_of_open_ports:
                        optimum = extended_path
                        continue

                # Don't attempt to extend if the neighbor is a terminal cube.
                if neighbor.kind in [ CubeKind.OOO , CubeKind.YYY ]:
                    continue

                # Update position of neighbor in unrelaxed as its distance is being updated
                if neighbor not in minimal_paths:
                    unrelaxed.append( extended_path )

                # Tracing exploration
                if tracer:
                    tracer.add_node(neighbor)
                    tracer.add_edge(terminal, neighbor)

                points_discovered += 1

                # Update minimal distance discovered
                minimal_paths[neighbor_point] = extended_path

            points_considered += 1

        console.debug(f"> Number of points considered : {points_considered}")
        console.debug(f"> Number of pruning performed : {pruning_performed}")
        console.debug(f"> Number of points discovered : {points_discovered}")

        # Tracing exploration
        if tracer:
            tracer.draw(cubes = [ source ])

        return optimum