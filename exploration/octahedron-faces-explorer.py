import logging

from IPython.core.magics.ast_mod import mangle_all

from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS

logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)

from functools import cmp_to_key
from collections import defaultdict

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import Spacetime, Octant
from qelebrimbor.helpers.octahedron import OctahedronHelper

logging.getLogger('qelebrimbor.helpers').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.utilities').setLevel(logging.INFO)

MOVE_ABOVE = Spacetime.XM + Spacetime.ZP
MOVE_RIGHT = Spacetime.XM + Spacetime.YP

def __make_overhead_delimiter(face: Octant, z: int, header: bool = True):
    if z == 0:
        xd, yd, _ = face.value
        if header:
            hdr = 'X' if xd == yd else 'Y'
        else:
            hdr = 'Y' if xd == yd else 'X'
    elif abs(z) == manhattan_distance:
        hdr = 'Z'
    else:
        hdr = ' '

    return hdr

def __make_overheads_layout(
        face: Octant, manhattan_distance: int, overheads: defaultdict[Coordinates, int]
) -> dict[int, str]:
    if face.value.z == +1:
        # The face lies in the upper hemi-octahedron
        zs = range(manhattan_distance, -1, -1)
    elif face.value.z == -1:
        zs = range(0, -manhattan_distance-1, -1)
    else:
        raise ValueError("Z must be +1/-1 [upper/lower hemi-octahedron].")

    layout: dict[int, str] = {}
    for z in zs:
        oh_row = abs(z) * ' '
        current_row = filter(lambda p : p[0].z == z, overheads.items())
        for pos, oh in current_row:
            oh_row += f" {oh}"
        oh_row += abs(z) * ' '
        hdr = __make_overhead_delimiter(face, z, header = True)
        trl = __make_overhead_delimiter(face, z, header = False)
        layout[z] = f" {hdr} >{oh_row} < {trl} "
    return layout

def __show_layouts_sidebyside(
        target_face: Octant,
        overheads1: defaultdict[Coordinates, int],
        overheads2: defaultdict[Coordinates, int]
):
    if target_face.value.z == +1:
        # The face lies in the upper hemi-octahedron
        zs = range(manhattan_distance, -1, -1)
    elif target_face.value.z == -1:
        zs = range(0, -manhattan_distance - 1, -1)
    else:
        raise ValueError("Z must be +1/-1 [upper/lower hemi-octahedron].")

    layout1 = __make_overheads_layout(target_face, manhattan_distance, overheads1)
    layout2 = __make_overheads_layout(target_face, manhattan_distance, overheads2)

    for z in zs:
        console.info(f"{layout1[z]}   {layout2[z]}")

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
    manhattan_distance = 3
    # The following seem to follow from symmetry relative to the source Cube
    # > Conjecture 1 : CubeKind.ZZX yields the same outcomes as CubeKind.ZXZ up to symmetry
    # > Conjecture 2 : CubeKind.XXZ yields the same outcomes as CubeKind.XZX up to symmetry
    kinds = [ CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZZX, CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ ]
    faces = [ Octant.PPP ] #, Octant.PPM, Octant.MPP, Octant.MPM, Octant.MMP, Octant.MMM, Octant.PMP, Octant.PMM ]

    source_kind = CubeKind.XZZ
    source_position = Spacetime.ORIGIN
    source = (source_kind, source_position)

    console.info(f"Source : {source_kind}@{source_position}")
    for target_kind in kinds:
        console.info(f"Target kind : {target_kind} [Overheads: explored vs. computed]")
        for target_face in faces:
            count = 1
            statistics: defaultdict[int, int] = defaultdict(int)
            explored_overheads: defaultdict[Coordinates, int] = defaultdict(int)
            computed_overheads: defaultdict[Coordinates, int] = defaultdict(int)
            positions = sorted(OctahedronHelper.get_face_positions(manhattan_distance, target_face), key = SORTING_FUNCTIONS[target_face])
            for target_position in positions:
                explored_overhead, paths = PathFinderDFS.find_minimal_paths(final = (target_kind, target_position), start = source)
                statistics[explored_overhead] += 1
                explored_overheads[target_position] = explored_overhead
                computed_overheads[target_position] = paths[0].minimal_overhead_possible()

                count += 1
            percentage = 100.0 * statistics[0] / len(positions)
            __show_layouts_sidebyside(target_face, explored_overheads, computed_overheads)