import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)
console.setLevel(logging.INFO)

import numpy as np
from functools import reduce
from itertools import product
from collections import deque, defaultdict

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime

class Path:
    def __init__(self, source: tuple[CubeKind, Coordinates] = None):
        self.cubes = []
        self.occupied = set()

        if source is not None:
            self.cubes.append(source)
            self.occupied.add(source[1])

    def volume(self):
        return len(self.cubes) - 1

    def contains(self, position: Coordinates):
        return position in self.occupied

    def append(self, kind: CubeKind, position: Coordinates):
        self.cubes.append((kind, position))
        self.occupied.add(position)

    def copy(self):
        cp = Path()
        cp.cubes.extend(self.cubes)
        cp.occupied = set(self.occupied)
        return cp

    def __str__(self):
        return str(self.cubes)

    def __repr__(self):
        return str(self.cubes)

def find_paths(
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

if __name__ == "__main__":

    MD = 6

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
    for target in targets:
        discovered_paths = find_paths(target, extra_volume = 6)
        minimal_volume = min(discovered_paths.keys())
        manhattan_distance = Spacetime.ORIGIN.get_manhattan_distance(target[1])
        differential = minimal_volume - manhattan_distance
        console.info(f"{count}/{total}> Target {target} [min-vol={minimal_volume}/man-dis={manhattan_distance}] : volume +{differential}")
        statistics[differential] += 1
        count += 1

    console.info(f"Statistics for MD={MD} / cases={total} : {statistics}")

    # INFO:__main__:Statistics for MD=2 / cases=36  : defaultdict(<class 'int'>, {0: 11, 2: 19, 4:6})
    # INFO:__main__:Statistics for MD=3 / cases=78  : defaultdict(<class 'int'>, {0: 29, 2: 35, 4:10, 6:4})
    # INFO:__main__:Statistics for MD=4 / cases=126 : defaultdict(<class 'int'>, {0: 57, 2: 58, 4:11})
    # INFO:__main__:Statistics for MD=5 / cases=204 : defaultdict(<class 'int'>, {0:102, 2: 83, 4:15, 6:4})
    # INFO:__main__:Statistics for MD=6 / cases=294 : defaultdict(<class 'int'>, {0:163, 2:115, 4:16})