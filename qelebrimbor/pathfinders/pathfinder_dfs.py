import logging as lgr
console = lgr.getLogger(__name__)

from collections import defaultdict
from queue import PriorityQueue

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime

from qelebrimbor.pathfinders.paths import Path

def find_paths_dfs(
    final: tuple[CubeKind, Coordinates], start: tuple[CubeKind, Coordinates] = (CubeKind.XZZ, Spacetime.ORIGIN),
    extra_volume: int = 3
) -> defaultdict[int, list[Path]]:
    paths = defaultdict(list)

    start_kind, start_position = start
    final_kind, final_position = final

    minimal_manhattan_distance = start_position.get_manhattan_distance(final_position) + extra_volume

    initial = Path( start )
    queue: PriorityQueue = PriorityQueue()
    queue.put( (initial.manhattan_distance_remaining(final), initial) )

    console.info(f"Searching for paths from {start_kind}@{start_position} to {final_kind}@{final_position}.")

    while not queue.empty():
        mdr, path = queue.get()
        kind, position = path.cubes[-1]
        console.debug(f"Current : {kind}@{position}")
        for next_kind, next_position in BlockGraphHelper.get_candidate_constellation(kind, position):
            if path.contains(next_position):
                continue

            if not Spacetime.in_octant(next_position):
                continue

            if next_kind in [ CubeKind.YYY , CubeKind.OOO ]:
                continue

            extended: Path = path.copy()
            extended.append(next_kind, next_position)

            if next_kind == final_kind and next_position == final_position:
                console.debug(f"> Target reached : {next_kind}@{next_position}")
                minimal_manhattan_distance = extended.manhattan_length()
                paths[ minimal_manhattan_distance ].append( extended )

            if extended.manhattan_length() <= minimal_manhattan_distance:
                console.debug(f"> {next_kind}@{next_position}")

                queue.put( (extended.manhattan_distance_remaining(final), extended) )

    return paths