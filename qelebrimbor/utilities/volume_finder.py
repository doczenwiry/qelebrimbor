from logging import getLogger
console = getLogger(__name__)

from qelebrimbor.helpers.spacetime import Spacetime, Coordinates
from qelebrimbor.common.components_bg import CubeKind

from qelebrimbor.pathfinders.pathfinder_dfs import find_paths_dfs

class VolumeFinder:
    SOURCE = (CubeKind.XZZ, Spacetime.ORIGIN)

    @staticmethod
    def get_path_overhead(target: tuple[CubeKind, Coordinates]):
        discovered_paths = find_paths_dfs(target, VolumeFinder.SOURCE, extra_volume = 12)
        minimal_volume = min(discovered_paths.keys())
        _, target_position = target
        manhattan_distance = Spacetime.ORIGIN.get_manhattan_distance(target_position)
        differential = minimal_volume - manhattan_distance

        return differential

        # Target : [ XZZ ]
        # INFO:__main__:Statistics for MD=2 / cases=6 : defaultdict(<class 'int'>, {2: 3, 0: 3})
        # INFO:__main__:Statistics for MD=3 / cases=10 : defaultdict(<class 'int'>, {0: 6, 2: 4})
        # INFO:__main__:Statistics for MD=4 / cases=15 : defaultdict(<class 'int'>, {0: 11, 2: 4})
        # INFO:__main__:Statistics for MD=5 / cases=21 : defaultdict(<class 'int'>, {2: 4, 0: 17})
        # INFO:__main__:Statistics for MD=6 / cases=28 : defaultdict(<class 'int'>, {2: 4, 0: 24})
        # INFO:__main__:Statistics for MD=7 / cases=36 : defaultdict(<class 'int'>, {0: 32, 2: 4})
        # INFO:__main__:Statistics for MD=8 / cases=45 : defaultdict(<class 'int'>, {0: 41, 2: 4})
        # INFO:__main__:Statistics for MD=9 / cases=55 : defaultdict(<class 'int'>, {0: 51, 2: 4})
        # INFO:__main__:Statistics for MD=10 / cases=66 : defaultdict(<class 'int'>, {0: 62, 2: 4})

        # Target : all
        # INFO:__main__:Statistics for MD<=1 / cases=18  : defaultdict(<class 'int'>, {0:  4, 2:  5, 4:5, 6:4})   ~22%
        # INFO:__main__:Statistics for MD<=2 / cases=36  : defaultdict(<class 'int'>, {0: 11, 2: 19, 4:6})        ~30%
        # INFO:__main__:Statistics for MD<=3 / cases=78  : defaultdict(<class 'int'>, {0: 29, 2: 35, 4:10, 6:4})  ~37%
        # INFO:__main__:Statistics for MD<=4 / cases=126 : defaultdict(<class 'int'>, {0: 57, 2: 58, 4:11})       ~45%
        # INFO:__main__:Statistics for MD<=5 / cases=204 : defaultdict(<class 'int'>, {0:102, 2: 83, 4:15, 6:4})  ~50%
        # INFO:__main__:Statistics for MD<=6 / cases=294 : defaultdict(<class 'int'>, {0:163, 2:115, 4:16})       ~55%
        # INFO:__main__:Statistics for MD<=7 / cases=420 : defaultdict(<class 'int'>, {0:247, 2:149, 4:20, 6:4})  ~59%
        # INFO:__main__:Statistics for MD<=8 / cases=564 : defaultdict(<class 'int'>, {2:190, 0:353, 4:21})       ~63%