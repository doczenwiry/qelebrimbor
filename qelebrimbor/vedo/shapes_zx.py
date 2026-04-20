from vedo import Assembly, Disc, Line, Text3D, Box  # type: ignore[import-untyped]

from qelebrimbor.common.components import ZxNode, ZxEdge
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.vedo.coloring.zx_palette import ZxPalette

from logging import getLogger
console = getLogger(__name__)

SPACING_X = 6.0
SPACING_Y = 6.0

class VdNode(Assembly):
    def __init__(self, node: ZxNode, placement: tuple[float, float]):
        super().__init__()

        self.zx_node: ZxNode = node

        console.debug(f"ZxNode : {node} [{placement}]")

        disc_position = (SPACING_X * placement[0], SPACING_Y * placement[1], 0.00)
        text_position = (SPACING_X * placement[0], SPACING_Y * placement[1], 0.05)
        radius = 1.0 if node.type != NodeType.O else 0.75
        color = ZxPalette.get_major(node.type)

        self.__disc = Disc(pos = disc_position, r1 = 0.0, r2 = radius, c = color).z(0.01)
        self.add( self.__disc )

        self.__background = Disc(pos = disc_position, r1 = 0.0, r2 = 1.30 * radius, c = 'white')
        self.add( self.__background )

        self.__text = Text3D(str(node.id), s = radius, pos = text_position, font = 'Calco', justify = 'centered', c = 'white').z(0.02)
        self.add( self.__text )

        self.alter_appearance(highlight = False)

    def alter_appearance(self, highlight: bool = False):
        color = 'teal5' if highlight else 'w'
        self.__background.color(color)

class VdEdge(Assembly):
    LENGTH = 3.00
    DIAMETER = 0.50

    def __init__(self,
            edge: ZxEdge, source_placement: tuple[float, float], target_placement: tuple[float, float]
    ):
        self.zx_edge: ZxEdge = edge

        color = 'k' if edge.type == EdgeType.IDENTITY else 'y4'

        source_position = Coordinates(SPACING_X * source_placement[0], SPACING_Y * source_placement[1],  0.05)
        target_position = Coordinates(SPACING_X * target_placement[0], SPACING_Y * target_placement[1], -0.05)

        # Create the line of this edge
        self.__edge = Line(p0 = source_position, p1 = target_position, lw = 8, c = color).z(0.01)

        console.debug(f"ZxEdge {edge.source}L{source_placement}@{source_position} - {edge.target}L{target_placement}@{target_position}")

        # Create the background of this edge for highlighting
        self.__background = Line(p0 = source_position, p1 = target_position, lw = 16, c = 'white')
        self.alter_appearance(highlight = False)

        super().__init__( self.__background, self.__edge )

    def alter_appearance(self, highlight: bool = False):
        color = 'teal5' if highlight else 'w' if self.zx_edge.type == EdgeType.IDENTITY else 'y4'
        self.__background.linecolor(color)