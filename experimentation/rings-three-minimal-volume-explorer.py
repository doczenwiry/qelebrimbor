from logging import basicConfig, getLogger, INFO, CRITICAL
basicConfig(level = INFO)
console = getLogger(__name__)
getLogger('qelebrimbor.helpers').setLevel(CRITICAL)
getLogger('qelebrimbor.pathfinders').setLevel(CRITICAL)
getLogger('qelebrimbor.utilities').setLevel(INFO)

from itertools import product
from collections import defaultdict

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.pathfinders.path import Path
from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS

def format_paths(paths: defaultdict[int, list[Path]]):
    report = ""
    for ovh in sorted(paths.keys()):
        report += f"+{ovh}:{len(paths[ovh])} "
    return report

def compute_ring_volume(
        target_a: tuple[CubeKind, Coordinates],
        target_b: tuple[CubeKind, Coordinates],
        target_c: tuple[CubeKind, Coordinates]
):
    console.info(f">>>>> Targets : {target_a}, {target_b} and {target_c}")
    total_volume = (Path.minimal_volume_possible(target_a, target_b, count_endpoints = False)
                    + Path.minimal_volume_possible(target_a, target_c, count_endpoints = False)
                    + 2)
    _, paths = PathFinderDFS.find_minimal_paths(start = target_c, final = target_b, maximal_overhead = 8)
    total_volume += paths[0].manhattan_length()
    console.info(f">>>>>> Total volume required : {total_volume}\n")

if __name__ == "__main__":
    manhattan_distance = 1
    # The following seem to follow from symmetry relative to the source Cube
    # > Conjecture 1 : CubeKind.ZZX yields the same outcomes as CubeKind.ZXZ
    # > Conjecture 2 : CubeKind.XXZ yields the same outcomes as CubeKind.XZX
    kinds = [ CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZZX, CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ ]

    source_kind = CubeKind.XZZ
    source_position = SpacetimeHelper.ORIGIN
    source = (source_kind, source_position)
    console.info(f"Source kind : {source_kind}@{source_position}")
    console.info(f"> Manhattan Distance : {manhattan_distance}")

    possibilities = list(filter(
        lambda ids : ids[0] <= ids[1] <= ids[2],
        product(range(len(kinds)), repeat = 3)
    ))

    positions = [SpacetimeHelper.ORIGIN, SpacetimeHelper.YP, SpacetimeHelper.ZP]

    count = 1
    total = len(possibilities)
    for indices in possibilities:
        cubes = list(zip(map(lambda idx : kinds[idx], indices), positions))
        console.info(f"{count}/{total}> {cubes}")
        compute_ring_volume(cubes[0], cubes[1], cubes[2])
        count += 1