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

import logging

from vedo import Plotter, settings  # type: ignore[import-untyped]

from qelebrimbor.core.components import ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.vedo.miscellaneous import VdCubeReference
from qelebrimbor.vedo.scene_manager_bg import BgSceneManager
from qelebrimbor.vedo.scene_manager_zx import ZxSceneManager
from qelebrimbor.vedo.shapes_bg import VdCube, VdPipe
from qelebrimbor.vedo.shapes_zx import VdEdge, VdNode
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout
from qelebrimbor.vedo.zx_layout.circuit import CircuitLayout
from qelebrimbor.vedo.zx_layout.planar import PlanarLayout

console = logging.getLogger(__name__)


ZX_VIEWPORT = 0
BG_VIEWPORT = 1
BG_CUBEFACE = 2

ZXVP = 0.25

VIEWPORTS = [
    dict(bottomleft=(0.00, 0.00), topright=(ZXVP, 1.00), bg="k8"),  # ZX Viewport
    dict(bottomleft=(ZXVP, 0.00), topright=(1.00, 1.00), bg="k6"),  # BG Viewport
    dict(bottomleft=(0.95, 0.90), topright=(1.00, 1.00), bg="k7"),  # BG Cube Face
]

settings.enable_default_mouse_callbacks = False
settings.enable_default_keyboard_callbacks = False


