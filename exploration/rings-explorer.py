import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)

from functools import reduce
from itertools import product
from collections import defaultdict

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import Spacetime

from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS
from qelebrimbor.pathfinders.path import Path

logging.getLogger('qelebrimbor.helpers').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.utilities').setLevel(logging.INFO)

def format_paths(paths: defaultdict[int, list[Path]]):
    report = ""
    for ovh in sorted(paths.keys()):
        report += f"+{ovh}:{len(paths[ovh])} "
    return report

def find_complete_rings(
        target_a: tuple[CubeKind, Coordinates], paths_ra: defaultdict[int, list[Path]],
        target_b: tuple[CubeKind, Coordinates], paths_rb: defaultdict[int, list[Path]]
):
    console.info(f"> Targets : {target_a} and {target_b}")
    console.info(f"> Paths R -> A : {format_paths(paths_ra)}")
    console.info(f"> Paths R -> B : {format_paths(paths_rb)}")

    paths_ab = PathFinderDFS.find_paths(target_b, target_a)
    console.info(f"> Paths A -> B : {format_paths(paths_ab)}")

if __name__ == "__main__":
    manhattan_distance = 1
    # The following seem to follow from symmetry relative to the source Cube
    # > Conjecture 1 : CubeKind.ZZX yields the same outcomes as CubeKind.ZXZ
    # > Conjecture 2 : CubeKind.XXZ yields the same outcomes as CubeKind.XZX
    x_kinds = [ CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZZX ]
    z_kinds = [ CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ ]
    positions = set(
        filter(
            lambda pos: pos.x >= 0 and pos.y >= 0 and pos.z >= 0 and pos != Spacetime.ORIGIN,
            [ reduce(lambda acc, x : acc + x, steps, Spacetime.ORIGIN)
              for steps in product(Spacetime.STEPS, repeat = manhattan_distance)
            ]
        )
    )

    source = (CubeKind.XZZ, Spacetime.ORIGIN)
    source_kind, source_position = source
    console.info(f"Source kind : {source_kind}@{source_position}")
    console.info(f"> Manhattan Distance : {manhattan_distance}")

    console.info(f"Positions : {len(positions)}")

    # Cases w/ 3 X-spiders
    console.info(f"Three X-spiders")
    three_xs = list(product(range(len(x_kinds)), positions))

    for index_a, position_a in three_xs:
        kind_a = x_kinds[index_a]
        target_a = (kind_a, position_a)
        paths_ra = PathFinderDFS.find_paths(target_a, maximal_overhead = range(6, 10, 2))
        for index_b, position_b in three_xs:
            if index_a <= index_b and position_a != position_b:
                kind_b = x_kinds[index_b]
                target_b = (kind_b, position_b)
                paths_rb = PathFinderDFS.find_paths(target_b, maximal_overhead = range(6, 10, 2))
                find_complete_rings(target_a, paths_ra, target_b, paths_rb)

    # # Cases w/ 2 X-spiders, 1 Z-spider
    # console.info(f"Two X-spiders, one Z-spider")
    # for index_a in range(len(x_kinds)):
    #     for index_b in range(len(x_kinds)):
    #         link_a_kind = x_kinds[index_a]
    #         link_b_kind = z_kinds[index_b]
    #         console.info(f"Link-A kind : {link_a_kind}, Link-B kind : {link_b_kind}")