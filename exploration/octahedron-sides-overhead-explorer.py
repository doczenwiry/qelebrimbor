import logging

from qelebrimbor.pathfinders.path import Path
from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS

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

def __make_overhead_delimiter(face: Octant, z: int, header: bool = True):
    if z == 0:
        xd, yd, zd = face.value
        # if header:
        hdr = f" {__convert_direction("X", xd) if xd == yd else __convert_direction("Y", yd)} "
        # else:
        #     hdr = f"{__convert_direction("Y", yd) if xd == yd else __convert_direction("X", xd)}"
    elif z == manhattan_distance:
        hdr = " ZP "
    elif z == -manhattan_distance:
        hdr = " ZM "
    else:
        hdr = "    "

    return hdr

def __make_overheads_layout(
        faces: tuple[Octant, Octant],
        manhattan_distance: int,
        overheads: defaultdict[Coordinates, int]
):
    target_face = faces[0]
    layout = {}
    for z in range(manhattan_distance, -manhattan_distance-1, -1):
        oh_row  = abs(z) * ' '
        current_row = sorted(filter(lambda p : p.z == z, overheads.keys()), key = SORTING_FUNCTIONS[target_face])
        for pos in current_row:
            oh = overheads[pos]
            oh_row += f" {oh}"
        oh_row += abs(z) * ' '
        hdr = __make_overhead_delimiter(faces[0], z, header = True)
        layout[z] = f"{hdr}>   {oh_row}   <"
    return layout

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
    "PM" : ( Octant.PMP, Octant.PMM ),
    "MP" : ( Octant.MPP, Octant.MPM ),
    "MM" : ( Octant.MMP, Octant.MMM )
}

if __name__ == "__main__":
    manhattan_distance = 3
    # The following seem to follow from symmetry relative to the source Cube
    # > Conjecture 1 : CubeKind.ZZX yields the same outcomes as CubeKind.ZXZ up to symmetry
    # > Conjecture 2 : CubeKind.XXZ yields the same outcomes as CubeKind.XZX up to symmetry
    kinds = [ CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZZX, CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ ]
    sides = [ "PP", "MP", "MM", "PM" ]

    source_kind = CubeKind.XZZ
    source_position = Spacetime.ORIGIN
    source = (source_kind, source_position)
    console.info(f"Source kind : {source_kind}@{source_position}")
    console.info(f"> Manhattan Distance : {manhattan_distance}")

    for target_kind in kinds:
        console.info(f"Target kind : {target_kind}")
        target_side_layouts = {}
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
                target = (target_kind, target_position)
                minimal_overhead = Path.minimal_overhead_possible(source, target)
                statistics[minimal_overhead] += 1
                overheads[target_position] = minimal_overhead

                count += 1
            percentage = 100.0 * statistics[0] / len(positions)
            target_side_layouts[target_side] = __make_overheads_layout(target_faces, manhattan_distance, overheads)

        for z in range(manhattan_distance, -manhattan_distance-1, -1):
            rows = ""
            for s in sides:
                rows += f"{target_side_layouts[s][z]}"
            console.info(rows)
        console.info("")