import logging as lgr

from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.components import BgCube

console = lgr.getLogger(__name__)

from typing import Iterable
from queue import PriorityQueue
from collections import defaultdict

from qelebrimbor.common.attributes_bg import CubeId, CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime

from qelebrimbor.pathfinders.path import Path

class PathFinderDFS:
    @staticmethod
    def find_minimal_paths(
        start: BgCube, final: BgCube,
        node_types: list[NodeType] | None = None, edge_types: list[EdgeType] | None = None,
        occupied_positions: set[Coordinates] = set(), reserved_positions: dict[Coordinates, CubeId] = dict(),
        maximal_overhead: int = 6
    ) -> tuple[int, list[Path]]:
        node_type_restrictions: list[NodeType] = node_types if node_types else []
        edge_type_restrictions: list[EdgeType] = edge_types if edge_types else []

        if any(tr in {NodeType.O, NodeType.Y} for tr in node_type_restrictions):
            raise Exception(f"Path cannot contain cubes of NodeType.O or NodeType.Y.")

        nt = len(node_type_restrictions)
        et = len(edge_type_restrictions)

        paths: list[Path] = []

        minimal_overhead = -1
        minimal_number_of_cubes = nt if nt % 2 == 0 else nt + 1
        maximal_volume = max(start.position.get_manhattan_distance(final.position), minimal_number_of_cubes) + maximal_overhead + 2
        console.info(f"Maximal volume considered : {maximal_volume}")

        initial = Path( start , final )
        queue: PriorityQueue[Path] = PriorityQueue[Path]()
        queue.put( initial )

        console.info(f"Searching for paths from {start} to {final} [{node_types}].")
        console.info(f"> Occupied : {occupied_positions}")
        console.info(f"> Reserved : {reserved_positions}")

        while not queue.empty():
            path: Path = queue.get()
            current = path.cubes[-1]
            length = len(path.cubes)
            console.debug(f"Current path : {path.cubes}")
            node_type_required = { node_type_restrictions[length-1] } if length <= nt else { NodeType.X, NodeType.Y, NodeType.Z, NodeType.O }
            pipe_type_required =   edge_type_restrictions[length-1]   if length <= et else EdgeType.IDENTITY
            console.debug(f"> Types required : {node_type_required}")
            for next_cube in BlockGraphHelper.get_candidate_constellation(current, node_types = node_type_required, pipe_type = pipe_type_required):
                extended: Path = path.copy()
                extended.append(next_cube)

                if extended.has_reached_target() and extended.manhattan_length() >= nt:
                    manhattan_length = extended.manhattan_length()
                    extended_overhead = extended.overhead()

                    console.info(f"> Target reached : {next_cube} [+{extended_overhead}]")
                    console.debug(f">> {extended}")

                    if manhattan_length < maximal_volume:
                        maximal_volume = manhattan_length
                        minimal_overhead = extended_overhead
                        paths.clear()

                    if manhattan_length == maximal_volume:
                        paths.append( extended )

                if next_cube.kind in [ CubeKind.YYY, CubeKind.OOO ]:
                    continue

                if path.occupies(next_cube.position) or next_cube.position in occupied_positions or next_cube.position in reserved_positions:
                    continue

                if extended.manhattan_length() + extended.manhattan_distance_remaining() < maximal_volume:
                    console.debug(f"> {next_cube}")
                    queue.put( extended )

        return minimal_overhead, paths

    @staticmethod
    def find_paths(
            final: tuple[CubeKind, Coordinates],
            start: tuple[CubeKind, Coordinates] = (CubeKind.XZZ, Spacetime.ORIGIN),
            maximal_overheads: Iterable[int] | None = None
    ):
        if maximal_overheads is None:
            return PathFinderDFS.__core_find_paths(final, start)
        else:
            for mo in maximal_overheads:
                paths = PathFinderDFS.__core_find_paths(final, start, mo)
                if len(paths) > 0:
                    return paths

        return {}

    @staticmethod
    def __core_find_paths(
            final: tuple[CubeKind, Coordinates],
            start: tuple[CubeKind, Coordinates] = (CubeKind.XZZ, Spacetime.ORIGIN),
            maximal_overhead: int = 6
    ) -> defaultdict[int, list[Path]]:
        paths = defaultdict(list)

        start_kind, start_position = start
        final_kind, final_position = final

        maximal_volume = start_position.get_manhattan_distance(final_position) + maximal_overhead

        initial = Path( start , final )
        queue: PriorityQueue[Path] = PriorityQueue[Path]()
        queue.put( initial )

        console.info(f"Searching for paths from {start_kind}@{start_position} to {final_kind}@{final_position}.")

        while not queue.empty():
            path = queue.get()
            current = path.cubes[-1]
            kind, position = current
            console.debug(f"Current : {kind}@{position}")
            for next_kind, next_position in BlockGraphHelper.get_candidate_constellation(current):
                if path.occupies(next_position):
                    continue

                if next_kind in [ CubeKind.YYY , CubeKind.OOO ]:
                    continue

                extended: Path = path.copy()
                extended.append(next_kind, next_position)

                if extended.has_reached_target():
                    extended_overhead = extended.overhead()
                    console.info(f"> Target reached : {next_kind}@{next_position} [+{extended_overhead}]")
                    console.debug(f">> {extended}")
                    paths[ extended_overhead ].append( extended )

                if extended.manhattan_length() + extended.manhattan_distance_remaining() < maximal_volume:
                    console.debug(f"> {next_kind}@{next_position}")
                    queue.put( extended )

        return paths