class VolumetricZxGraphViewer(Plotter):
    def __init__(
        self,
        graph: VolumetricZxGraph,
        cycles: list[ZxCycle] | None = None,
        scope: tuple[ZxNode, int] | None = None,
        label: str = "",
        layout: ZxLayout | None = None,
        size: str = "auto",
    ):
        super().__init__(size=size, shape=VIEWPORTS, sharecam=False, title=f"qelebrimbor [{label}]")

        # Store the original AugmentedNxGraph
        self.__vzx_graph = graph

        # Prepare the scene manager for the ZX-graph
        selected_layout: ZxLayout
        if layout is None:
            if len(graph.get_zx_qubits()) > 0 and len(graph.get_zx_layers()) > 0:
                selected_layout = CircuitLayout(
                    graph,
                    vertical=len(graph.get_zx_qubits()) <= len(graph.get_zx_layers()),
                )
            else:
                selected_layout = PlanarLayout(graph, scale=1.5)
        else:
            selected_layout = layout

        if scope is not None:
            zx_node, st_range = scope
            bg_cubes = set(
                filter(
                    lambda bgc: bgc.position.get_manhattan_distance(zx_node.realising_cube.position) <= st_range,
                    graph.get_bg_cubes(),
                )
            )
            zx_nodes = set(bgc.realised_node for bgc in bg_cubes if bgc.realised_node is not None)
        else:
            zx_nodes = None
            bg_cubes = None

        self.__zx_scene_manager = ZxSceneManager(
            graph=self.__vzx_graph,
            show_nodes=zx_nodes,
            plotter=self.at(ZX_VIEWPORT),
            layout=selected_layout,
        )
        self.at(ZX_VIEWPORT).camera.SetParallelProjection(True)

        # Prepare the scene manager for the BG-graph
        self.__bg_scene_manager = BgSceneManager(
            graph=self.__vzx_graph, plotter=self.at(BG_VIEWPORT), show_cubes=bg_cubes
        )

        # Prepare the cube for face reference
        self.at(BG_CUBEFACE).add(VdCubeReference())

        # Initialise the cameras for the viewports
        self.reset_camera()
        self.__setup_camera()

        self.__hovered_object = None

        self.__cycles_processed = cycles if cycles is not None else []
        self.__highlighted_cycle = -1

        self.__highlighting_manhattan_excess = False
        self.__highlighting_insufficient_ports = False
        self.__highlighting_unrealised_subgraph = False

        # Set the global callbacks
        self.add_callback("key press", self.__on_key_pressed)
        self.add_callback("mouse move", self.__on_mouse_moved)

    def __setup_camera(self):
        # Initialise the camera for the ZX Graph
        self.at(ZX_VIEWPORT).camera.SetViewUp(0, 1, 0)

        # Initialise the camera for the BG Graph
        self.at(BG_VIEWPORT).camera.SetPosition(22, 14, 15)
        self.at(BG_VIEWPORT).camera.SetViewUp(0, 0, 1)

        # Share the camera between the BlockGraph and the CubeFaces
        self.at(BG_CUBEFACE).camera.SetViewUp(0, 0, 1)
        self.at(BG_CUBEFACE).camera.SetPosition(22, 14, 15)

    def __alter_highlighting(self, selected, highlighting: bool = True):
        if isinstance(selected, VdNode):
            # Highlight the zx-node and its corresponding bg-cube
            zx_node = selected.zx_node
            if highlighting:
                console.info(f"ZxNode : {zx_node}")
            self.__zx_scene_manager.alter_node_highlighting(zx_node, highlight=highlighting)
            if zx_node.is_realised():
                self.__bg_scene_manager.alter_cube_highlighting(zx_node.realising_cube, highlight=highlighting)
        elif isinstance(selected, VdEdge):
            zx_edge = selected.zx_edge
            if highlighting:
                console.info(f"ZxEdge : {zx_edge}")
            # Highlight the edge in the ZX-graph and all the pipes of its realisation
            self.__zx_scene_manager.alter_edge_highlighting(zx_edge, highlight=highlighting)
            self.__bg_scene_manager.alter_path_highlighting(*zx_edge.realisation, highlight=highlighting)
        elif isinstance(selected, VdCube):
            bg_cube = selected.bg_cube
            if highlighting:
                console.info(f"BgCube : {bg_cube}")
            # Highlight the bg-cube and its corresponding zx-node if it has one
            self.__zx_scene_manager.alter_node_highlighting(bg_cube.realised_node, highlight=highlighting)
            self.__bg_scene_manager.alter_cube_highlighting(bg_cube, highlight=highlighting)
        elif isinstance(selected, VdPipe):
            bg_pipe = selected.bg_pipe
            if highlighting:
                console.info(f"BgPipe : {bg_pipe}")
            self.__bg_scene_manager.alter_path_highlighting(bg_pipe, highlight=highlighting)

    def __shift_selected_cycle(self, shift: int):
        if self.__highlighted_cycle != -1 and len(self.__cycles_processed) > 0:
            self.__alter_selected_cycle_highlighting(highlighting=False)
            self.__highlighted_cycle = (self.__highlighted_cycle + shift) % len(self.__cycles_processed)
            self.__alter_selected_cycle_highlighting(highlighting=True)

    def __alter_selected_cycle_highlighting(self, highlighting: bool):
        if self.__highlighted_cycle != -1:
            selected_cycle = self.__cycles_processed[self.__highlighted_cycle]
            self.__zx_scene_manager.alter_cycle_highlighting(selected_cycle, highlight=highlighting)
            self.__bg_scene_manager.alter_cycle_highlighting(selected_cycle, highlight=highlighting)

    def __on_key_pressed(self, event):
        if event.keypress == "Escape":
            self.close()
        # Keypresses dealing with cycle highlighting
        elif event.keypress == "c":
            if len(self.__cycles_processed) > 0:
                if self.__highlighted_cycle == -1:
                    self.__highlighted_cycle = 0
                    self.__alter_selected_cycle_highlighting(highlighting=True)
                else:
                    self.__alter_selected_cycle_highlighting(highlighting=False)
                    self.__highlighted_cycle = -1
        elif event.keypress == "Up":
            self.__shift_selected_cycle(shift=+1)
        elif event.keypress == "Down":
            self.__shift_selected_cycle(shift=-1)
        # Keypress dealing with Manhattan Excesses highlighting
        elif event.keypress == "e":
            self.__highlighting_manhattan_excess = not self.__highlighting_manhattan_excess
            self.__zx_scene_manager.alter_manhattan_excess_highlighting(self.__highlighting_manhattan_excess)
        # Keypress dealing with Insufficient Ports highlighting
        elif event.keypress == "i":
            self.__highlighting_insufficient_ports = not self.__highlighting_insufficient_ports
            self.__zx_scene_manager.alter_insufficient_ports_highlighting(self.__highlighting_insufficient_ports)
        # Keypresses dealing with toggling unrealised parts of the ZX-graph
        elif event.keypress == "u":
            self.__highlighting_unrealised_subgraph = not self.__highlighting_unrealised_subgraph
            self.__zx_scene_manager.alter_unrealised_subgraph_highlighting(self.__highlighting_unrealised_subgraph)
            pass
        else:
            self.__bg_scene_manager.on_key_press(event)

        self.render()

    def __on_mouse_moved(self, event):
        if (
            self.__highlighted_cycle != -1
            or self.__highlighting_unrealised_subgraph
            or self.__highlighting_insufficient_ports
        ):
            return

        if event.object != self.__hovered_object:
            if self.__hovered_object is not None:
                self.__alter_highlighting(self.__hovered_object, highlighting=False)

            self.__hovered_object = event.object
            self.__alter_highlighting(self.__hovered_object, highlighting=True)

        try:
            # TODO: lock the orientation of the BG_CUBEFACE to match that of VdCubes in BG_VIEWPORT correctly.
            self.at(BG_CUBEFACE).camera.SetViewUp(self.at(BG_VIEWPORT).camera.GetViewUp())
        except IndexError:
            pass

        self.render()

    def display(self):
        self.at(ZX_VIEWPORT).show()
        self.at(BG_VIEWPORT).show()
        self.at(BG_CUBEFACE).show()
        self.interactive()
