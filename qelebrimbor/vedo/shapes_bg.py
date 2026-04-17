from typing import Iterable

from numpy import array
from vedo import Assembly, Cube, Box, Text3D

from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.common.components_bg import CubeId, CubeKind
from qelebrimbor.common.components_zx import NodeId, EdgeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.vedo.color_scheme import COLOR_RGBS

GLOBAL_SPACING_FACTOR = 3.0

class BgCube(Assembly):
    LARGE_CUBE = 1.00
    LARGE_TEXT = 0.50
    FACTOR_SMALLER = 0.75
    SMALL_CUBE = LARGE_CUBE * FACTOR_SMALLER
    SMALL_TEXT = LARGE_TEXT * FACTOR_SMALLER

    def __init__(self, cube: CubeId, kind: CubeKind, position: Coordinates, realised_node: NodeId):
        super().__init__()

        self.bg_cube: CubeId = cube
        self.__kind = kind
        self.__position = position

        # Scaling the position
        position = GLOBAL_SPACING_FACTOR * position

        # Parameters for the label
        label = str(realised_node) if realised_node != -1 else ''
        text_size = BgCube.LARGE_TEXT if kind != CubeKind.OOO else BgCube.SMALL_TEXT
        step_scale = 0.55 if kind != CubeKind.OOO else 0.55 * BgCube.FACTOR_SMALLER

        # Initialise the cube
        self.__cube = Cube(pos = position, side = BgCube.LARGE_CUBE if kind != CubeKind.OOO else BgCube.SMALL_CUBE)
        # Assign colors to the six faces of the cube (i.e. +X,-X,+Y,-Y,+Z,-Z)
        self.__cube.cellcolors = array([ COLOR_RGBS[ kind.name[f // 2] ] for f in range(6) ])
        self.__cube.linecolor('k')
        self.__cube.linewidth(3)
        self.__cube.lighting('off')

        self.add(self.__cube)

        # Initialise the labels (i.e. numbers on the cube if it corresponds to a ZX-node)
        self.__texts = []
        cube_kind_reach: Coordinates = kind.get_reach()
        for direction in [ cube_kind_reach , Spacetime.ORIGIN - cube_kind_reach ]:
            face_center = (position + step_scale * direction).as_tuple()
            text = Text3D(txt = label, pos = face_center, s = text_size, font ='Roboto', justify ='centered', c ='white')
            # Rotate the text to line it up with its face
            rotation_axis = Spacetime.ZP.cross(direction).as_tuple()
            text.rotate(angle = 90.0, axis = rotation_axis, point = face_center)
            # Rotate the text to line it up with the top (resp. bottom) in the plus (resp. minus) direction
            if   direction == Spacetime.XP: rotation_angle =  90.0
            elif direction == Spacetime.XM: rotation_angle = -90.0
            elif direction == Spacetime.YP: rotation_angle = 180.0
            else: # direction in [Spacetime.YM, Spacetime.ZP, Spacetime.ZM]
                rotation_angle = 0.0

            text.rotate(angle = rotation_angle, axis = direction.as_tuple(), point = face_center)
            self.__texts.append(text)
            self.add(text)

        self.__highlighted = False

    def alter_appearance(self, highlight: bool = False):
        if highlight:
            self.__cube.linecolor('k5')
            self.__cube.linewidth(6)
        else:
            self.__cube.linecolor('k')
            self.__cube.linewidth(3)

    def __repr__(self):
        return str(self)

    def __str__(self):
        stringed = ""
        if self.bg_cube != -1:
            stringed += f"#{self.bg_cube}:"
        stringed += f"{self.__kind}@{self.__position}"
        return stringed

class BgPipe(Assembly):
    PIPE_RING_LENGTH = 0.25
    HALF_PIPE_LENGTH = (GLOBAL_SPACING_FACTOR - BgCube.LARGE_CUBE) / 2.0 - (PIPE_RING_LENGTH / 2.0)
    DIAMETER = BgCube.LARGE_CUBE * 0.75

    @staticmethod
    def __prepare_pipe_colors(kind: CubeKind, other_kind: CubeKind, distances: Coordinates):
        # cellcolors are for faces (+X, -X, +Y, -Y, +Z, -Z)
        colors = []
        distances = distances.as_tuple()
        for c in range(3):
            if distances[c] == 0 and (
                    kind not in [CubeKind.OOO, CubeKind.YYY] or other_kind not in [CubeKind.OOO, CubeKind.YYY]):
                color = kind.name[c] if kind not in [CubeKind.OOO, CubeKind.YYY] else other_kind.name[c]
            else:
                color = 'U'
            colors.append(COLOR_RGBS[color])
            colors.append(COLOR_RGBS[color])
        return colors

    def __init__(self,
        source_kind: CubeKind, source_position: Coordinates,
        target_kind: CubeKind, target_position: Coordinates,
        pipe_type: EdgeType = EdgeType.IDENTITY,
        source: CubeId = -1, target: CubeId = -1
    ):
        super().__init__()

        self.bg_source: CubeId = source
        self.bg_target: CubeId = target

        distances = target_position - source_position

        if pipe_type == EdgeType.IDENTITY:
            # Construct the pipe
            self.__pipe = Box(
                pos = GLOBAL_SPACING_FACTOR * (source_position + distances / 2.0),
                size = [2.2 * BgPipe.HALF_PIPE_LENGTH if d != 0 else BgPipe.DIAMETER for d in distances]
            )
            self.add(self.__pipe)
            self.__pipe.cellcolors = BgPipe.__prepare_pipe_colors(source_kind, target_kind, distances)
        else:  # pipe_type == EdgeType.HADAMARD
            # Construct the pipe on the side of the source
            self.__pipe_source = Box(
                pos = GLOBAL_SPACING_FACTOR * (source_position + distances / 4.0) + (BgPipe.HALF_PIPE_LENGTH / 4.0) * distances,
                size = [BgPipe.HALF_PIPE_LENGTH if d != 0 else BgPipe.DIAMETER for d in distances]
            )
            self.__pipe_source.cellcolors = BgPipe.__prepare_pipe_colors(source_kind, target_kind, distances)
            self.add(self.__pipe_source)
            # Construct the pipe on the side of the target
            self.__pipe_target = Box(
                pos = GLOBAL_SPACING_FACTOR * (target_position - distances / 4.0) - (BgPipe.HALF_PIPE_LENGTH / 4.0) * distances,
                size = [BgPipe.HALF_PIPE_LENGTH if d != 0 else BgPipe.DIAMETER for d in distances]
            )
            self.__pipe_target.cellcolors = BgPipe.__prepare_pipe_colors(target_kind, source_kind, distances)
            self.add(self.__pipe_target)
            # Construct the ring representing the HADAMARD type of the pipe
            self.__pipe_type_ring = Box(
                pos = GLOBAL_SPACING_FACTOR * (source_position + distances / 2.0),
                size = [0.8 * BgPipe.PIPE_RING_LENGTH if d != 0 else BgPipe.DIAMETER for d in distances],
                c = 'y'
            )
            self.add(self.__pipe_type_ring)

        for mesh in self.objects:
            mesh.lighting('off')
            mesh.linecolor('k')
            mesh.linewidth(3)

    def alter_appearance(self, highlight: bool = False):
        color = 'k5' if highlight else 'k'
        width = 6 if highlight else 3

        for mesh in self.objects:
            mesh.linecolor(color)
            mesh.linewidth(width)

    def __repr__(self):
        return str(self)

    def __str__(self):
        stringed = ""
        if self.bg_source != -1:
            stringed += f"{self.bg_source}"
        stringed += "-"
        if self.bg_target != -1:
            stringed += f"{self.bg_target}"
        return stringed