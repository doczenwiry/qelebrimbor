from vedo import settings, Plotter  # type: ignore[import-untyped]

from qelebrimbor.vedo.scene_manager_bg import BgSceneManager
from qelebrimbor.vedo.scene_manager_zx import ZxSceneManager
from qelebrimbor.vedo.shapes_zx import VdNode, VdEdge
from qelebrimbor.vedo.shapes_bg import VdCube, VdPipe

from qelebrimbor.vedo.zx_layout.abstract import ZxLayout
from qelebrimbor.vedo.zx_layout.circuit import CircuitLayout

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.attributes_bg import CubeId

import logging
console = logging.getLogger(__name__)
logging.getLogger('matplotlib').setLevel(logging.CRITICAL)

ZX_VIEWPORT = 0
BG_VIEWPORT = 1

VIEWPORTS = [
    dict(bottomleft=(0.00, 0.00), topright=(0.50, 1.00), bg='k8'), # ZX Viewport
    dict(bottomleft=(0.50, 0.00), topright=(1.00, 1.00), bg='k6'), # BG Viewport
]

settings.enable_default_mouse_callbacks = False
settings.enable_default_keyboard_callbacks = False

class VolumetricZxGraphViewer(Plotter):
    def __init__(self, vzx: VolumetricZxGraph, label: str = "", layout: ZxLayout | None = None):
        super().__init__(size = "full", shape = VIEWPORTS, sharecam = False, title = f"qelebrimbor [{label}]")

        # Initialise the camera for the BG Graph
        zx_camera = self.at(ZX_VIEWPORT).camera
        zx_camera.SetParallelProjection(True)
        zx_camera.SetViewUp(0, 1, 0)

        # Store the original AugmentedNxGraph
        self.__graph = vzx

        # Set the global callbacks
        self.add_callback("key press", self.__on_key_pressed)
        self.add_callback("mouse move", self.__on_mouse_moved)

        # Prepare the scene manager for the ZX-graph
        self.__zx_scene_manager = ZxSceneManager(
            vzx= self.__graph,
            plotter = self.at(ZX_VIEWPORT),
            layout = CircuitLayout(vzx) if layout is None else layout
        )

        # Prepare the scene manager for the BG-graph
        self.__bg_scene_manager = BgSceneManager(self.__graph, self.at(BG_VIEWPORT))

        self.__selected_object = None

    def __alter_highlighting(self, selected_object, highlighting: bool = True):
        if isinstance(selected_object, VdNode):
            # Highlight the zx-node and its corresponding bg-cube
            zx_node = selected_object.zx_node
            if highlighting:
                console.info(f"ZxNode : {zx_node}")
            self.__zx_scene_manager.alter_node_appearance(zx_node.id, highlight = highlighting)
            self.__bg_scene_manager.alter_cube_appearance(zx_node.realising_cube, highlight = highlighting)
        elif isinstance(selected_object, VdEdge):
            zx_edge = selected_object.zx_edge
            if highlighting:
                console.info(f"ZxEdge : {zx_edge}")
            # Highlight the edge in the ZX-graph and all the pipes of its realisation
            self.__zx_scene_manager.alter_edge_appearance(zx_edge, highlight = highlighting)
            self.__bg_scene_manager.alter_pipes_appearance(*zx_edge.realisation, highlight = highlighting)
        elif isinstance(selected_object, VdCube):
            bg_cube = selected_object.bg_cube
            if highlighting:
                console.info(f"BgCube : {bg_cube}")
            # Highlight the bg-cube and its corresponding zx-node if it has one
            self.__zx_scene_manager.alter_node_appearance(bg_cube.realised_node, highlight = highlighting)
            self.__bg_scene_manager.alter_cube_appearance(bg_cube.id, highlight = highlighting)
        elif isinstance(selected_object, VdPipe):
            bg_source_cube = selected_object.bg_source
            bg_target_cube = selected_object.bg_target
            if highlighting:
                console.info(f"BgPipe : {bg_source_cube}-{bg_target_cube}")
            self.__bg_scene_manager.alter_pipes_appearance((bg_source_cube.id, bg_target_cube.id), highlight = highlighting)
            # TODO: highlight the entire path this pipe belongs to

    def __on_key_pressed(self, event):
        # Pass the key press to the BG scene manager
        if event.keypress == "Escape":
            self.close()
        else:
            self.__bg_scene_manager.on_key_press(event)

    def __on_mouse_moved(self, event):
        if event.object != self.__selected_object:
            console.debug(f"Entered new object.")

            if self.__selected_object is not None:
                self.__alter_highlighting(self.__selected_object, highlighting = False)

            self.__selected_object = event.object
            self.__alter_highlighting(self.__selected_object, highlighting = True)

        self.render()

    def display(self):
        self.at(ZX_VIEWPORT).show()
        self.at(BG_VIEWPORT).show()
        self.interactive().close()