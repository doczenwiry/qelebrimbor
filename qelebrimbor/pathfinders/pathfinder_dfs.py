import logging as lgr
import queue

from qelebrimbor.common.components_zx import NodeType

console = lgr.getLogger(__name__)

from typing import Iterable
from queue import PriorityQueue
from collections import defaultdict

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime

from qelebrimbor.pathfinders.path import Path

class PathFinderDFS:
    @staticmethod
    def find_minimal_paths(
        final: tuple[CubeKind, Coordinates], start: tuple[CubeKind, Coordinates] = (CubeKind.XZZ, Spacetime.ORIGIN),
        type_restrictions: list[NodeType] = [], occupied_positions: set[Coordinates] = set(),
        maximal_overhead: int = 6
    ) -> tuple[int, list[Path]]:
        if any(tr in {NodeType.O, NodeType.Y} for tr in type_restrictions):
            raise Exception(f"Path cannot contain cubes of NodeType.O or NodeType.Y.")

        paths: list[Path] = []

        start_kind, start_position = start
        final_kind, final_position = final

        minimal_overhead = -1
        maximal_volume = start_position.get_manhattan_distance(final_position) + maximal_overhead

        initial = Path( start , final )
        queue: PriorityQueue[Path] = PriorityQueue[Path]()
        queue.put( initial )

        console.info(f"Searching for paths from {start_kind}@{start_position} to {final_kind}@{final_position} [{type_restrictions}].")

        while not queue.empty():
            path: Path = queue.get()
            current = path.cubes[-1]
            console.debug(f"Current path : {path.cubes}")
            types_required: set[NodeType] = {
                node_type for node_type in (NodeType.X, NodeType.Z)
                if path.manhattan_length() >= len(type_restrictions) or node_type == type_restrictions[path.manhattan_length()]
            }
            console.debug(f"> Types required : {types_required}")
            for next_kind, next_position in BlockGraphHelper.get_candidate_constellation(current, node_types = types_required):
                extended: Path = path.copy()
                extended.append(next_kind, next_position)

                if extended.has_reached_target() and extended.manhattan_length() >= len(type_restrictions):
                    manhattan_length = extended.manhattan_length()
                    extended_overhead = extended.overhead()

                    console.info(f"> Target reached : {next_kind}@{next_position} [+{extended_overhead}]")
                    console.debug(f">> {extended}")

                    if manhattan_length < maximal_volume:
                        maximal_volume = manhattan_length
                        minimal_overhead = extended_overhead
                        paths.clear()

                    if manhattan_length == maximal_volume:
                        paths.append( extended )

                if path.occupies(next_position) or next_position in occupied_positions:
                    continue

                if extended.manhattan_length() + extended.manhattan_distance_remaining() < maximal_volume:
                    console.debug(f"> {next_kind}@{next_position}")
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