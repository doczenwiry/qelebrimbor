from vedo import Assembly, Cube, Box, Text3D  # type: ignore[import-untyped]

from qelebrimbor.vedo.coloring.abstract import BlockGraphPainter
from qelebrimbor.vedo.coloring.default_bg_painter import DefaultBlockGraphPainter
from qelebrimbor.vedo.coloring.shaded_bg_painter import ShadedBlockGraphPainter

from qelebrimbor.common.components import BgCube
from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.coordinates import Coordinates

from logging import getLogger
console = getLogger(__name__)

GLOBAL_SPACING_FACTOR = 3.0

class VdCube(Assembly):
    LARGE_CUBE = 1.00
    LARGE_TEXT = 0.50
    FACTOR_SMALLER = 0.75
    SMALL_CUBE = LARGE_CUBE * FACTOR_SMALLER
    SMALL_TEXT = LARGE_TEXT * FACTOR_SMALLER

    def __init__(self, cube: BgCube, painter: BlockGraphPainter = DefaultBlockGraphPainter()):
        super().__init__()

        self.bg_cube: BgCube = cube

        console.debug(f"BgCube : {cube}")

        # Scaling the position
        position = GLOBAL_SPACING_FACTOR * cube.position

        # Parameters for the label
        label = str(cube.realised_node) if cube.realised_node != -1 else ''
        text_size = VdCube.LARGE_TEXT if cube.kind != CubeKind.OOO else VdCube.SMALL_TEXT
        step_scale = 0.55 if cube.kind != CubeKind.OOO else 0.55 * VdCube.FACTOR_SMALLER

        # Initialise the cube
        self.__cube = Cube(pos = position, side = VdCube.LARGE_CUBE if cube.kind != CubeKind.OOO else VdCube.SMALL_CUBE)
        # Assign colors to the six faces of the cube (i.e. +X,-X,+Y,-Y,+Z,-Z)
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

        self.paint(painter)

        self.__highlighted = False

    def paint(self, painter: BlockGraphPainter):
        self.__cube.cellcolors = painter.get_cube_colors(self.bg_cube)

    def alter_appearance(self, highlight: bool = False):
        if highlight:
            self.__cube.linecolor('teal5')
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

    def __init__(self,
         source: BgCube, target: BgCube,
         pipe_type: EdgeType = EdgeType.IDENTITY,
         painter: BlockGraphPainter = DefaultBlockGraphPainter()
    ):
        super().__init__()

        console.debug(f"BgPipe : {source} -{pipe_type.name[0]}- {target}")

        self.bg_source: BgCube = source
        self.bg_target: BgCube = target
        self.pipe_type: EdgeType = pipe_type

        distances = target.position - source.position

        if pipe_type == EdgeType.IDENTITY:
            # Construct the pipe
            self.__pipe = Box(
                pos = GLOBAL_SPACING_FACTOR * (source.position + distances / 2.0),
                size = [2.2 * VdPipe.HALF_PIPE_LENGTH if d != 0 else VdPipe.DIAMETER for d in distances]
            )
            self.add(self.__pipe)
        else:  # pipe_type == EdgeType.HADAMARD
            # Construct the pipe on the side of the source
            self.__pipe_source = Box(
                pos =GLOBAL_SPACING_FACTOR * (source.position + distances / 4.0) + (VdPipe.HALF_PIPE_LENGTH / 4.0) * distances,
                size = [VdPipe.HALF_PIPE_LENGTH if d != 0 else VdPipe.DIAMETER for d in distances]
            )
            self.add(self.__pipe_source)
            # Construct the pipe on the side of the target
            self.__pipe_target = Box(
                pos =GLOBAL_SPACING_FACTOR * (target.position - distances / 4.0) - (VdPipe.HALF_PIPE_LENGTH / 4.0) * distances,
                size = [VdPipe.HALF_PIPE_LENGTH if d != 0 else VdPipe.DIAMETER for d in distances]
            )
            self.add(self.__pipe_target)
            # Construct the ring representing the HADAMARD type of the pipe
            self.__pipe_type_ring = Box(
                pos = GLOBAL_SPACING_FACTOR * (source.position + distances / 2.0),
                size = [0.8 * VdPipe.PIPE_RING_LENGTH if d != 0 else VdPipe.DIAMETER for d in distances],
                c = 'k' if EdgeType.IDENTITY else 'y'
            )
            self.add(self.__pipe_type_ring)

        for mesh in self.objects:
            mesh.lighting('off')
            mesh.linecolor('k')
            mesh.linewidth(3)

        self.paint(painter)

    def paint(self, painter: BlockGraphPainter):
        if self.pipe_type == EdgeType.IDENTITY:
            self.__pipe.cellcolors = painter.get_pipe_colors(self.bg_source, self.bg_target)
        else:
            self.__pipe_source.cellcolors = painter.get_pipe_colors(self.bg_source, self.bg_target)
            self.__pipe_target.cellcolors = painter.get_pipe_colors(self.bg_target, self.bg_source)

    def alter_appearance(self, highlight: bool = False):
        color = 'teal5' if highlight else 'k'
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