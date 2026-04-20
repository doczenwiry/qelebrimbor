from logging import getLogger

from qelebrimbor.common.components import BgCube

console = getLogger(__name__)

from qelebrimbor.helpers.spacetime import Spacetime

from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS

class VolumeFinder:
    @staticmethod
    def get_path_overhead(source: BgCube, target: BgCube):
        discovered_paths = PathFinderDFS.find_minimal_paths(start = source, final = target, maximal_overhead= 12)
        manhattan_distance = Spacetime.ORIGIN.get_manhattan_distance(target.position)
        differential = discovered_paths[0].manhattan_length() - manhattan_distance

        return differential