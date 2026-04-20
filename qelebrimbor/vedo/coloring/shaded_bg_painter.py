from numpy import array

from qelebrimbor.common.attributes_zx import NodeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.vedo.coloring.abstract import BlockGraphPainter
from qelebrimbor.vedo.coloring.zx_palette import ZxPalette


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
        source_type = source.kind.get_type()
        target_type = target.kind.get_type()
        for c in range(3):
            color = ZxPalette.get_major(NodeType.O)
            if distances[c] == 0:
                if source_type == target_type:
                    color = ZxPalette.get_minor(source_type)
                else:
                    color = ZxPalette.BLACK
            colors.append(color)
            colors.append(color)
        return colors
