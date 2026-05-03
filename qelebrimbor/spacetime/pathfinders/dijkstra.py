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
import networkx as nx
import matplotlib.pyplot as plt

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeId, NodeType, EdgeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.deprecated.path import Path, Distance


import logging
console = logging.getLogger(__name__)

class PathfinderDijkstra:
    @staticmethod
    def __retrieve_closest_unrelaxed(
            unrelaxed: dict[Distance, list[BgCube]]
    ) -> tuple[BgCube, Distance]:
        pass

    @staticmethod
    def __add_into_unrelaxed(cube: BgCube, distance: Distance, unrelaxed: dict[Distance, list[BgCube]]):
        if distance in unrelaxed:
            unrelaxed[distance].append(cube)
        else:
            unrelaxed[distance] = [ cube ]

    @staticmethod
    def __remove_from_unrelaxed(cube: BgCube, distance: Distance, unrelaxed: dict[Distance, list[BgCube]]):
        unrelaxed[distance].remove(cube)
        if len(unrelaxed[distance]) == 0:
            unrelaxed.pop(distance)

    @staticmethod
    def __extract_closest_point(unrelaxed: dict[Distance, list[BgCube]]) -> BgCube:
        min_distance = min(unrelaxed.keys())
        current: BgCube = unrelaxed[min_distance][0]
        PathfinderDijkstra.__remove_from_unrelaxed(current, min_distance, unrelaxed)
        return current

    @staticmethod
    def find_optimal_paths(source: BgCube, target: BgCube, tracing: bool = False) -> Path | None:
        optimum: Path | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()

        # TODO: switch to a more efficient data-structure (i.e. fibo-heap)
        unrelaxed: dict[Distance, list[BgCube]] = defaultdict(list)
        PathfinderDijkstra.__add_into_unrelaxed(source, 0, unrelaxed)
        minimal_paths[ (source.kind, source.position) ] = Path(source = source, target = source)

        manhattan_distance = source.position.get_manhattan_distance(target.position)
        console.info(f"Searching for path from {source} to {target} [distance={manhattan_distance}].")
        console.info(f"> Least bound relaxed req. : {8 * 6 ** (manhattan_distance - 1)}")
        console.info(f"> Upper bound relaxed req. : {8 * 6 ** manhattan_distance}")

        interconnect = { NodeType.X, NodeType.Z }

        points_reached = 0
        points_relaxed = 0

        # Tracing exploration
        nodes : dict[BgCube, NodeId] = dict()
        labels: dict[NodeId, str] = dict()
        trace: nx.Graph = nx.Graph()
        if tracing:
            trace.add_node( 0 )
            labels[len(nodes)] = str(source)
            nodes[source] = 0

        while len(unrelaxed) != 0 and optimum is None:
            current: BgCube = PathfinderDijkstra.__extract_closest_point(unrelaxed)
            current_point = (current.kind, current.position)
            current_path: Path = minimal_paths[ current_point ]
            console.debug(f"Current : {current} [{current_path}]")

            if BlockGraphHelper.connectable(current, target, EdgeType.IDENTITY):
                console.info(f">> Current {current} be connected to target {target} [{current_path}]")
                completed_path = current_path.copy()
                if current != source:
                    completed_path.append( current )
                completed_path.target = target

                # Tracing exploration
                if tracing:
                    labels[len(nodes)] = str(target)
                    nodes[target] = len(nodes)
                    trace.add_node( nodes[target] )
                    trace.add_edge( nodes[current], nodes[target] )

                optimum = completed_path

            # Relaxation step on every neighbor
            for neighbor in BlockGraphHelper.get_candidate_constellation(current, node_types = interconnect):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")
                # Ignore neighbor if it introduces a loop
                if neighbor.position in current_path.occupied:
                    continue

                extended_path = current_path.copy()
                if current != source:
                    extended_path.append( current )
                extended_path.target = neighbor
                extended_distance = extended_path.manhattan_length()
                console.debug(f">> {current_path}   =Relax=   {extended_path}")

                if neighbor not in minimal_paths or extended_distance < minimal_paths[neighbor_point].manhattan_length():
                    # Update position of neighbor in unrelaxed as its distance is being updated
                    if neighbor in minimal_paths:
                        PathfinderDijkstra.__remove_from_unrelaxed(
                            neighbor, minimal_paths[neighbor_point].manhattan_length(), unrelaxed
                        )
                    PathfinderDijkstra.__add_into_unrelaxed(neighbor, extended_distance, unrelaxed)

                    # Tracing exploration
                    if tracing:
                        # labels[len(nodes)] = str(neighbor)
                        nodes[neighbor] = len(nodes)
                        trace.add_node( nodes[neighbor] )
                        trace.add_edge( nodes[current], nodes[neighbor] )

                    points_reached += 1

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

            points_relaxed += 1

        n = manhattan_distance + 1
        points_present = int(n * (2 * n**2 + 1) / 3)
        console.info(f"Number of points present : {points_present}")
        console.info(f"Number of points relaxed : {points_relaxed}")
        console.info(f"Number of points reached : {points_reached}")

        if tracing:
            layout = nx.drawing.layout.bfs_layout(trace, start = 0)
            nx.draw(trace, layout, node_size = 1)
            nx.draw_networkx_labels(trace, layout, labels)
            console.info(f"> Number of nodes : {len(trace.nodes)}")
            plt.show()

        return optimum