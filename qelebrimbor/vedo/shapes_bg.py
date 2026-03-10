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

    def __init__(self, kind: CubeKind, position: Coordinates, node: NodeId = -1, cube: CubeId = -1):
        super().__init__()

        self.bg_cube: CubeId = cube
        self.__kind = kind
        self.__position = position

        # Scaling the position
        position = GLOBAL_SPACING_FACTOR * position

        # Parameters for the label
        label = str(node) if node != -1 else ""
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
        for direction in Spacetime.STEPS:
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
    LENGTH = GLOBAL_SPACING_FACTOR * 0.205
    DIAMETER = 0.25

    def __compute_pipe_colors(self):
        if self.pipe_type == EdgeType.IDENTITY:
            pass
        else:
            pass

    def __init__(self,
        source_kind: CubeKind, source_position: Coordinates,
        target_kind: CubeKind, target_position: Coordinates,
        pipe_type: EdgeType = EdgeType.IDENTITY,
        source: CubeId = -1, target: CubeId = -1
    ):
        super().__init__()

        self.bg_source: CubeId = source
        self.bg_target: CubeId = target
        self.pipe_type: EdgeType = pipe_type

        # Determine the position where the pipe will be placed
        distances = target_position - source_position
        position = GLOBAL_SPACING_FACTOR * (source_position + distances / 2.0)
        # Compute the measurements of this pipe (i.e. length, width, height) according to its direction
        measures = [
            GLOBAL_SPACING_FACTOR * (BgPipe.LENGTH if d != 0 else BgPipe.DIAMETER)
            for d in distances
        ]

        self.__pipe = Box(position, size = measures)
        self.__pipe.lighting('off')
        self.add(self.__pipe)

        colors = []
        distances = distances.as_tuple()
        for c in range(3):
            if distances[c] == 0:
                source_color = source_kind.name[c]
                target_color = target_kind.name[c]
                if source_color != 'O' and target_color != 'O' and source_color != target_color:
                    raise Exception(f"Incompatible cubes [{source_kind}/{target_kind}] [{distances}].")
                if source_color != 'O':
                    color = source_color
                elif target_color != 'O':
                    color = target_color
                else:
                    color = 'U'
            else:
                color = 'O'
            colors.append(COLOR_RGBS[color])
            colors.append(COLOR_RGBS[color])

        self.__pipe.cellcolors = colors

        self.__pipe.linecolor('k')
        self.__pipe.linewidth(3)

    def alter_appearance(self, highlight: bool = False):
        if highlight:
            self.__pipe.linecolor('k5')
            self.__pipe.linewidth(6)
        else:
            self.__pipe.linecolor('k')
            self.__pipe.linewidth(3)

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