from collections import defaultdict

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.components import BgCube

from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.pathfinders.path import Path, Distance

import logging
console = logging.getLogger(__name__)

# TODO: clarify that this is a Depth-First-Search with a Brand-and-Bound feature.
class PathfinderDFS:
    @staticmethod
    def __retrieve_closest_unrelaxed(
            unrelaxed: dict[Distance, list[BgCube]]
    ) -> tuple[BgCube, Distance]:
        pass

    @staticmethod
    def __add_into_unrelaxed(cube: BgCube, distance: Distance, unrelaxed: dict[Distance, list[BgCube]]):
        if distance not in unrelaxed:
            unrelaxed[distance] = []
        unrelaxed[distance].append(cube)

    @staticmethod
    def __remove_from_unrelaxed(cube: BgCube, distance: Distance, unrelaxed: dict[Distance, list[BgCube]]):
        unrelaxed[distance].remove(cube)
        if len(unrelaxed[distance]) == 0:
            unrelaxed.pop(distance)

    @staticmethod
    def __extract_closest_point(unrelaxed: dict[Distance, list[BgCube]]) -> BgCube:
        min_distance = min(unrelaxed.keys())
        current: BgCube = unrelaxed[min_distance][0]
        PathfinderDFS.__remove_from_unrelaxed(current, min_distance, unrelaxed)
        return current

    @staticmethod
    def find_optimal_paths(source: BgCube, target: BgCube, bnb: bool = False) -> Path | None:
        """
        Perform path-finding using a Depth-First Search approach.
        :param source: The cube from which to start.
        :param target: The cube towards which to go.
        :param bnb: Controls whether a Branch-and-Bound refinement ought to be performed after finding the first path.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        :return:
        """
        optimum: Path | None = None

        minimal_length_achieved: int | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()
        unrelaxed: dict[Distance, list[BgCube]] = defaultdict(list)
        PathfinderDFS.__add_into_unrelaxed(source, 0, unrelaxed)
        minimal_paths[ (source.kind, source.position) ] = Path(source = source, target = source)

        manhattan_distance = source.position.get_manhattan_distance(target.position)
        console.info(f"Searching for path from {source} to {target} [distance={manhattan_distance}].")

        interconnect = { NodeType.X, NodeType.Z }

        points_discovered = 0
        points_considered = 0

        while len(unrelaxed) != 0 and (bnb or optimum is None):
            current: BgCube = PathfinderDFS.__extract_closest_point(unrelaxed)
            current_point = (current.kind, current.position)
            current_path = minimal_paths[current_point]
            terminal = current_path.target

            minimal_length_possible: int = Path.minimal_length_possible(terminal, target)
            manhattan_length_projected: int = current_path.manhattan_length() + minimal_length_possible

            # Branch-and-bound
            if minimal_length_achieved and minimal_length_achieved <= manhattan_length_projected:
                continue

            console.debug(f"Current : {current} [mlp-rest:{minimal_length_possible},mlp-total:{manhattan_length_projected},path:{current_path}]")

            if BlockGraphHelper.connectable(current, target, EdgeType.IDENTITY):
                console.debug(f"> Connectable to {target} : {BlockGraphHelper.connectable(current, target, EdgeType.IDENTITY)}")
                completed_path = current_path.copy()
                if current != source:
                    completed_path.append(current)
                completed_path.target = target
                if not minimal_length_achieved or completed_path.manhattan_length() < minimal_length_achieved:
                    minimal_length_achieved = completed_path.manhattan_length()
                    optimum = completed_path

            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal, node_types = interconnect):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")

                # Ignore neighbor if it introduces a loop
                if neighbor.position in current_path.occupied:
                    continue

                extended_path = current_path.copy()
                if current != source:
                    extended_path.append(current)
                extended_path.target = neighbor
                extended_distance = extended_path.manhattan_length()

                if neighbor not in minimal_paths or extended_distance < minimal_paths[neighbor_point].manhattan_length():
                    # Update position of neighbor in unrelaxed as its distance is being updated
                    if neighbor in minimal_paths:
                        PathfinderDFS.__remove_from_unrelaxed(
                            neighbor, minimal_paths[neighbor_point].manhattan_length(), unrelaxed
                        )
                    PathfinderDFS.__add_into_unrelaxed(neighbor, Path.minimal_length_possible(neighbor, target), unrelaxed)

                    points_discovered += 1

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

            points_considered += 1

        points_octahedron = int(manhattan_distance * (2 * manhattan_distance**2 + 1) / 3)
        console.info(f"> Number of octahedron points : {points_octahedron}")
        console.info(f"> Number of points considered : {points_considered}")
        console.info(f"> Number of points discovered : {points_discovered}")

        return optimum