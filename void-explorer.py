import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)

from collections import defaultdict

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.utilities.volume_finder import VolumeFinder

logging.getLogger('qelebrimbor.helpers').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.utilities').setLevel(logging.INFO)

MOVE_ABOVE = Spacetime.XM + Spacetime.ZP
MOVE_RIGHT = Spacetime.XM + Spacetime.YP

if __name__ == "__main__":
    manhattan_distance = 6
    start_position = manhattan_distance * Spacetime.XP
    # The following seem to follow from symmetry relative to the source Cube
    # > Conjecture 1 : CubeKind.ZZX yields the same outcomes as CubeKind.ZXZ
    # > Conjecture 2 : CubeKind.XXZ yields the same outcomes as CubeKind.XZX
    kinds = [CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZZX, CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ]
    positions = [(xy, z) for z in range(manhattan_distance + 1) for xy in range(manhattan_distance - z + 1)]

    for target_kind in kinds:
        count = 1
        statistics = defaultdict(int)
        console.info(f"Target kind : {target_kind}")
        overheads = defaultdict(int)
        for xy, z in positions:
            target_position = start_position + z * MOVE_ABOVE + xy * MOVE_RIGHT
            overhead = VolumeFinder.find_path_overhead( (target_kind, target_position) )

            statistics[overhead] += 1
            overheads[xy, z] = overhead

            count += 1
        percentage = 100.0 * statistics[0] / len(positions)
        console.info(f"> Zero-overhead percentage : {percentage:.2f}% [{statistics}]")
        for current_z in reversed(range(manhattan_distance + 1)):
            report = current_z * ' '
            for current_xy in range(manhattan_distance - current_z + 1):
                report += f" {overheads[current_xy, current_z]}"
            console.info(f">> Overhead :{report}")