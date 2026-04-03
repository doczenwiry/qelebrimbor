from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_bg import CubeId

from vedo import settings, Plotter

from qelebrimbor.vedo.scene_manager_bg import BgSceneManager
from qelebrimbor.vedo.scene_manager_zx import ZxSceneManager
from qelebrimbor.vedo.shapes_zx import ZxNode, ZxEdge
from qelebrimbor.vedo.shapes_bg import BgCube, BgPipe

import logging

from qelebrimbor.vedo.zx_layout.abstract import ZxLayout
from qelebrimbor.vedo.zx_layout.circuit import CircuitLayout

console = logging.getLogger(__name__)
logging.getLogger('matplotlib').setLevel(logging.CRITICAL)

ZX_VIEWPORT = 0
BG_VIEWPORT = 1

VIEWPORTS = [
    dict(bottomleft=(0.00, 0.75), topright=(1.00, 1.00), bg='k8'), # ZX Viewport
    dict(bottomleft=(0.00, 0.00), topright=(1.00, 0.75), bg='k6'), # BG Viewport
]

settings.enable_default_mouse_callbacks = False
settings.enable_default_keyboard_callbacks = False

class AugmentedZxGraphViewer(Plotter):
    def __init__(self, azx: AugmentedZxGraph, label: str = "", layout: ZxLayout | None = None):
        super().__init__(shape = VIEWPORTS, sharecam = False, title = f"qelebrimbor [{label}]")

        # Initialise the camera for the BG Graph
        zx_camera = self.at(ZX_VIEWPORT).camera
        zx_camera.SetParallelProjection(True)
        zx_camera.SetViewUp(0, 1, 0)

        # Store the original AugmentedNxGraph
        self.__graph = azx

        # Set the global callbacks
        self.add_callback("key press", self.__on_key_pressed)
        self.add_callback("mouse move", self.__on_mouse_moved)

        # Prepare the scene manager for the ZX-graph
        self.__zx_scene_manager = ZxSceneManager(
            azx = self.__graph,
            plotter = self.at(ZX_VIEWPORT),
            layout = CircuitLayout(azx) if layout is None else layout
        )

        # Prepare the scene manager for the BG-graph
        self.__bg_scene_manager = BgSceneManager(self.__graph, self.at(BG_VIEWPORT))
        self.__min_bg_cube_id = self.__graph.number_of_nodes()
        self.__max_bg_cube_id = self.__min_bg_cube_id + self.__graph.number_of_cubes() - 1

        self.__selected_object = None

    def __alter_highlighting(self, selected_object, highlighting: bool = True):
        if isinstance(selected_object, ZxNode):
            # Highlight the zx-node and its corresponding bg-cube
            zx_node = selected_object.zx_node
            self.__zx_scene_manager.alter_node_appearance(zx_node, highlight = highlighting)
            for bg_cube in self.__graph.get_realising_cubes(zx_node):
                self.__bg_scene_manager.alter_cube_appearance(bg_cube, highlight = highlighting)
        elif isinstance(selected_object, ZxEdge):
            # Highlight the edge in the ZX-graph
            zx_source = selected_object.zx_source
            zx_target = selected_object.zx_target
            self.__zx_scene_manager.alter_node_appearance(zx_source, highlight = highlighting)
            self.__zx_scene_manager.alter_node_appearance(zx_target, highlight = highlighting)
            self.__zx_scene_manager.alter_edge_appearance(zx_source, zx_target, highlight = highlighting)
            # Highlight all the pipes of that path
            if len(self.__graph.get_edge_realisation(zx_source, zx_target)) > 0:
                previous_cube: CubeId = self.__graph.get_edge_realisation(zx_source, zx_target)[0][0]
                self.__bg_scene_manager.alter_cube_appearance(previous_cube, highlight = highlighting)
                for _, current_cube in self.__graph.get_edge_realisation(zx_source, zx_target):
                    self.__bg_scene_manager.alter_cube_appearance(current_cube, highlight = highlighting)
                    self.__bg_scene_manager.alter_pipe_appearance(previous_cube, current_cube, highlight = highlighting)
                    previous_cube = current_cube
        elif isinstance(selected_object, BgCube):
            # Highlight the bg-cube and its corresponding zx-node if it has one
            bg_cube = selected_object.bg_cube
            console.debug(f"> BgCube #{bg_cube}")
            if self.__min_bg_cube_id <= bg_cube <= self.__max_bg_cube_id:
                for zx_node in self.__graph.get_realised_nodes(bg_cube):
                    self.__zx_scene_manager.alter_node_appearance(zx_node, highlight = highlighting)
            self.__bg_scene_manager.alter_cube_appearance(bg_cube, highlight = highlighting)
        elif isinstance(selected_object, BgPipe):
            bg_source_cube = selected_object.bg_source
            bg_target_cube = selected_object.bg_target
            console.debug(f"> BgPipe #{bg_source_cube}-#{bg_target_cube}")
            self.__bg_scene_manager.alter_cube_appearance(bg_source_cube, highlight = highlighting)
            self.__bg_scene_manager.alter_cube_appearance(bg_target_cube, highlight = highlighting)
            self.__bg_scene_manager.alter_pipe_appearance(bg_source_cube, bg_target_cube, highlight = highlighting)
            # Show the highlighting for the entire path this pipe belongs to

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

        self.at(ZX_VIEWPORT).render()
        self.at(BG_VIEWPORT).render()

    def display(self):
        self.at(ZX_VIEWPORT).show()
        self.at(BG_VIEWPORT).show()
        self.interactive().close()