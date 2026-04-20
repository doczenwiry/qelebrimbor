from vedo import get_color  # type: ignore[import-untyped]

from qelebrimbor.common.attributes_zx import NodeType

class ZxPalette:
    BLACK = [ 255 * c for c in get_color(rgb='black')]
    LGRAY = [ 255 * c for c in get_color(rgb='k5')]
    DGRAY = [ 255 * c for c in get_color(rgb='k2')]
    WHITE = [ 255 * c for c in get_color(rgb='white')]

    MAJOR_COLORS = {
        NodeType.O: [255 * c for c in get_color(rgb='k2')],
        NodeType.X: [255 * c for c in get_color(rgb='r5')],
        NodeType.Y: [255 * c for c in get_color(rgb='g5')],
        NodeType.Z: [255 * c for c in get_color(rgb='b5')]
    }

    MINOR_COLORS = {
        NodeType.O: [255 * c for c in get_color(rgb='k4')],
        NodeType.X: [255 * c for c in get_color(rgb='r4')],
        NodeType.Y: [255 * c for c in get_color(rgb='g4')],
        NodeType.Z: [255 * c for c in get_color(rgb='b4')]
    }

    @staticmethod
    def get_major(node_type: NodeType):
        return ZxPalette.MAJOR_COLORS[node_type]

    @staticmethod
    def get_minor(node_type: NodeType):
        return ZxPalette.MINOR_COLORS[node_type]