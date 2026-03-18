from logging import basicConfig, getLogger, INFO, CRITICAL
basicConfig(level = INFO)
console = getLogger(__name__)

from functools import reduce
from itertools import product
from collections import defaultdict

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import Spacetime

from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS
from qelebrimbor.pathfinders.path import Path

getLogger('qelebrimbor.helpers').setLevel(CRITICAL)
getLogger('qelebrimbor.pathfinders').setLevel(CRITICAL)
getLogger('qelebrimbor.utilities').setLevel(INFO)

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
    paths_report  = ""
    paths_report += f"[ R -> A : {format_paths(paths_ra)}] , "
    paths_report += f"[ R -> B : {format_paths(paths_rb)}] , "
    paths_ab = PathFinderDFS.find_paths(target_b, target_a)
    paths_report += f"[ A -> B : {format_paths(paths_ab)}]"

    console.info(f">> Paths : {paths_report}")

    minimal_overhead_ra = min(paths_ra.keys())
    minimal_overhead_rb = min(paths_rb.keys())
    minimal_overhead_ab = min(paths_ab.keys())
    minimal_overhead = minimal_overhead_ra + minimal_overhead_rb + minimal_overhead_ab
    console.info(f">> MINIMAL OVERHEAD POSSIBLE : {minimal_overhead}\n")

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
    console.info("###################################################################################################")
    console.info("#                                            { X,X,X }                                            #")
    console.info("###################################################################################################")
    three_xs = list(product(range(len(x_kinds)), positions))

    for index_a, position_a in three_xs:
        target_a = (x_kinds[index_a], position_a)
        paths_ra = PathFinderDFS.find_paths(target_a, maximal_overhead = range(6, 10, 2))
        for index_b, position_b in three_xs:
            if index_a <= index_b and position_a != position_b:
                target_b = (x_kinds[index_b], position_b)
                paths_rb = PathFinderDFS.find_paths(target_b, maximal_overhead = range(6, 10, 2))
                find_complete_rings(target_a, paths_ra, target_b, paths_rb)

    # Cases w/ 2 X-spiders, 1 Z-spider
    console.info("###################################################################################################")
    console.info("#                                            { X,X,Z }                                            #")
    console.info("###################################################################################################")
    two_xs = list(product(range(len(x_kinds)), positions))
    one_zs = list(product(range(len(z_kinds)), positions))
    for index_a, position_a in two_xs:
        target_a = (x_kinds[index_a], position_a)
        paths_ra = PathFinderDFS.find_paths(target_a, maximal_overhead = range(6, 10, 2))
        for index_b, position_b in one_zs:
            if position_a != position_b:
                target_b = (z_kinds[index_b], position_b)
                paths_rb = PathFinderDFS.find_paths(target_b, maximal_overhead = range(6, 10, 2))
                find_complete_rings(target_a, paths_ra, target_b, paths_rb)