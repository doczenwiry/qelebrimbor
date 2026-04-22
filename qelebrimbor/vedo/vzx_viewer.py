from vedo import settings, Plotter, ButtonWidget, Text3D  # type: ignore[import-untyped]

from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser
from qelebrimbor.utilities.least_cycle_analyser import MinimalCycleBasisAnalyser
from qelebrimbor.vedo.miscellaneous import VdCubeReference
from qelebrimbor.vedo.scene_manager_bg import BgSceneManager
from qelebrimbor.vedo.scene_manager_zx import ZxSceneManager
from qelebrimbor.vedo.shapes_zx import VdNode, VdEdge
from qelebrimbor.vedo.shapes_bg import VdCube, VdPipe

from qelebrimbor.vedo.zx_layout.abstract import ZxLayout
from qelebrimbor.vedo.zx_layout.circuit import CircuitLayout

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

ZX_VIEWPORT = 0
BG_VIEWPORT = 1
BG_CUBEFACE = 2

ZXVP = 0.25

VIEWPORTS = [
    dict(bottomleft=(0.00, 0.00), topright=(ZXVP, 1.00), bg='k8'), # ZX Viewport
    dict(bottomleft=(ZXVP, 0.00), topright=(1.00, 1.00), bg='k6'), # BG Viewport
    dict(bottomleft=(0.95, 0.90), topright=(1.00, 1.00), bg='k7'), # BG Cube Face
]

settings.enable_default_mouse_callbacks = False
settings.enable_default_keyboard_callbacks = False

