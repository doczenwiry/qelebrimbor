from numpy import array
from vedo import Assembly, Cube, Box, Text3D  # type: ignore[import-untyped]

from qelebrimbor.common.components import BgCube
from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.common.attributes_bg import CubeId, CubeKind
from qelebrimbor.common.attributes_zx import NodeId, EdgeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.vedo.color_scheme import COLOR_RGBS

GLOBAL_SPACING_FACTOR = 3.0

class VdCube(Assembly):
    LARGE_CUBE = 1.00
    LARGE_TEXT = 0.50
    FACTOR_SMALLER = 0.75
    SMALL_CUBE = LARGE_CUBE * FACTOR_SMALLER
    SMALL_TEXT = LARGE_TEXT * FACTOR_SMALLER

    def __init__(self, cube: BgCube):
        super().__init__()

        self.bg_cube: BgCube = cube

        # Scaling the position
        position = GLOBAL_SPACING_FACTOR * cube.position

        # Parameters for the label
        label = str(cube.realised_node) if cube.realised_node != -1 else ''
        text_size = VdCube.LARGE_TEXT if cube.kind != CubeKind.OOO else VdCube.SMALL_TEXT
        step_scale = 0.55 if cube.kind != CubeKind.OOO else 0.55 * VdCube.FACTOR_SMALLER

        # Initialise the cube
        self.__cube = Cube(pos = position, side = VdCube.LARGE_CUBE if cube.kind != CubeKind.OOO else VdCube.SMALL_CUBE)
        # Assign colors to the six faces of the cube (i.e. +X,-X,+Y,-Y,+Z,-Z)
        self.__cube.cellcolors = array([ COLOR_RGBS[ cube.kind.name[f // 2] ] for f in range(6) ])
        self.__cube.linecolor('k')
        self.__cube.linewidth(3)
        self.__cube.lighting('off')

        self.add(self.__cube)

        # Initialise the labels (i.e. numbers on the cube if it corresponds to a ZX-node)
        self.__texts = []
        cube_kind_reach: Coordinates = cube.kind.get_reach()
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

class VdPipe(Assembly):
    PIPE_RING_LENGTH = 0.25
    HALF_PIPE_LENGTH = (GLOBAL_SPACING_FACTOR - VdCube.LARGE_CUBE) / 2.0 - (PIPE_RING_LENGTH / 2.0)
    DIAMETER = VdCube.LARGE_CUBE * 0.75

    @staticmethod
    def __prepare_pipe_colors(source: BgCube, target: BgCube, distances: Coordinates):
        # cellcolors are for faces (+X, -X, +Y, -Y, +Z, -Z)
        colors = []
        distances = distances.as_tuple()
        for c in range(3):
            if distances[c] == 0 and (
                    source.kind not in [CubeKind.OOO, CubeKind.YYY] or target.kind not in [CubeKind.OOO, CubeKind.YYY]):
                color = source.kind.name[c] if source.kind not in [CubeKind.OOO, CubeKind.YYY] else target.kind.name[c]
            else:
                color = 'U'
            colors.append(COLOR_RGBS[color])
            colors.append(COLOR_RGBS[color])
        return colors

    def __init__(self,
        source: BgCube, target: BgCube, pipe_type: EdgeType = EdgeType.IDENTITY
    ):
        super().__init__()

        self.bg_source: BgCube = source
        self.bg_target: BgCube = target

        distances = target.position - source.position

        if pipe_type == EdgeType.IDENTITY:
            # Construct the pipe
            self.__pipe = Box(
                pos = GLOBAL_SPACING_FACTOR * (source.position + distances / 2.0),
                size = [2.2 * VdPipe.HALF_PIPE_LENGTH if d != 0 else VdPipe.DIAMETER for d in distances]
            )
            self.add(self.__pipe)
            self.__pipe.cellcolors = VdPipe.__prepare_pipe_colors(source, target, distances)
        else:  # pipe_type == EdgeType.HADAMARD
            # Construct the pipe on the side of the source
            self.__pipe_source = Box(
                pos =GLOBAL_SPACING_FACTOR * (source.position + distances / 4.0) + (VdPipe.HALF_PIPE_LENGTH / 4.0) * distances,
                size = [VdPipe.HALF_PIPE_LENGTH if d != 0 else VdPipe.DIAMETER for d in distances]
            )
            self.__pipe_source.cellcolors = VdPipe.__prepare_pipe_colors(source, target, distances)
            self.add(self.__pipe_source)
            # Construct the pipe on the side of the target
            self.__pipe_target = Box(
                pos =GLOBAL_SPACING_FACTOR * (target.position - distances / 4.0) - (VdPipe.HALF_PIPE_LENGTH / 4.0) * distances,
                size = [VdPipe.HALF_PIPE_LENGTH if d != 0 else VdPipe.DIAMETER for d in distances]
            )
            self.__pipe_target.cellcolors = VdPipe.__prepare_pipe_colors(target, source, distances)
            self.add(self.__pipe_target)
            # Construct the ring representing the HADAMARD type of the pipe
            self.__pipe_type_ring = Box(
                pos = GLOBAL_SPACING_FACTOR * (source.position + distances / 2.0),
                size = [0.8 * VdPipe.PIPE_RING_LENGTH if d != 0 else VdPipe.DIAMETER for d in distances],
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