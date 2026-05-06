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

from vedo import Assembly, Disc, Line, Text3D, Box  # type: ignore[import-untyped]

from qelebrimbor.common.components import ZxNode, ZxEdge
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.vedo.zx_palette import ZxPalette

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
        radius = 1.00 if node.type != NodeType.O else 0.75
        radius *= 1.25
        color = ZxPalette.get_major(node.type)

        self.__disc = Disc(pos = disc_position, r1 = 0.0, r2 = radius, c = color).z(0.01)
        self.add( self.__disc )

        self.__background = Disc(pos = disc_position, r1 = 0.0, r2 = 1.40 * radius, c = 'white')
        self.add( self.__background )

        self.__node_id = Text3D(str(node.id), s = radius, pos = text_position, font ='Calco', justify ='centered', c ='white').z(0.02)
        self.add(self.__node_id)

    def alter_highlighting(self, color: str):
        self.__background.color(color)

class VdEdge(Assembly):
    LENGTH = 3.00
    DIAMETER = 0.50

    def __init__(self,
            edge: ZxEdge, source_placement: tuple[float, float], target_placement: tuple[float, float]
    ):
        super().__init__()
        self.zx_edge: ZxEdge = edge

        color = 'k' if edge.type == EdgeType.IDENTITY else 'y4'

        offset = 0.00
        if edge.source.layer == edge.target.layer:
            offset += 0.05

        source_position = Coordinates(SPACING_X * source_placement[0], SPACING_Y * source_placement[1], -0.05)
        target_position = Coordinates(SPACING_X * target_placement[0], SPACING_Y * target_placement[1], -0.05)

        # Create the line of this edge
        self.__edge = Line(p0 = source_position, p1 = target_position, lw = 8, c = color).z(offset + 0.01)
        self.add(self.__edge)

        console.debug(f"ZxEdge {edge.source}L{source_placement}@{source_position} - {edge.target}L{target_placement}@{target_position}")
        console.debug(f"> Manhattan Excess Volume : {edge.excess_volume}")

        # Create the Manhattan Excess annotation
        if edge.excess_volume > 0:
            excess_position = source_position
            if edge.source.qubit != -1 and edge.target.qubit != -1 and edge.source.qubit == edge.target.qubit:
                excess_position += Coordinates(2.0, 3.0, 0.0)
            elif edge.source.layer != -1 and edge.target.layer != -1 and edge.source.layer == edge.target.layer:
                excess_position += Coordinates(3.0, 2.0, 0.0)
            self.__manhattan_excess = Text3D(
                txt = f"+{edge.excess_volume}", s = 1, pos = excess_position,
                font = 'Roboto', depth = 5.0, justify = 'centered', c = 'black'
            ).z(0.5)
        else:
            self.__manhattan_excess = None

        # Create the background of this edge for highlighting
        self.__background = Line(p0 = source_position, p1 = target_position, lw = 16, c = 'white').z(offset + 0.005)
        self.add(self.__background)

    def toggle_excess_volume(self, shown: bool = False):
        if self.__manhattan_excess:
            if shown:
                self.add(self.__manhattan_excess)
                self.__background.linecolor('red6')
            else:
                self.remove(self.__manhattan_excess)
                self.__background.linecolor('white')

    def alter_highlighting(self, color: str):
        self.__background.linecolor(color)