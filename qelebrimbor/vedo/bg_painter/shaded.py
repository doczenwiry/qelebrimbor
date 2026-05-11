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

from numpy import array

from qelebrimbor.core.zx.attributes import NodeType
from qelebrimbor.core.components import BgCube
from qelebrimbor.vedo.bg_painter.abstract import BlockGraphPainter
from qelebrimbor.vedo.zx_palette import ZxPalette


class ShadedBlockGraphPainter(BlockGraphPainter):
    @staticmethod
    def __query_color(cube: BgCube, f: int):
        cube_type = cube.kind.get_type()
        face_type = NodeType[cube.kind.name[f // 2]]
        return ZxPalette.get_major(cube_type) if face_type == cube_type else ZxPalette.get_minor(cube_type)

    @staticmethod
    def get_cube_colors(cube: BgCube):
        return array([ ShadedBlockGraphPainter.__query_color(cube, f) for f in range(6) ])

    @staticmethod
    def get_pipe_colors(source: BgCube, target: BgCube):
        # cellcolors are for faces (+X, -X, +Y, -Y, +Z, -Z)
        colors = []
        distances = target.position - source.position
        for c in range(3):
            color = ZxPalette.LGRAY
            if distances[c] == 0:
                if source.kind == target.kind:
                    color = ZxPalette.get_minor(source.kind.get_type())
                else:
                    color = ZxPalette.LGRAY
            colors.append(color)
            colors.append(color)
        return colors
