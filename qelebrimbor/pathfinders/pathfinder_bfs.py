import logging as lgr

from qelebrimbor.pathfinders.paths import Path

console = lgr.getLogger(__name__)

from collections import defaultdict, deque

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime

def find_paths_bfs(
    final: tuple[CubeKind, Coordinates], start: tuple[CubeKind, Coordinates] = (CubeKind.XZZ, Spacetime.ORIGIN),
    extra_volume: int = 3
) -> defaultdict[int, list[Path]]:
    paths = defaultdict(list)

    start_kind, start_position = start
    final_kind, final_position = final

    maximal_volume = start_position.get_manhattan_distance(final_position) + extra_volume

    initial = Path( start )
    queue: deque[Path] = deque([ initial ])

    while queue:
        path = queue.popleft()
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
                maximal_volume = extended.volume()
                paths[ maximal_volume ].append( extended )

            if extended.volume() <= maximal_volume:
                console.debug(f"> {next_kind}@{next_position}")

                queue.append( extended )

    return paths