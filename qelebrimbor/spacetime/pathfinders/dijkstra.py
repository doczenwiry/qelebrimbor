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
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.path import Path, Length
from qelebrimbor.spacetime.tracer import SpacetimeTracer
from qelebrimbor.helpers.blockgraph import BlockGraphHelper


import logging
console = logging.getLogger(__name__)

class PathfinderDijkstra:
    @staticmethod
    def __retrieve_closest_unrelaxed(
            unrelaxed: dict[int, list[BgCube]]
    ) -> tuple[BgCube, int]:
        pass

    @staticmethod
    def __add_into_unrelaxed(cube: BgCube, distance: int, unrelaxed: dict[int, list[BgCube]]):
        if distance in unrelaxed:
            unrelaxed[distance].append(cube)
        else:
            unrelaxed[distance] = [ cube ]

    @staticmethod
    def __remove_from_unrelaxed(cube: BgCube, distance: int, unrelaxed: dict[int, list[BgCube]]):
        unrelaxed[distance].remove(cube)
        if len(unrelaxed[distance]) == 0:
            unrelaxed.pop(distance)

    @staticmethod
    def __extract_closest_point(unrelaxed: dict[int, list[BgCube]]) -> BgCube:
        min_distance = min(unrelaxed.keys())
        current: BgCube = unrelaxed[min_distance][0]
        PathfinderDijkstra.__remove_from_unrelaxed(current, min_distance, unrelaxed)
        return current

    @staticmethod
    def find_optimal_paths(source: BgCube, target: BgCube, tracing: bool = False) -> Path | None:
        optimum: Path | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()

        # TODO: switch to a more efficient data-structure (i.e. fibo-heap)
        # unrelaxed: dict[int, list[BgCube]] = defaultdict(list)
        unrelaxed: list[tuple[Length, Path]] = []

        initial = Path(start = source)
        minimal_paths[ (source.kind, source.position) ] = initial

        vertex: tuple[Length, Path] = (initial.manhattan_length(), initial)
        heapq.heappush(unrelaxed, vertex)

        manhattan_distance = source.position.get_manhattan_distance(target.position)
        console.info(f"Searching for path from {source} to {target} [distance={manhattan_distance}].")
        console.info(f"> Least bound relaxed req. : {8 * 6 ** (manhattan_distance - 1)}")
        console.info(f"> Upper bound relaxed req. : {8 * 6 ** manhattan_distance}")

        interconnect = { NodeType.X, NodeType.Z }

        # Tracing exploration
        tracer: SpacetimeTracer | None = SpacetimeTracer() if tracing else None
        if tracer:
            tracer.add_node(source)

        while len(unrelaxed) != 0 and optimum is None:
            heapq.heapify(unrelaxed)
            vertex: tuple[Length, Path] = heapq.heappop(unrelaxed)
            manhattan_length, current_path = vertex
            terminal = current_path.final

            # current: BgCube = PathfinderDijkstra.__extract_closest_point(unrelaxed)
            # current_point = (terminal.kind, terminal.position)
            # current_path: Path = minimal_paths[ current_point ]
            console.debug(f"Current : {current_path}")

            if BlockGraphHelper.connectable(terminal, target, EdgeType.IDENTITY):
                console.info(f">> Terminal {terminal} be connected to target {target} [{current_path}]")
                completed_path = current_path.extend(target, pipe_type = EdgeType.IDENTITY)

                # Tracing exploration
                if tracer:
                    tracer.add_node( target )
                    tracer.add_edge( terminal, target )

                optimum = completed_path

            # Relaxation step on every neighbor
            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal, node_types = interconnect):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")
                # Ignore neighbor if it introduces a loop
                if neighbor.position in current_path.occupied:
                    continue

                extended_path = current_path.extend(neighbor, pipe_type = EdgeType.IDENTITY)
                extended_distance = extended_path.manhattan_length()
                console.debug(f">> {current_path}   =Relax=   {extended_path}")

                if neighbor not in minimal_paths or extended_distance < minimal_paths[neighbor_point].manhattan_length():
                    # Filtering out the neighbor from unrelaxed
                    unrelaxed = [ vertex for vertex in unrelaxed if vertex[1].final != neighbor ]
                    unrelaxed.append( (extended_path.manhattan_length(), extended_path) )

                    # Tracing exploration
                    if tracer:
                        tracer.add_node(neighbor)
                        tracer.add_edge(terminal, neighbor)

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

        # Tracing exploration
        if tracer:
            tracer.report(cubes_to_label = [ source, target ])

        return optimum