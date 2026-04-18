from logging import getLogger
console = getLogger(__name__)

from qelebrimbor.helpers.spacetime import Spacetime, Coordinates
from qelebrimbor.common.attributes_bg import CubeKind

from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS

class VolumeFinder:
    SOURCE = (CubeKind.XZZ, Spacetime.ORIGIN)

    @staticmethod
    def get_path_overhead(target: tuple[CubeKind, Coordinates]):
        minimal_volume, discovered_paths = PathFinderDFS.find_minimal_paths(final = target, start = VolumeFinder.SOURCE, maximal_overhead= 12)
        _, target_position = target
        manhattan_distance = Spacetime.ORIGIN.get_manhattan_distance(target_position)
        differential = minimal_volume - manhattan_distance

        return differential