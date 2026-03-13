from logging import getLogger
console = getLogger(__name__)

from qelebrimbor.helpers.spacetime import Spacetime, Coordinates
from qelebrimbor.common.components_bg import CubeKind

from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS

class VolumeFinder:
    SOURCE = (CubeKind.XZZ, Spacetime.ORIGIN)

    @staticmethod
    def get_path_overhead(target: tuple[CubeKind, Coordinates]):
        minimal_volume, discovered_paths = PathFinderDFS.find_paths(target, VolumeFinder.SOURCE, extra_volume = 12)
        _, target_position = target
        manhattan_distance = Spacetime.ORIGIN.get_manhattan_distance(target_position)
        differential = minimal_volume - manhattan_distance

        return differential