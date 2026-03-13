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

def __layout_overheads(face: Octant, manhattan_distance: int, overheads: defaultdict[Coordinates, int]):
    if face.value.z == +1:
        # The face lies in the upper hemi-octahedron
        zs = range(manhattan_distance, -1, -1)
    elif face.value.z == -1:
        zs = range(0, -manhattan_distance-1, -1)
    else:
        raise ValueError("Z must be +1/-1 [upper/lower hemi-octahedron].")
    for z in zs:
        oh_row = abs(z) * ' '
        current_row = filter(lambda p : p[0].z == z, overheads.items())
        for pos, oh in current_row:
            oh_row += f" {oh}"
        hdr = __make_overhead_header(face, z)
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

if __name__ == "__main__":
    manhattan_distance = 6
    # The following seem to follow from symmetry relative to the source Cube
    # > Conjecture 1 : CubeKind.ZZX yields the same outcomes as CubeKind.ZXZ
    # > Conjecture 2 : CubeKind.XXZ yields the same outcomes as CubeKind.XZX
    kinds = [ CubeKind.XZZ ] #, CubeKind.ZXZ, CubeKind.ZZX, CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ ]
    faces = [ Octant.PPP, Octant.PPM, Octant.MPP, Octant.MPM, Octant.MMP, Octant.MMM, Octant.PMP, Octant.PMM ]

    for target_kind in kinds:
        console.info(f"Target kind : {target_kind}")
        for target_face in faces:
            count = 1
            statistics: defaultdict[int, int] = defaultdict(int)
            overheads: defaultdict[Coordinates, int] = defaultdict(int)
            positions = sorted(OctahedronHelper.get_face_positions(manhattan_distance, target_face), key = SORTING_FUNCTIONS[target_face])
            for target_position in positions:
                overhead = VolumeFinder.get_path_overhead((target_kind, target_position))
                statistics[overhead] += 1
                overheads[target_position] = overhead

                count += 1
            percentage = 100.0 * statistics[0] / len(positions)
            console.info(f"{target_face}> Zero-overhead percentage : {percentage:.2f}% [{statistics}]")
            __layout_overheads(target_face, manhattan_distance, overheads)