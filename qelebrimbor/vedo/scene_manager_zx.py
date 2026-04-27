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
        self.__show_unrealised = False
        self.toggle_unrealised_appearance()

    def toggle_unrealised_appearance(self):
        self.__show_unrealised = not self.__show_unrealised

        node_alpha = 1.0
        edge_alpha = 1.0
        if not self.__show_unrealised:
            node_alpha /= 4.0
            edge_alpha /= 32.0
        
        for node in self.__vzx_graph.get_zx_nodes():
            if not node.is_realised():
                self.__nodes[ node ].alpha(node_alpha)

        for edge in self.__vzx_graph.get_zx_edges():
            if not edge.is_realised():
                self.__edges[ edge ].alpha(edge_alpha)

    def alter_node_appearance(self, node: ZxNode, highlight: bool = False):
        if node is not None:
            self.__nodes[node].alter_highlighting(
                color = 'white' if not highlight else 'teal5' if node.is_realised() else 'indigo5'
            )

    def alter_edge_appearance(self, edge: ZxEdge, highlight: bool = False):
        self.alter_node_appearance(edge.source, highlight=highlight)
        self.alter_node_appearance(edge.target, highlight=highlight)

        self.__edges[ edge ].alter_highlighting(
            color='white' if not highlight else 'teal5' if edge.is_realised() else 'indigo5'
        )

    def alter_cycle_appearance(self, cycle: list[ZxEdge], highlight: bool = False):
        for edge in cycle:
            self.alter_node_appearance(edge.source, highlight=highlight )
            self.alter_node_appearance(edge.target, highlight=highlight )
            self.alter_edge_appearance(edge, highlight=highlight)