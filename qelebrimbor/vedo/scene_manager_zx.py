from vedo.plotter import Plotter  # type: ignore[import-untyped]

from qelebrimbor.common.attributes_zx import NodeId
from qelebrimbor.common.components import ZxEdge
from qelebrimbor.vedo.shapes_zx import VdNode, VdEdge
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from logging import getLogger
console = getLogger(__name__)

class ZxSceneManager:
    def __init__(self, vzx: VolumetricZxGraph, plotter: Plotter, layout: ZxLayout):
        self.__plotter = plotter
        self.__zx_layout = layout

        self.__nodes = dict()
        self.__edges = dict()

        # Prepare all the elements for the ZX scene (i.e. nodes and edges)
        for node in vzx.get_zx_nodes():
            vd_node = VdNode(node, layout.get_node_placement(node.id)).z(+0.1)
            self.__nodes[ node.id ] = vd_node
            self.__plotter.add( vd_node )

        for edge in vzx.get_zx_edges():
            vd_edge = VdEdge(
                edge, layout.get_node_placement(edge.source), layout.get_node_placement(edge.target)
            ).z(-0.1)
            self.__edges[ edge.source , edge.target ] = vd_edge
            self.__plotter.add( vd_edge )

        self.__selected_object = None

    def alter_node_appearance(self, node: NodeId, highlight: bool = False):
        self.__nodes[ node ].alter_appearance(highlight = highlight)

    def alter_edge_appearance(self, edge: ZxEdge, highlight: bool = False):
        self.__edges[ edge.source, edge.target ].alter_appearance(highlight = highlight)

    # def on_left_click(self, event):
    #     if isinstance(event.object, ZxNode):
    #         bg_cube = self.__nx_graph.get_cube(event.object.zx_node)
    #         extra = f"[C{bg_cube}]" if bg_cube is not None else ""
    #         console.debug(f"Clicked on Node #{event.object.zx_node} {extra}")
    #         event.object.toggle_highlight()
    #
    #     if isinstance(event.object, ZxEdge):
    #         console.debug(f"Clicked on Edge  {event.object.zx_source}-{event.object.zx_target}")