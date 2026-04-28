from collections import defaultdict

from numba.cpython.builtins import min_iterable

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.pathfinders.path import Path

type Distance = int

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
    def find_optimal_paths(source: BgCube, target: BgCube, ecmp: bool = False) -> list[Path]:
        paths: list[Path] = []
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()

        # TODO: switch to a more efficient data-structure (i.e. fibo-heap)
        unrelaxed: dict[Distance, list[BgCube]] = defaultdict(list)
        PathfinderDijkstra.__add_into_unrelaxed(source, 0, unrelaxed)
        minimal_paths[ (source.kind, source.position) ] = Path(source = source, target = source)

        interconnect = { NodeType.X, NodeType.Z }

        while len(unrelaxed) != 0 and (ecmp or len(paths) == 0):
            min_distance = min(unrelaxed.keys())
            current: BgCube = unrelaxed[min_distance][0]
            current_point = (current.kind, current.position)
            PathfinderDijkstra.__remove_from_unrelaxed(current, min_distance, unrelaxed)
            current_path: Path = minimal_paths[ current_point ]
            console.debug(f"Current : {current} [{current_path}]")

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

                if BlockGraphHelper.connectable(neighbor, target, EdgeType.IDENTITY):
                    console.debug(f">> Neighbor {neighbor} can be connected to target {target} [{current_path}]")
                    completed_path = extended_path.copy()
                    completed_path.append( neighbor )
                    completed_path.target = target
                    paths.append( completed_path )

                if neighbor not in minimal_paths or extended_distance < minimal_paths[neighbor_point].manhattan_length():
                    if neighbor.kind not in [CubeKind.OOO, CubeKind.YYY]:
                        # Update position of neighbor in unrelaxed as its distance is being updated
                        if neighbor in minimal_paths:
                            PathfinderDijkstra.__remove_from_unrelaxed(
                                neighbor, minimal_paths[neighbor_point].manhattan_length(), unrelaxed
                            )
                        PathfinderDijkstra.__add_into_unrelaxed(neighbor, extended_distance, unrelaxed)

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

        console.debug(f"Number of points found : {len(minimal_paths.keys())}")
        for kind in CubeKind:
            if kind in [ CubeKind.OOO, CubeKind.YYY ]:
                continue

            if not any( point[0] == kind for point in minimal_paths.keys() ):
                continue

            points = list(filter(lambda p : p[0] == kind, minimal_paths.keys()))
            console.debug(f"> Kind {kind} has {len(points)} points: {points}")

        return paths