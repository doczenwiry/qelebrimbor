from vedo.plotter.runtime import Plotter

from qelebrimbor.vedo.shapes_zx import ZxNode, ZxEdge
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_zx import NodeId

from logging import getLogger
console = getLogger(__name__)

class ZxSceneManager:
    def __init__(self, azx: AugmentedZxGraph, plotter: Plotter, layout: ZxLayout):
        self.__graph = azx
        self.__plotter = plotter
        self.__zx_layout = layout

        self.__nodes = dict()
        self.__edges = dict()

        # Prepare all the elements for the ZX scene (i.e. nodes and edges)
        for node in self.__graph.nodes:
            zx_node = ZxNode(node, self.__graph, layout.get_node_placement(node)).z(+0.1)
            self.__nodes[ node ] = zx_node

        for source, target in self.__graph.get_edges():
            zx_edge = ZxEdge(source, target, self.__graph).z(-0.1)
            self.__edges[ source , target ] = zx_edge

        self.__plotter.add(list(self.__nodes.values()))
        self.__plotter.add(list(self.__edges.values()))

        self.__selected_object = None

    def alter_node_appearance(self, node: NodeId, highlight: bool = False):
        self.__nodes[ node ].alter_appearance(highlight = highlight)

    def alter_edge_appearance(self, source: NodeId, target: NodeId, highlight: bool = False):
        self.__edges[ source , target ].alter_appearance(highlight = highlight)

    # def on_left_click(self, event):
    #     if isinstance(event.object, ZxNode):
    #         bg_cube = self.__nx_graph.get_cube(event.object.zx_node)
    #         extra = f"[C{bg_cube}]" if bg_cube is not None else ""
    #         console.debug(f"Clicked on Node #{event.object.zx_node} {extra}")
    #         event.object.toggle_highlight()
    #
    #     if isinstance(event.object, ZxEdge):
    #         console.debug(f"Clicked on Edge  {event.object.zx_source}-{event.object.zx_target}")