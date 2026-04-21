from vedo.plotter import Plotter  # type: ignore[import-untyped]

from qelebrimbor.common.attributes_zx import NodeId
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

        self.__nodes = dict()
        self.__edges = dict()

        # Prepare all the elements for the ZX scene (i.e. nodes and edges)
        for node in graph.get_zx_nodes():
            vd_node = VdNode(node, layout.get_node_placement(node.id)).z(+0.1)
            self.__nodes[ node.id ] = vd_node
            self.__plotter.add( vd_node )

        for edge in graph.get_zx_edges():
            vd_edge = VdEdge(
                edge, layout.get_node_placement(edge.source), layout.get_node_placement(edge.target)
            ).z(-0.1)
            self.__edges[ edge.source , edge.target] = vd_edge
            self.__plotter.add( vd_edge )

        self.__selected_object = None
        self.__show_unrealised = True
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
                self.__nodes[ node.id ].alpha(node_alpha)

        for edge in self.__vzx_graph.get_zx_edges():
            if not edge.is_realised():
                self.__edges[ edge.source , edge.target ].alpha(edge_alpha)

    def alter_node_appearance(self, node: NodeId, highlight: bool = False):
        if node != -1:
            if highlight:
                new_color = 'teal5' if self.__vzx_graph.is_zx_node_realised(node) else 'indigo5'
            else:
                new_color = 'white'

            self.__nodes[node].alter_highlighting(color= new_color)

    def alter_edge_appearance(self, edge: EdgeId, highlight: bool = False):
        source, target = edge
        self.alter_node_appearance(source, highlight=highlight)
        self.alter_node_appearance(target, highlight=highlight)

        if highlight:
            new_color = 'teal5' if self.__vzx_graph.is_zx_edge_realised(*edge) else 'indigo5'
        else:
            new_color = 'white'
        self.__edges[ *edge ].alter_highlighting(color = new_color)

    def alter_cycle_appearance(self, cycle: list[EdgeId], highlight: bool = False):
        for edge in cycle:
            source, target = edge
            self.alter_node_appearance(source, highlight=highlight )
            self.alter_node_appearance(target, highlight=highlight )
            self.alter_edge_appearance(edge, highlight=highlight)