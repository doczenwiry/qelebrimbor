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

from logging import getLogger

from vedo.plotter import Plotter  # type: ignore[import-untyped]

from qelebrimbor.core.components import ZxEdge, ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker
from qelebrimbor.vedo.shapes_zx import VdEdge, VdNode
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout

console = getLogger(__name__)


class ZxSceneManager:
    def __init__(
        self,
        graph: VolumetricZxGraph,
        plotter: Plotter,
        layout: ZxLayout,
        show_nodes: set[ZxNode] | None = None,
    ):
        self.__plotter = plotter
        self.__vzx_graph = graph

        self.__vd_nodes: dict[ZxNode, VdNode] = dict()
        self.__vd_edges: dict[ZxEdge, VdEdge] = dict()

        # Prepare all the elements for the ZX scene (i.e. nodes and edges)
        for node in graph.get_zx_nodes():
            vd_node = VdNode(node, layout.get_node_placement(node)).z(+0.1)
            self.__vd_nodes[node] = vd_node
            if not show_nodes or node in show_nodes:
                self.__plotter.add(vd_node)

        for edge in graph.get_zx_edges():
            vd_edge = VdEdge(
                edge,
                layout.get_node_placement(edge.source),
                layout.get_node_placement(edge.target),
            ).z(-0.1)
            self.__vd_edges[edge] = vd_edge
            if not show_nodes or (edge.source in show_nodes and edge.target in show_nodes):
                self.__plotter.add(vd_edge)

        self.__selected_object = None
        self.__highlight_manhattan_excess = False

    def alter_unrealised_subgraph_highlighting(self, highlight: bool):
        for zx_node in self.__vzx_graph.get_zx_nodes():
            self.__vd_nodes[zx_node].alter_highlighting(
                highlight
            )  # , concealed = highlight and not zx_node.is_realised())

        for zx_edge in self.__vzx_graph.get_zx_edges():
            self.__vd_edges[zx_edge].alter_highlighting(
                highlight
            )  # , concealed = highlight and not zx_edge.is_realised())

    def alter_manhattan_excess_highlighting(self, highlight: bool):
        for zx_edge in self.__vzx_graph.get_zx_edges():
            if zx_edge.excess_volume > 0:
                self.alter_node_highlighting(zx_edge.source, highlight=highlight)
                self.alter_node_highlighting(zx_edge.target, highlight=highlight)
                self.__vd_edges[zx_edge].alter_highlighting(highlight=highlight, excess=True)

    def alter_insufficient_ports_highlighting(self, highlight: bool):
        for node in OpenPortsTracker.get_nodes_with_insufficient_ports(self.__vzx_graph):
            self.__vd_nodes[node].alter_highlighting(highlight=highlight, unreachable=True)

    def alter_node_highlighting(self, node: ZxNode, highlight: bool, concealed: bool = False):
        if node:
            self.__vd_nodes[node].alter_highlighting(highlight=highlight, concealed=concealed)

    def alter_edge_highlighting(self, edge: ZxEdge, highlight: bool, excluded: bool = False):
        self.alter_node_highlighting(edge.source, highlight=highlight, concealed=excluded)
        self.alter_node_highlighting(edge.target, highlight=highlight, concealed=excluded)
        self.__vd_edges[edge].alter_highlighting(highlight=highlight, concealed=excluded)

    def alter_cycle_highlighting(self, cycle: ZxCycle, highlight: bool):
        _, edges = zip(*cycle)
        for edge in edges:
            self.alter_node_highlighting(edge.source, highlight=highlight)
            self.alter_node_highlighting(edge.target, highlight=highlight)
            self.__vd_edges[edge].alter_highlighting(highlight=highlight, excess=True)
