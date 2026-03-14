import logging as lgr
from collections import defaultdict
from typing import Iterable

console = lgr.getLogger(__name__)

from queue import PriorityQueue

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime

from qelebrimbor.pathfinders.path import Path

class PathFinderDFS:
    @staticmethod
    def find_minimal_paths(
        final: tuple[CubeKind, Coordinates], start: tuple[CubeKind, Coordinates] = (CubeKind.XZZ, Spacetime.ORIGIN),
        maximal_overhead: int = 6
    ) -> tuple[int, list[Path]]:
        paths = []

        start_kind, start_position = start
        final_kind, final_position = final

        minimal_overhead = None
        maximal_volume = start_position.get_manhattan_distance(final_position) + maximal_overhead

        initial = Path( start , final )
        queue: PriorityQueue = PriorityQueue()
        queue.put( initial )

        console.info(f"Searching for paths from {start_kind}@{start_position} to {final_kind}@{final_position}.")

        while not queue.empty():
            path = queue.get()
            kind, position = path.cubes[-1]
            console.debug(f"Current : {kind}@{position}")
            for next_kind, next_position in BlockGraphHelper.get_candidate_constellation(kind, position):
                if path.contains(next_position):
                    continue

                if next_kind in [ CubeKind.YYY , CubeKind.OOO ]:
                    continue

                extended: Path = path.copy()
                extended.append(next_kind, next_position)

                if extended.has_reached_target():
                    manhattan_length = extended.manhattan_length()
                    extended_overhead = extended.overhead()
                    if manhattan_length < maximal_volume:
                        maximal_volume = manhattan_length
                        minimal_overhead = extended_overhead
                        paths.clear()

                    if manhattan_length == maximal_volume:
                        console.info(f"> Target reached : {next_kind}@{next_position} [+{extended_overhead}]")
                        console.debug(f">> {extended}")
                        paths.append( extended )

                if extended.manhattan_length() + extended.manhattan_distance_remaining() < maximal_volume:
                    console.debug(f"> {next_kind}@{next_position}")
                    queue.put( extended )

        return minimal_overhead, paths

    @staticmethod
    def find_paths(
            final: tuple[CubeKind, Coordinates],
            start: tuple[CubeKind, Coordinates] = (CubeKind.XZZ, Spacetime.ORIGIN),
            maximal_overhead: Iterable[int] = None
    ):
        if maximal_overhead is None:
            maximal_overhead = [6]

        for mo in maximal_overhead:
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
        queue: PriorityQueue = PriorityQueue()
        queue.put( initial )

        console.info(f"Searching for paths from {start_kind}@{start_position} to {final_kind}@{final_position}.")

        while not queue.empty():
            path = queue.get()
            kind, position = path.cubes[-1]
            console.debug(f"Current : {kind}@{position}")
            for next_kind, next_position in BlockGraphHelper.get_candidate_constellation(kind, position):
                if path.contains(next_position):
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