from logging import basicConfig, getLogger, INFO, CRITICAL
basicConfig(level = INFO)
console = getLogger(__name__)

from functools import reduce
from itertools import product
from collections import defaultdict

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import SpacetimeHelper, Octant

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
        target_b: tuple[CubeKind, Coordinates], paths_rb: defaultdict[int, list[Path]],
        target_c: tuple[CubeKind, Coordinates]
):
    console.info(f"> Targets : {target_a}, {target_b} and {target_c}")
    paths_report  = ""
    paths_report += f"[ R -> A : {format_paths(paths_ra)}] , "
    paths_report += f"[ R -> B : {format_paths(paths_rb)}] , "
    paths_ac = PathFinderDFS.find_paths(target_c, target_a, maximal_overheads= range(6, 8, 2))
    paths_report += f"[ A -> C : {format_paths(paths_ac)}]"
    paths_bc = PathFinderDFS.find_paths(target_c, target_b, maximal_overheads= range(6, 8, 2))
    paths_report += f"[ B -> C : {format_paths(paths_bc)}]"

    console.info(f">> Paths : {paths_report}")

    if paths_ra and paths_rb and paths_ac and paths_bc:
        minimal_ra = next(iter(paths_ra.values()))[0].manhattan_length()
        minimal_rb = next(iter(paths_rb.values()))[0].manhattan_length()
        minimal_ac = next(iter(paths_ac.values()))[0].manhattan_length()
        minimal_bc = next(iter(paths_bc.values()))[0].manhattan_length()
        minimal = minimal_ra + minimal_rb + minimal_ac + minimal_bc
    else:
        minimal = None
    console.info(f">> Manhattan Length Achieved ? {minimal}\n")

    return minimal

def find_xxxx_rings():
    # Cases w/ 3 X-spiders
    console.info("###################################################################################################")
    console.info("#                                           { X,X,X,X }                                           #")
    console.info("###################################################################################################")
    four_xs_md1 = list(product(range(len(x_kinds)), range(len(positions_md_1))))
    four_xs_md2 = list(product(range(len(x_kinds)), range(len(positions_md_2))))

    minimum_achieved = None
    for kind_a, position_a in four_xs_md1:
        target_a = (x_kinds[kind_a], positions_md_1[position_a])
        paths_ra = PathFinderDFS.find_paths(target_a, maximal_overheads= range(6, 10, 2))
        for kind_b, position_b in four_xs_md1:
            if kind_a <= kind_b and position_a < position_b:
                target_b = (x_kinds[kind_b], positions_md_1[position_b])
                paths_rb = PathFinderDFS.find_paths(target_b, maximal_overheads= range(6, 10, 2))
                for index_c, position_c in four_xs_md2:
                    if position_a != position_c != position_b:
                        target_c = (x_kinds[index_c], positions_md_2[position_c])
                        minimum = find_complete_rings(target_a, paths_ra, target_b, paths_rb, target_c)
                        if minimum_achieved is None or minimum_achieved < minimum:
                            minimum_achieved = minimum

    console.info(f"Minimum achieved is {minimum_achieved}")

def find_xzzx_rings():
    # Cases w/ 2 X-spiders, 1 Z-spider
    console.info("###################################################################################################")
    console.info("#                                           { X,X,X,Z }                                           #")
    console.info("###################################################################################################")
    four_md1 = list(product(range(len(x_kinds)), range(len(positions_md_1))))
    four_md2 = list(product(range(len(x_kinds)), range(len(positions_md_2))))

    minimum_achieved = None
    for kind_a, position_a in four_md1:
        target_a = (z_kinds[kind_a], positions_md_1[position_a])
        paths_ra = PathFinderDFS.find_paths(target_a, maximal_overheads= range(6, 10, 2))
        for kind_b, position_b in four_md1:
            if kind_a <= kind_b and position_a < position_b:
                target_b = (z_kinds[kind_b], positions_md_1[position_b])
                paths_rb = PathFinderDFS.find_paths(target_b, maximal_overheads= range(6, 10, 2))
                for index_c, position_c in four_md2:
                    if position_a != position_c != position_b:
                        target_c = (x_kinds[index_c], positions_md_2[position_c])
                        minimum = find_complete_rings(target_a, paths_ra, target_b, paths_rb, target_c)
                        if minimum_achieved is None or minimum_achieved < minimum:
                            minimum_achieved = minimum

    console.info(f"Minimum achieved is {minimum_achieved}")

def find_xzxx_rings():
    # Cases w/ 2 X-spiders, 1 Z-spider
    console.info("###################################################################################################")
    console.info("#                                           { X,Z,X,X }                                           #")
    console.info("###################################################################################################")
    four_md2 = list(product(range(len(x_kinds)), range(len(positions_md_2))))

    minimum_achieved = None
    count = 0
    total = len(four_md2)**3
    for kind_a, position_a in four_md2:
        target_a = (z_kinds[kind_a], positions_md_2[position_a])
        paths_ra = PathFinderDFS.find_paths(target_a, maximal_overheads= range(6, 10, 2))
        for kind_b, position_b in four_md2:
            if position_a < position_b:
                target_b = (x_kinds[kind_b], positions_md_2[position_b])
                paths_rb = PathFinderDFS.find_paths(target_b, maximal_overheads= range(6, 10, 2))
                for index_c, position_c in four_md2:
                    if position_a != position_c != position_b:
                        count += 1
                        console.info(f"{count}/{total}")
                        target_c = (x_kinds[index_c], positions_md_2[position_c])
                        minimum = find_complete_rings(target_a, paths_ra, target_b, paths_rb, target_c)
                        if minimum_achieved is None or (minimum is not None and minimum < minimum_achieved):
                            minimum_achieved = minimum

    console.info(f"Minimum achieved is {minimum_achieved}")

if __name__ == "__main__":
    manhattan_distance = 2
    # The following seem to follow from symmetry relative to the source Cube
    # > Conjecture 1 : CubeKind.ZZX yields the same outcomes as CubeKind.ZXZ
    # > Conjecture 2 : CubeKind.XXZ yields the same outcomes as CubeKind.XZX

    x_kinds = [ CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZZX ]
    z_kinds = [ CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ ]

    positions_md_1 = list(set(
        filter(
            lambda pos: pos != SpacetimeHelper.ORIGIN and SpacetimeHelper.in_octant(pos, Octant.PPP),
            [ reduce(lambda acc, x : acc + x, steps, SpacetimeHelper.ORIGIN)
              for steps in product(SpacetimeHelper.STEPS, repeat = 1)
            ]
        )
    ))

    positions_md_2 = list(set(
        filter(
            lambda pos: pos != SpacetimeHelper.ORIGIN and SpacetimeHelper.in_octant(pos, Octant.PPP),
            [ reduce(lambda acc, x : acc + x, steps, SpacetimeHelper.ORIGIN)
              for steps in product(SpacetimeHelper.STEPS, repeat = manhattan_distance)
            ]
        )
    ))

    source = (CubeKind.XZZ, SpacetimeHelper.ORIGIN)
    source_kind, source_position = source
    console.info(f"Source kind : {source_kind}@{source_position}")
    console.info(f"> Manhattan Distance : {manhattan_distance}")

    console.info(f"Positions : {len(positions_md_2)}")

    find_xzxx_rings()