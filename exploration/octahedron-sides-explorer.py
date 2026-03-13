import logging

from IPython.core.magics.ast_mod import mangle_all

logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)

from functools import cmp_to_key
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

def __convert_direction(axis: str, direction: int):
    if direction == +1:
        return axis + 'P'
    elif direction == -1:
        return axis + 'M'
    else:
        raise ValueError("Direction must be +1/-1.")

def __make_overhead_header(face: Octant, z: int):
    if z == 0:
        xd, yd, zd = face.value
        point_l = __convert_direction("X", xd) if xd == yd else __convert_direction("Y", yd)
        point_r = __convert_direction("Y", yd) if xd == yd else __convert_direction("X", xd)
        hdr = f"{point_l}--{point_r}"
    elif z == manhattan_distance:
        hdr = "  ZP  "
    elif z == -manhattan_distance:
        hdr = "  ZM  "
    else:
        hdr = "      "

    return hdr

def __layout_overheads(faces: tuple[Octant, Octant], manhattan_distance: int, overheads: defaultdict[Coordinates, int]):
    target_face = faces[0]
    for z in range(manhattan_distance, -manhattan_distance-1, -1):
        oh_row = abs(z) * ' '
        current_row = sorted(filter(lambda p : p.z == z, overheads.keys()), key = SORTING_FUNCTIONS[target_face])
        for pos in current_row:
            oh = overheads[pos]
            oh_row += f" {oh}"
        hdr = __make_overhead_header(faces[0], z)
        console.info(f"{hdr}>{oh_row}")

def __cmp_xp_yp(position1: Coordinates, position2: Coordinates):
    return -1 if position1.x > position2.x and position1.y < position2.y else +1

def __cmp_yp_xm(position1: Coordinates, position2: Coordinates):
    return -1 if position1.x > position2.x and position1.y > position2.y else +1

def __cmp_xm_ym(position1: Coordinates, position2: Coordinates):
    return -1 if position1.x < position2.x and position1.y > position2.y else +1

def __cmp_ym_xp(position1: Coordinates, position2: Coordinates):
    return -1 if position1.x < position2.x and position1.y < position2.y else +1

SORTING_FUNCTIONS = {
    Octant.PPP : cmp_to_key(__cmp_xp_yp),
    Octant.MPP : cmp_to_key(__cmp_yp_xm),
    Octant.MMP : cmp_to_key(__cmp_xm_ym),
    Octant.PMP : cmp_to_key(__cmp_ym_xp),
    Octant.PPM : cmp_to_key(__cmp_xp_yp),
    Octant.MPM : cmp_to_key(__cmp_yp_xm),
    Octant.MMM : cmp_to_key(__cmp_xm_ym),
    Octant.PMM : cmp_to_key(__cmp_ym_xp)
}

SIDE = {
    "PP" : ( Octant.PPP, Octant.PPM ),
    "MP" : ( Octant.MPP, Octant.MPM ),
    "PM" : ( Octant.PMP, Octant.PMM ),
    "MM" : ( Octant.MMP, Octant.MMM )
}

if __name__ == "__main__":
    manhattan_distance = 3
    # The following seem to follow from symmetry relative to the source Cube
    # > Conjecture 1 : CubeKind.ZZX yields the same outcomes as CubeKind.ZXZ
    # > Conjecture 2 : CubeKind.XXZ yields the same outcomes as CubeKind.XZX
    kinds = [ CubeKind.XZZ , CubeKind.ZXZ, CubeKind.ZZX, CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ ]
    sides = [ "PP", "MP", "MM", "PM" ]

    for target_kind in kinds:
        console.info(f"Target kind : {target_kind}")
        for target_side in sides:
            count = 1
            statistics: defaultdict[int, int] = defaultdict(int)
            overheads: defaultdict[Coordinates, int] = defaultdict(int)
            target_faces = SIDE[target_side]
            target_face_p, target_face_m = target_faces
            positions = set()
            positions.update(OctahedronHelper.get_face_positions(manhattan_distance, target_face_p))
            positions.update(OctahedronHelper.get_face_positions(manhattan_distance, target_face_m))
            for target_position in positions:
                overhead = VolumeFinder.get_path_overhead((target_kind, target_position))
                statistics[overhead] += 1
                overheads[target_position] = overhead

                count += 1
            percentage = 100.0 * statistics[0] / len(positions)
            console.info(f"{target_side}> Zero-overhead percentage : {percentage:.2f}% [{statistics}]")
            __layout_overheads(target_faces, manhattan_distance, overheads)