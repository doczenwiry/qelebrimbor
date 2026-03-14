import logging as lgr
console = lgr.getLogger(__name__)

from collections import deque

from qelebrimbor.pathfinders.path import Path
from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime

class PathFinderBFS:
    @staticmethod
    def find_paths(
        final: tuple[CubeKind, Coordinates], start: tuple[CubeKind, Coordinates] = (CubeKind.XZZ, Spacetime.ORIGIN),
        extra_volume: int = 3
    ) -> tuple[int, list[Path]]:
        paths = []

        start_kind, start_position = start
        final_kind, final_position = final

        console.info(f"Searching for paths from {start_kind}@{start_position} to {final_kind}@{final_position}.")

        minimal_volume = None
        maximal_volume = start_position.get_manhattan_distance(final_position) + extra_volume

        initial = Path( start, final )
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
                    if extended.manhattan_length() < maximal_volume:
                        minimal_volume = extended.manhattan_length()
                        maximal_volume = extended.manhattan_length()
                        paths.clear()
                    if extended.manhattan_length() == maximal_volume:
                        paths.append( extended )

                if extended.manhattan_length() <= maximal_volume:
                    console.debug(f"> {next_kind}@{next_position}")

                    queue.append( extended )

        return minimal_volume, paths