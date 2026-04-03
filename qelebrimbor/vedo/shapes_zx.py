from vedo import Assembly, Disc, Line, Text3D, Box

from qelebrimbor.common.components_zx import NodeId, NodeType, EdgeType
from qelebrimbor.common.coordinates import Coordinates

from qelebrimbor.vedo.color_scheme import COLOR_NAMES

from logging import getLogger
console = getLogger(__name__)

SPACING_X = 6.0
SPACING_Y = 6.0

class ZxNode(Assembly):
    def __init__(self, node: NodeId, node_type: NodeType, placement: tuple[float, float]):
        self.zx_node = node

        disc_position = (SPACING_X * placement[0], SPACING_Y * placement[1], 0.00)
        text_position = (SPACING_X * placement[0], SPACING_Y * placement[1], 0.05)
        radius = 1.0 if node_type != NodeType.O else 0.75
        color = COLOR_NAMES[ node_type.name ]

        self.__disc = Disc(pos = disc_position, r1 = 0.0, r2 = radius, c = color)
        self.__background = Disc(pos = disc_position, r1 = 0.0, r2 = 1.15 * radius, c = 'white')
        self.__text = Text3D(str(node), pos = text_position, font = 'Calco', justify = 'centered', c = 'white')

        super().__init__( [ self.__background, self.__disc, self.__text ] )

        self.alter_appearance(highlight = False)

    def alter_appearance(self, highlight: bool = False):
        color = 'k5' if highlight else 'w'
        self.__background.color(color)

class ZxEdge(Assembly):
    LENGTH = 3.00
    DIAMETER = 0.50

    def __init__(self,
            source: NodeId, target: NodeId, edge_type: EdgeType,
            source_placement: tuple[float, float], target_placement: tuple[float, float]
    ):
        self.zx_source: NodeId = source
        self.zx_target: NodeId = target
        self.edge_type = edge_type

        color = 'k' if edge_type == EdgeType.IDENTITY else 'y4'

        source_position = Coordinates(SPACING_X * source_placement[0], SPACING_Y * source_placement[1],  0.05)
        target_position = Coordinates(SPACING_X * target_placement[0], SPACING_Y * target_placement[1], -0.05)

        # Create the line of this edge
        self.__edge = Line(p0 = source_position, p1 = target_position, lw = 5, c = color)

        console.debug(f"ZxEdge {source}L{source_placement}@{source_position} - {target}L{target_placement}@{target_position}")

        # Create the background of this edge for highlighting
        self.__background = Line(p0 = source_position, p1 = target_position, lw = 10, c = 'white', alpha = 0.0)
        self.alter_appearance(highlight = False)

        super().__init__( self.__background, self.__edge )

    def alter_appearance(self, highlight: bool = False):
        color = 'k5' if highlight else 'w' if self.edge_type == EdgeType.IDENTITY else 'y4'
        self.__background.linecolor(color)