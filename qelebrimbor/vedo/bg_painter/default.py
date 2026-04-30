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

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.vedo.bg_painter.abstract import BlockGraphPainter
from qelebrimbor.vedo.zx_palette import ZxPalette


class DefaultBlockGraphPainter(BlockGraphPainter):
    @staticmethod
    def __query_color(cube: BgCube, f: int):
        face_type = NodeType[cube.kind.name[f // 2]]
        return ZxPalette.get_major(face_type) if face_type == cube.kind.get_type() else ZxPalette.get_minor(face_type)

    @staticmethod
    def get_cube_colors(cube: BgCube):
        return array([ DefaultBlockGraphPainter.__query_color(cube, f) for f in range(6) ])

    @staticmethod
    def get_pipe_colors(source: BgCube, target: BgCube):
        distances = target.position - source.position
        # cellcolors are for faces (+X, -X, +Y, -Y, +Z, -Z)
        colors = []
        for c in range(3):
            if distances[c] == 0 and (
                    source.kind not in [CubeKind.OOO, CubeKind.YYY] or target.kind not in [CubeKind.OOO, CubeKind.YYY]):
                color = source.kind.name[c] if source.kind not in [CubeKind.OOO, CubeKind.YYY] else target.kind.name[c]
            else:
                color = 'O'
            colors.append(ZxPalette.get_major(NodeType[color]))
            colors.append(ZxPalette.get_major(NodeType[color]))
        return colors
