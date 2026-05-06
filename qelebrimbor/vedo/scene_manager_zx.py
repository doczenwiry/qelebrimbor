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

from vedo.plotter import Plotter  # type: ignore[import-untyped]

from qelebrimbor.common.attributes_zx import NodeId
from qelebrimbor.common.components import ZxNode, ZxEdge
from qelebrimbor.vedo.shapes_zx import VdNode, VdEdge
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout

from qelebrimbor.common.attributes_zx import EdgeId
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from logging import getLogger
console = getLogger(__name__)

class ZxSceneManager:
    def __init__(self, graph: VolumetricZxGraph, plotter: Plotter, layout: ZxLayout):
        self.__plotter = plotter
        self.__vzx_graph = graph

        self.__nodes: dict[ZxNode, VdNode] = dict()
        self.__edges: dict[ZxEdge, VdEdge] = dict()

        # Prepare all the elements for the ZX scene (i.e. nodes and edges)
        for node in graph.get_zx_nodes():
            vd_node = VdNode(node, layout.get_node_placement(node)).z(+0.1)
            self.__nodes[ node ] = vd_node
            self.__plotter.add( vd_node )

        for edge in graph.get_zx_edges():
            vd_edge = VdEdge(
                edge, layout.get_node_placement(edge.source), layout.get_node_placement(edge.target)
            ).z(-0.1)
            self.__edges[ edge ] = vd_edge
            self.__plotter.add( vd_edge )

        self.__selected_object = None
        self.__highlight_unrealised = True
        self.__show_manhattan_excess = False
        self.toggle_unrealised_appearance()

    def toggle_unrealised_appearance(self):
        self.__highlight_unrealised = not self.__highlight_unrealised

        unrealised_color = 'red6' if self.__highlight_unrealised else 'white'
        realised_color = 'green6' if self.__highlight_unrealised else 'white'

        for node in self.__vzx_graph.get_zx_nodes():
            if node.is_realised():
                self.__nodes[node].alter_highlighting(realised_color)
            else:
                self.__nodes[node].alter_highlighting(unrealised_color)

        for edge in self.__vzx_graph.get_zx_edges():
            if edge.is_realised():
                self.__edges[edge].alter_highlighting(realised_color)
            else:
                self.__edges[edge].alter_highlighting(unrealised_color)

    def toggle_manhattan_excess_volume(self):
        self.__show_manhattan_excess = not self.__show_manhattan_excess

        for edge in self.__edges.values():
            edge.toggle_excess_volume(shown = self.__show_manhattan_excess)

    def alter_node_appearance(self, node: ZxNode, highlight: bool = False):
        if node is not None:
            self.__nodes[node].alter_highlighting(
                color = 'white' if not highlight else 'green4' if node.is_realised() else 'red4'
            )

    def alter_node_color(self, node: ZxNode, color: str):
        if node is not None:
            self.__nodes[node].alter_highlighting(color = color)

    def alter_edge_appearance(self, edge: ZxEdge, highlight: bool = False):
        self.alter_node_appearance(edge.source, highlight=highlight)
        self.alter_node_appearance(edge.target, highlight=highlight)

        self.__edges[ edge ].alter_highlighting(
            color='white' if not highlight else 'green5' if edge.is_realised() else 'red4'
        )

    def alter_cycle_appearance(self, cycle: list[ZxEdge], highlight: bool = False):
        for edge in cycle:
            self.alter_node_appearance(edge.source, highlight=highlight )
            self.alter_node_appearance(edge.target, highlight=highlight )
            self.alter_edge_appearance(edge, highlight=highlight)