class VolumetricZxGraphViewer(Plotter):
    def __init__(self, graph: VolumetricZxGraph, label: str = "", layout: ZxLayout | None = None):
        super().__init__(size = "auto", shape = VIEWPORTS, sharecam = False, title = f"qelebrimbor [{label}]")

        # Store the original AugmentedNxGraph
        self.__vzx_graph = graph

        # Prepare the scene manager for the ZX-graph
        self.__zx_scene_manager = ZxSceneManager(
            graph= self.__vzx_graph,
            plotter = self.at(ZX_VIEWPORT),
            layout = CircuitLayout(graph) if layout is None else layout
        )
        self.at(ZX_VIEWPORT).camera.SetParallelProjection(True)

        # Prepare the scene manager for the BG-graph
        self.__bg_scene_manager = BgSceneManager(self.__vzx_graph, self.at(BG_VIEWPORT))

        # Prepare the cube for face reference
        self.at(BG_CUBEFACE).add( VdCubeReference() )

        # Initialise the cameras for the viewports
        self.__reset_camera()

        self.__hovered_object = None

        self.__available_cycle_analysers = [
            MinimalCycleBasisAnalyser.decompose_edges(self.__vzx_graph),
            CycleBasisAnalyser.decompose_edges(self.__vzx_graph)
        ]
        self.__selected_cycle_analyser = 0
        self.__selected_cycle_index = -1
        self.__available_cycles = self.__available_cycle_analysers[self.__selected_cycle_analyser]

        # Set the global callbacks
        self.add_callback("key press", self.__on_key_pressed)
        self.add_callback("mouse move", self.__on_mouse_moved)

    def __reset_camera(self):
        # Initialise the camera for the ZX Graph
        self.at(ZX_VIEWPORT).camera.SetViewUp(0, 1, 0)

        # Initialise the camera for the BG Graph
        self.at(BG_VIEWPORT).camera.SetPosition(22, 14, 15)
        self.at(BG_VIEWPORT).camera.SetFocalPoint(0, 0, 0)
        self.at(BG_VIEWPORT).camera.SetViewUp(0, 0, 1)

        # Share the camera between the BlockGraph and the CubeFaces
        self.at(BG_CUBEFACE).camera.SetFocalPoint(0, 0, 0)
        self.at(BG_CUBEFACE).camera.SetViewUp(0, 0, 1)
        self.at(BG_CUBEFACE).camera.SetPosition(22, 14, 15)

    def __alter_highlighting(self, selected, highlighting: bool = True):
        if isinstance(selected, VdNode):
            # Highlight the zx-node and its corresponding bg-cube
            zx_node = selected.zx_node
            if highlighting:
                console.info(f"ZxNode : {zx_node}")
            self.__zx_scene_manager.alter_node_appearance(zx_node, highlight = highlighting)
            self.__bg_scene_manager.alter_cube_appearance(zx_node.realising_cube, highlight = highlighting)
        elif isinstance(selected, VdEdge):
            zx_edge = selected.zx_edge
            if highlighting:
                console.info(f"ZxEdge : {zx_edge}")
            # Highlight the edge in the ZX-graph and all the pipes of its realisation
            self.__zx_scene_manager.alter_edge_appearance(zx_edge, highlight = highlighting)
            self.__bg_scene_manager.alter_pipes_appearance(*zx_edge.realisation, highlight = highlighting)
        elif isinstance(selected, VdCube):
            bg_cube = selected.bg_cube
            if highlighting:
                console.info(f"BgCube : {bg_cube}")
            # Highlight the bg-cube and its corresponding zx-node if it has one
            self.__zx_scene_manager.alter_node_appearance(bg_cube.realised_node, highlight = highlighting)
            self.__bg_scene_manager.alter_cube_appearance(bg_cube, highlight = highlighting)
        elif isinstance(selected, VdPipe):
            bg_pipe = selected.bg_pipe
            if highlighting:
                console.info(f"BgPipe : {bg_pipe}")
            self.__bg_scene_manager.alter_pipes_appearance(bg_pipe, highlight = highlighting)

    def __shift_selected_cycle(self, shift: int):
        self.__alter_selected_cycle_appearance(highlighting=False)
        self.__selected_cycle_index = (self.__selected_cycle_index + shift) % len(self.__available_cycles)
        self.__alter_selected_cycle_appearance(highlighting=True)

    def __alter_selected_cycle_appearance(self, highlighting: bool):
        if self.__selected_cycle_index != -1:
            selected_cycle = self.__available_cycles[self.__selected_cycle_index]
            self.__zx_scene_manager.alter_cycle_appearance(selected_cycle, highlight = highlighting)
            self.__bg_scene_manager.alter_cycle_appearance(selected_cycle, highlight = highlighting)

    def __on_key_pressed(self, event):
        if event.keypress == "Escape":
            self.close()
        elif event.keypress == "grave":
            self.__alter_selected_cycle_appearance(highlighting = False)
            self.__selected_cycle_index = -1
        elif event.keypress == "Up":
            self.__shift_selected_cycle(shift = +1)
        elif event.keypress == "Down":
            self.__shift_selected_cycle(shift = -1)
        elif event.keypress == "m":
            self.__alter_selected_cycle_appearance(highlighting = False)
            self.__selected_cycle_analyser = (self.__selected_cycle_analyser + 1) % len(self.__available_cycle_analysers)
            self.__available_cycles = self.__available_cycle_analysers[self.__selected_cycle_analyser]
            self.__selected_cycle_index = 0
            self.__alter_selected_cycle_appearance(highlighting = True)
        elif event.keypress == "u":
            # TODO: hide the unrealised part of the zx-graph
            self.__zx_scene_manager.toggle_unrealised_appearance()
            pass
        else:
            self.__bg_scene_manager.on_key_press(event)

        self.render()

    def __on_mouse_moved(self, event):
        if self.__selected_cycle_index == -1:
            if event.object != self.__hovered_object:
                if self.__hovered_object is not None:
                    self.__alter_highlighting(self.__hovered_object, highlighting = False)

                self.__hovered_object = event.object
                self.__alter_highlighting(self.__hovered_object, highlighting = True)

            self.at(BG_CUBEFACE).camera.SetViewUp(self.at(BG_VIEWPORT).camera.GetViewUp())
            self.render()

    def display(self):
        self.at(ZX_VIEWPORT).show()
        self.at(BG_VIEWPORT).show()
        self.at(BG_CUBEFACE).show()
        self.interactive().close()