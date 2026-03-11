import logging

from qelebrimbor.pathfinders.pathfinder_bfs import find_paths_bfs
from qelebrimbor.pathfinders.pathfinder_dfs import find_paths_dfs

logging.basicConfig(level=logging.DEBUG)
console = logging.getLogger(__name__)
console.setLevel(logging.INFO)

from collections import defaultdict

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.helpers.spacetime import Spacetime

logging.getLogger('qelebrimbor.helpers').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders').setLevel(logging.CRITICAL)

if __name__ == "__main__":

    MD = 11
    START = MD * Spacetime.XP
    MOVE_ABOVE = Spacetime.XM + Spacetime.ZP
    MOVE_RIGHT = Spacetime.XM + Spacetime.YP

    # The following seem to follow from symmetry relative to the source Cube
    # > Conjecture 1 : CubeKind.ZZX yields the same outcomes as CubeKind.ZXZ
    # > Conjecture 2 : CubeKind.XXZ yields the same outcomes as CubeKind.XZX
    kinds = [ CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZXX, CubeKind.XZX]
    positions = [ START + z * MOVE_ABOVE + xy * MOVE_RIGHT for z in range(MD+1) for xy in range(MD - z + 1) ]

    total_kinds = len(kinds)
    total_positions = len(positions)
    console.info(f"Kinds [{total_kinds}]")
    console.info(f"Positions [{total_positions}]")

    console.info(f"Manhattan Distance : {MD}")
    for target_kind in kinds:
        count = 1
        statistics = defaultdict(int)
        console.info(f"Target kind : {target_kind}")
        for target_position in positions:
            target = (target_kind, target_position)
            discovered_paths = find_paths_dfs(target, extra_volume = 12)
            minimal_volume = min(discovered_paths.keys())
            manhattan_distance = Spacetime.ORIGIN.get_manhattan_distance(target_position)
            differential = minimal_volume - manhattan_distance
            console.debug(f"{count}/{total_positions}> @{target_position} [min-vol={minimal_volume}/man-dis={manhattan_distance}] : volume +{differential}")
            # for mv, path in discovered_paths.items(): console.info(f"> {path}")
            statistics[differential] += 1
            count += 1
        percentage = 100.0 * statistics[0] / total_positions
        console.info(f"> Zero-overhead percentage : {percentage:.2f}% [{statistics}]")
        # console.info(f"> Statistics for MD={MD} / cases={total_positions} : {statistics}")

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