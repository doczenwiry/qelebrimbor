from collections import defaultdict

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.components import BgCube
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
        minimal_paths: dict[BgCube, Path] = dict()

        # TODO: switch to a more efficient data-structure (i.e. fibo-heap)
        unrelaxed: dict[Distance, list[BgCube]] = defaultdict(list)
        PathfinderDijkstra.__add_into_unrelaxed(source, 0, unrelaxed)
        minimal_paths[ source ] = Path(source = source, target = source)

        while len(unrelaxed) != 0 and (ecmp or len(paths) == 0):
            min_distance = min(unrelaxed.keys())
            current: BgCube = unrelaxed[min_distance][0]
            PathfinderDijkstra.__remove_from_unrelaxed(current, min_distance, unrelaxed)
            current_path: Path = minimal_paths[ current ]
            console.debug(f"Current : {current} [{current_path}]")

            # Relaxation step on every neighbor
            for neighbor in BlockGraphHelper.get_candidate_constellation(current):
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

                if target.matches(neighbor):
                    console.debug(f">> Target {target} matches neighbor {neighbor} [{current_path}]")
                    paths.append( extended_path )

                if neighbor not in minimal_paths or extended_distance < minimal_paths[neighbor].manhattan_length():
                    if neighbor.kind not in [CubeKind.OOO, CubeKind.YYY]:
                        # Update position of neighbor in unrelaxed as its distance is being updated
                        if neighbor in minimal_paths:
                            PathfinderDijkstra.__remove_from_unrelaxed(
                                neighbor, minimal_paths[neighbor].manhattan_length(), unrelaxed
                            )
                        PathfinderDijkstra.__add_into_unrelaxed(neighbor, extended_distance, unrelaxed)

                    # Update minimal distance discovered
                    minimal_paths[neighbor] = extended_path

        for cube, path in minimal_paths.items():
            console.debug(f"Cube {cube} : {path.source} -> {path.extras} -> {path.target}")

        return paths