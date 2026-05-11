#   Copyright 2026 Seweryn Dynerowicz
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from typing import Iterable
from functools import cmp_to_key
from collections import defaultdict

from qelebrimbor.core.zx.attributes import EdgeType
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.coordinates import Coordinates

from qelebrimbor.helpers.calculator import ManhattanCalculator
from qelebrimbor.helpers.spacetime import SpacetimeHelper, Octant
from qelebrimbor.helpers.octahedron import OctahedronHelper

from qelebrimbor.spacetime.pathfinders.depth_first_search import PathfinderDFS

import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)
logging.getLogger('qelebrimbor').setLevel(logging.CRITICAL)

MOVE_ABOVE = SpacetimeHelper.XM + SpacetimeHelper.ZP
MOVE_RIGHT = SpacetimeHelper.XM + SpacetimeHelper.YP

def __make_overhead_delimiter(face: Octant, z: int, header: bool = True):
    if z == 0:
        xd, yd, _ = face.value
        if header:
            hdr = 'X' if xd == yd else 'Y'
        else:
            hdr = 'Y' if xd == yd else 'X'
    elif abs(z) == manhattan_distance_checked:
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

def __show_layouts(face: Octant, manhattan: int, *data: defaultdict[Coordinates, int]):
    if face.value.z == +1:
        # The face lies in the upper hemi-octahedron
        zs = range(manhattan, -1, -1)
    elif face.value.z == -1:
        zs = range(0, -manhattan - 1, -1)
    else:
        raise ValueError("Z must be +1/-1 [upper/lower hemi-octahedron].")

    layouts = []
    for overheads in data:
        layouts.append(__make_overheads_layout(face, manhattan, overheads))

    for z in zs:
        line = ""
        for layout in layouts:
            line += f"{layout[z]}   "
        console.info(line)

def __show_layouts_sidebyside(
        target_face: Octant,
        overheads1: defaultdict[Coordinates, int],
        overheads2: defaultdict[Coordinates, int]
):
    if target_face.value.z == +1:
        # The face lies in the upper hemi-octahedron
        zs = range(manhattan_distance_checked, -1, -1)
    elif target_face.value.z == -1:
        zs = range(0, -manhattan_distance_checked - 1, -1)
    else:
        raise ValueError("Z must be +1/-1 [upper/lower hemi-octahedron].")

    layout1 = __make_overheads_layout(target_face, manhattan_distance_checked, overheads1)
    layout2 = __make_overheads_layout(target_face, manhattan_distance_checked, overheads2)

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

def check_consistency(kinds: Iterable[CubeKind], faces: Iterable[Octant], manhattan_distance: int = 3):
    # The following seem to follow from symmetry relative to the source Cube
    # > Conjecture 1 : CubeKind.ZZX yields the same outcomes as CubeKind.ZXZ up to symmetry
    # > Conjecture 2 : CubeKind.XXZ yields the same outcomes as CubeKind.XZX up to symmetry
    source = BgCube(CubeKind.XZZ, SpacetimeHelper.ORIGIN)

    pathfinder = PathfinderDFS()
    inconsistencies = 0

    target_kinds = list(kinds)
    target_faces = list(faces)

    console.info(f"Source : {source}")
    console.info(f"Manhattan Distance: {manhattan_distance}")
    for target_kind in target_kinds:
        console.info(f"Target kind : {target_kind} [Overheads: explored vs. computed]")
        for target_face in target_faces:
            console.info(f"> Target face : {target_face}")
            count = 1
            statistics: defaultdict[int, int] = defaultdict(int)
            explored_overheads: defaultdict[Coordinates, int] = defaultdict(int)
            computed_overheads: defaultdict[Coordinates, int] = defaultdict(int)
            positions = sorted(OctahedronHelper.get_face_positions(manhattan_distance, target_face), key = SORTING_FUNCTIONS[target_face])
            for target_position in positions:
                target = BgCube(target_kind, target_position)
                path = pathfinder.find_optimum(source, target, EdgeType.IDENTITY)
                if path is None:
                    raise Exception(f"No path found between {source} and {target}")
                explored_overhead = path.overhead()
                statistics[explored_overhead] += 1
                explored_overheads[target_position] = explored_overhead
                computed_overheads[target_position] = ManhattanCalculator.minimal_manhattan_excess(source, target)

                count += 1

            __show_layouts_sidebyside(target_face, explored_overheads, computed_overheads)

            if explored_overheads != computed_overheads:
                for target_position in positions:
                    explored = explored_overheads[target_position]
                    computed = computed_overheads[target_position]
                    if explored != computed:
                        console.info(f"Inconsistency : {target_position} [relative:{target_position - source.position}]")
                        console.info(f"> Target relative octant : {target_face.value}")
                        console.info(f"> Source reach : {source.kind.get_reach()}")
                        console.info(f"> Explored : {explored_overheads[target_position]}")
                        console.info(f"> Computed : {computed_overheads[target_position]}")
                inconsistencies += 1

    console.info(f"INCONSISTENCIES : {inconsistencies}")

if __name__ == "__main__":
    manhattan_distance_checked = 6
    kinds_checked = [CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZZX, CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ]
    faces_checked = [Octant.PPP, Octant.PPM, Octant.MPP, Octant.MPM, Octant.MMP, Octant.MMM, Octant.PMP, Octant.PMM]

    check_consistency(kinds = kinds_checked, faces = faces_checked, manhattan_distance = manhattan_distance_checked)