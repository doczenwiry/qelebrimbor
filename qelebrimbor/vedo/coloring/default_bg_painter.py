from numpy import array

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.vedo.coloring.abstract import BlockGraphPainter
from qelebrimbor.vedo.coloring.zx_palette import ZxPalette


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
        distances = distances.as_tuple()
        for c in range(3):
            if distances[c] == 0 and (
                    source.kind not in [CubeKind.OOO, CubeKind.YYY] or target.kind not in [CubeKind.OOO, CubeKind.YYY]):
                color = source.kind.name[c] if source.kind not in [CubeKind.OOO, CubeKind.YYY] else target.kind.name[c]
            else:
                color = 'O'
            colors.append(ZxPalette.get_major(NodeType[color]))
            colors.append(ZxPalette.get_major(NodeType[color]))
        return colors
