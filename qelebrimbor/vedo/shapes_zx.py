from vedo import Assembly, Disc, Line, Text3D, Box

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_zx import NodeId, NodeType, EdgeType
from qelebrimbor.common.coordinates import Coordinates

from qelebrimbor.vedo.color_scheme import COLOR_NAMES

from logging import getLogger
console = getLogger(__name__)

QUBIT_SPACING = 6.0
LAYER_SPACING = 6.0

class ZxNode(Assembly):
    def __init__(self, node: NodeId, anx: AugmentedZxGraph):
        self.zx_node = node

        node_type = anx.get_node_type(node)
        qubit = anx.get_qubit(node)
        layer = anx.get_node_layer(node)

        disc_position = (LAYER_SPACING * layer, QUBIT_SPACING * qubit, 0.00)
        text_position = (LAYER_SPACING * layer, QUBIT_SPACING * qubit, 0.05)
        radius = 1.0 if node_type != NodeType.O else 0.75
        color = COLOR_NAMES[ node_type.name ]

        self.__disc = Disc(pos = disc_position, r1 = 0.0, r2 = radius, c = color)
        self.__background = Disc(pos = disc_position, r1 = 0.0, r2 = 1.15 * radius, c = 'white')
        self.__disc_highlight = Disc(pos = text_position, r1 = 0.8 * radius, r2 = radius - 0.05, c = COLOR_NAMES[ 'highlighted' ])
        self.__text = Text3D(str(node), pos = text_position, font = 'Calco', justify = 'centered', c = 'white')

        super().__init__( [ self.__background, self.__disc, self.__disc_highlight, self.__text ] )

        # self.__highlighted = False
        self.alter_appearance(highlight = False)

    def alter_appearance(self, highlight: bool = False):
        if highlight: self.__disc_highlight.alpha(1.0)
        else: self.__disc_highlight.alpha(0.0)

    def show_label(self): self.__text.alpha(1.0)
    def hide_label(self): self.__text.alpha(0.0)

# Replace line with a Box
class ZxEdge(Assembly):
    LENGTH = 3.00
    DIAMETER = 0.50

    def __init__(self, source: NodeId, target: NodeId, anx: AugmentedZxGraph):

        self.zx_source: NodeId = source
        self.zx_target: NodeId = target
        self.edge_type = anx.get_edge_type(source, target)

        source_qubit = anx.get_qubit(source)
        source_layer = anx.get_node_layer(source)
        target_qubit = anx.get_qubit(target)
        target_layer = anx.get_node_layer(target)
        edge_type = anx.get_edge_type(source, target)

        color = 'k' if edge_type == EdgeType.IDENTITY else 'y4'

        source_position = Coordinates(LAYER_SPACING * source_layer, QUBIT_SPACING * source_qubit,  0.05)
        target_position = Coordinates(LAYER_SPACING * target_layer, QUBIT_SPACING * target_qubit, -0.05)

        distances = target_position - source_position
        position = source_position + distances / 2.0
        # Compute the measurements of this pipe (i.e. length, width, height) according to its direction
        measures = [ abs(d) if d != 0 else ZxEdge.DIAMETER for d in distances ]
        self.__edge = Box(pos = position.as_tuple(), size = measures, c = color)

        console.debug(f"ZxEdge {source}L{source_layer}@{source_position} - {target}L{target_layer}@{target_position} : {measures} / {distances}")

        measures = [ abs(d) if d != 0 else 1.25 * ZxEdge.DIAMETER for d in distances ]
        self.__background = Box(pos = position.as_tuple(), size = measures, c = 'white')

        self.alter_appearance(highlight = False)

        super().__init__( self.__background, self.__edge )

    def alter_appearance(self, highlight: bool = False):
        if highlight:
            self.__edge.linecolor('k5')
            self.__edge.linewidth(6)
        else:
            self.__edge.linecolor('k' if self.edge_type == EdgeType.IDENTITY else 'y4')
            self.__edge.linewidth(3)