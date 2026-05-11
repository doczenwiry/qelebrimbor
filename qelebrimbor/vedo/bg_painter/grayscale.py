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

from vedo import get_color  # type: ignore[import-untyped]
from numpy import array

from qelebrimbor.core.zx.attributes import NodeType
from qelebrimbor.core.components import BgCube
from qelebrimbor.vedo.bg_painter.abstract import BlockGraphPainter


class GrayscaleBlockGraphPainter(BlockGraphPainter):
    NAUGHT = [ 255 * c for c in get_color(rgb='white') ]
    BRIGHT = [ 255 * c for c in get_color(rgb='k5') ]
    SHADED = [ 255 * c for c in get_color(rgb='k2') ]

    @staticmethod
    def __convert_color(node_type: NodeType):
        if node_type is NodeType.X:
            return GrayscaleBlockGraphPainter.SHADED
        elif node_type is NodeType.Z:
            return GrayscaleBlockGraphPainter.BRIGHT
        else:
            return GrayscaleBlockGraphPainter.NAUGHT

    @staticmethod
    def __query_color(cube: BgCube, f: int):
        return GrayscaleBlockGraphPainter.__convert_color(NodeType[cube.kind.name[f // 2]])

    @staticmethod
    def get_cube_colors(cube: BgCube):
        return array([GrayscaleBlockGraphPainter.__query_color(cube, f) for f in range(6)])

    @staticmethod
    def get_pipe_colors(source: BgCube, target: BgCube):
        distances = target.position - source.position
        # cellcolors are for faces (+X, -X, +Y, -Y, +Z, -Z)
        colors = []
        source_type = source.kind.get_type()
        target_type = target.kind.get_type()
        for c in range(3):
            face_type = NodeType.O
            if distances[c] == 0:
                if source_type not in [ NodeType.O, NodeType.Y ]:
                    face_type = NodeType[source.kind.name[c]]
                elif target_type not in [ NodeType.O, NodeType.Y ]:
                    face_type = NodeType[target.kind.name[c]]
            colors.append(GrayscaleBlockGraphPainter.__convert_color(face_type))
            colors.append(GrayscaleBlockGraphPainter.__convert_color(face_type))
        return colors
