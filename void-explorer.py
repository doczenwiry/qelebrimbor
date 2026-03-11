import logging

from qelebrimbor.pathfinders.pathfinder_bfs import find_paths_bfs
from qelebrimbor.pathfinders.pathfinder_dfs import find_paths_dfs

logging.basicConfig(level=logging.DEBUG)
console = logging.getLogger(__name__)
console.setLevel(logging.INFO)

from functools import reduce
from itertools import product
from collections import defaultdict

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.helpers.spacetime import Spacetime

logging.getLogger('qelebrimbor.helpers').setLevel(logging.CRITICAL)

if __name__ == "__main__":

    MD = 1

    kinds = [ CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZZX, CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ ]
    steps = set(filter(
        lambda entry : entry != Spacetime.ORIGIN and entry.x >= 0 and entry.y >= 0 and entry.z >= 0,
        [ reduce(lambda acc, x : acc + x, steps, Spacetime.ORIGIN)
          for steps in product(Spacetime.STEPS, repeat = MD) ]
    ))

    targets = [
        (kind, Spacetime.ORIGIN + step)
        for kind, step in product(kinds, steps)
    ]

    count = 1
    total = len(targets)
    print(f"Targets : {total}")

    statistics = defaultdict(int)
    for target in targets[:1]:
        discovered_paths = find_paths_bfs(target, extra_volume = 6)
        minimal_volume = min(discovered_paths.keys())
        manhattan_distance = Spacetime.ORIGIN.get_manhattan_distance(target[1])
        differential = minimal_volume - manhattan_distance
        console.info(f"{count}/{total}> Target {target} [min-vol={minimal_volume}/man-dis={manhattan_distance}] : volume +{differential}")
        for mv, path in discovered_paths.items():
            console.info(f"> {path}")
        statistics[differential] += 1
        count += 1

    console.info(f"Statistics for MD={MD} / cases={total} : {statistics}")

    # INFO:__main__:Statistics for MD=2 / cases=36  : defaultdict(<class 'int'>, {0: 11, 2: 19, 4:6})
    # INFO:__main__:Statistics for MD=3 / cases=78  : defaultdict(<class 'int'>, {0: 29, 2: 35, 4:10, 6:4})
    # INFO:__main__:Statistics for MD=4 / cases=126 : defaultdict(<class 'int'>, {0: 57, 2: 58, 4:11})
    # INFO:__main__:Statistics for MD=5 / cases=204 : defaultdict(<class 'int'>, {0:102, 2: 83, 4:15, 6:4})
    # INFO:__main__:Statistics for MD=6 / cases=294 : defaultdict(<class 'int'>, {0:163, 2:115, 4:16})