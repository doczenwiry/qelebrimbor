import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)

from collections import defaultdict

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import Spacetime, Octant
from qelebrimbor.helpers.octahedron import OctahedronHelper
from qelebrimbor.utilities.volume_finder import VolumeFinder

logging.getLogger('qelebrimbor.helpers').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.utilities').setLevel(logging.INFO)

MOVE_ABOVE = Spacetime.XM + Spacetime.ZP
MOVE_RIGHT = Spacetime.XM + Spacetime.YP

def layout_overheads(manhattan_distance: int, overheads: defaultdict[Coordinates, int]):
    for z in reversed(range(manhattan_distance + 1)):
        report = z * ' '
        for position, overhead in overheads.items():
            if position.z == z:
                report += f" {overhead}"
        console.info(f">> Overheads :{report}")

if __name__ == "__main__":
    manhattan_distance = 2
    start_position = manhattan_distance * Spacetime.XP
    # The following seem to follow from symmetry relative to the source cube
    # > Conjecture 1 : CubeKind.ZZX yields the same outcomes as CubeKind.ZXZ
    # > Conjecture 2 : CubeKind.XXZ yields the same outcomes as CubeKind.XZX
    kinds = [CubeKind.XZZ]
    positions = list(OctahedronHelper.get_hemi_positions(manhattan_distance, upper = True))

    console.info(f"Corners : {manhattan_distance * Spacetime.YM} {manhattan_distance * Spacetime.XM}")
    console.info(f"Corners : {manhattan_distance * Spacetime.XP} {manhattan_distance * Spacetime.YP}")

    for position in positions:
        console.info(f"> {position}")

    # Top row : ( 0,-2, 0) - (-1,-1, 0) - (-2, 0, 0)
    # In1 row :       ( 0,-1,+1) - (-1, 0,+1)
    # Mid row : (+1,-1, 0) - ( 0, 0,+2) - (-1,+1, 0)
    # In2 row :       (+1,-1,+1) - ( 0,-1,+1)
    # Bot row : (+2, 0, 0) - (+1,+1, 0) - ( 0,+2, 0)

    # for target_kind in kinds:
    #     console.info(f"Target kind : {target_kind}")
    #     count = 1
    #     statistics: defaultdict[int, int] = defaultdict(int)
    #     overheads: defaultdict[Coordinates, int] = defaultdict(int)
    #     for target_position in positions:
    #         overhead = VolumeFinder.get_path_overhead((target_kind, target_position))
    #         statistics[overhead] += 1
    #         overheads[target_position] = overhead
    #
    #         count += 1
    #     percentage = 100.0 * statistics[0] / len(positions)
    #     console.info(f"UPPER> Zero-overhead percentage : {percentage:.2f}% [{statistics}]")
    #     layout_overheads(manhattan_distance, overheads)