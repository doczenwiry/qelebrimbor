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

from vedo import Assembly, Cube, Box, Text3D  # type: ignore[import-untyped]

from qelebrimbor.core.zx.attributes import NodeType
from qelebrimbor.helpers.spacetime import SpacetimeHelper

from numpy import array

from logging import getLogger

from qelebrimbor.vedo.zx_palette import ZxPalette

console = getLogger(__name__)

class VdCubeReference(Assembly):
    LARGE_CUBE = 1.00

    def __init__(self):
        super().__init__()

        # Initialise the cube
        self.__cube = Cube(pos = (0,0,0), side = 1.00)
        # Assign colors to the six faces of the cube (i.e. +X,-X,+Y,-Y,+Z,-Z)
        self.__cube.linecolor('k')
        self.__cube.linewidth(3)
        self.__cube.lighting('off')

        self.add(self.__cube)

        # Initialise the labels (i.e. numbers on the cube if it corresponds to a ZX-node)
        self.__texts = []
        for label, direction in [('X', SpacetimeHelper.XP), ('X', SpacetimeHelper.XM) , ('Y', SpacetimeHelper.YP), ('Y', SpacetimeHelper.YM) , ('Z', SpacetimeHelper.ZP) , ('Z', SpacetimeHelper.ZM)]:
            face_center = (0.55 * direction)
            text = Text3D(txt = label, pos = face_center, s = 0.5, font ='Roboto', justify ='centered', c ='white')
            # Rotate the text to line it up with its face
            rotation_axis = SpacetimeHelper.ZP.cross(direction)
            text.rotate(angle = 90.0, axis = rotation_axis, point = face_center)
            # Rotate the text to line it up with the top (resp. bottom) in the plus (resp. minus) direction
            if   direction == SpacetimeHelper.XP: rotation_angle =  90.0
            elif direction == SpacetimeHelper.XM: rotation_angle = -90.0
            elif direction == SpacetimeHelper.YP: rotation_angle = 180.0
            else: # direction in [Spacetime.YM, Spacetime.ZP, Spacetime.ZM]
                rotation_angle = 0.0

            text.rotate(angle = rotation_angle, axis = direction, point = face_center)
            self.__texts.append(text)
            self.add(text)

        self.__cube.cellcolors = array([
            ZxPalette.get_major(f) for f in [NodeType.X, NodeType.X, NodeType.Y, NodeType.Y, NodeType.Z, NodeType.Z]
        ])

    def __repr__(self):
        return str(self)

    def __str__(self):
        stringed = ""
        if self.bg_cube != -1:
            stringed += f"#{self.bg_cube}:"
        stringed += f"{self.__kind}@{self.__position}"
        return stringed