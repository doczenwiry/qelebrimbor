from vedo.plotter.runtime import Plotter

from qelebrimbor.common.components_zx import EdgeType
from qelebrimbor.common.path import Path
from qelebrimbor.vedo.frame_manager import FrameManager

from qelebrimbor.common.components_bg import CubeId
from qelebrimbor.augmented_nx_graph import AugmentedNxGraph
from qelebrimbor.vedo.shapes_bg import BgCube, BgPipe

from logging import getLogger
console = getLogger(__name__)

class BgSceneManager:
    def __init__(self, nx_graph: AugmentedNxGraph, plotter: Plotter):
        self.__nx_graph = nx_graph
        self.__plotter = plotter

        self.__cubes = dict()
        self.__pipes = dict()

        self.__alternative_cubes = dict()
        self.__alternative_pipes = dict()

        # Prepare all the components for the BG viewport (i.e. cubes and pipes)
        self.__frame_manager = FrameManager(self.__plotter)

        for cube in nx_graph.get_cubes():
            node = self.__nx_graph.get_node(cube)
            kind = self.__nx_graph.get_cube_kind(cube)
            position = self.__nx_graph.get_cube_position(cube)
            extra_cube = BgCube(kind, position, node, cube)
            self.__cubes[cube] = extra_cube

        for source, target in nx_graph.get_pipes():
            pipe = tuple(sorted((source, target)))
            source_kind = self.__nx_graph.get_cube_kind(source)
            target_kind = self.__nx_graph.get_cube_kind(target)
            source_position = self.__nx_graph.get_cube_position(source)
            target_position = self.__nx_graph.get_cube_position(target)
            pipe_type = self.__nx_graph.get_pipe_kind(source, target)
            bg_pipe = BgPipe(source_kind, source_position, target_kind, target_position, pipe_type, source, target)
            self.__pipes[pipe] = bg_pipe

        node_realisation_order = self.__nx_graph.get_node_realisation_order()
        edge_realisation_order = self.__nx_graph.get_edge_realisation_order()

        if len(node_realisation_order) == 0 and len(edge_realisation_order) == 0:
            current_frame = self.__frame_manager.create_next_frame()
            self.__frame_manager.add_all_to_frame(current_frame, self.__cubes.values())
            self.__frame_manager.add_all_to_frame(current_frame, self.__pipes.values())
            console.debug(f"> Added {len(self.__cubes.values())} cubes.")
            console.debug(f"> Added {len(self.__pipes.values())} pipes.")
        else:
            placed_cubes = set()
            if len(node_realisation_order) > 0:
                root = node_realisation_order[0]
                root_cube = self.__cubes[ self.__nx_graph.get_cube(root) ]
                placed_cubes.add(root_cube)
                current_frame = self.__frame_manager.create_next_frame()
                self.__frame_manager.add_to_frame(current_frame, root_cube)

            for source, target in edge_realisation_order:
                # Add extra cubes to a new frame
                current_frame = self.__frame_manager.create_next_frame()
                previous_cube = self.__nx_graph.get_cube(source)
                for current_cube in self.__nx_graph.get_edge_realisation(source, target).get_cube_ids()[1:]:
                    pipe = tuple(sorted((previous_cube, current_cube)))
                    self.__frame_manager.add_to_frame(current_frame, self.__pipes[pipe])

                    if current_cube not in placed_cubes:
                        self.__frame_manager.add_to_frame(current_frame, self.__cubes[current_cube])
                        placed_cubes.add(current_cube)

                    previous_cube = current_cube

                # Add alternative paths to subsequent subframes
                alternatives = self.__nx_graph.get_edge_alternatives(source, target)
                if alternatives is None:
                    continue

                for alternative in alternatives:
                    current_subframe = self.__frame_manager.create_next_subframe(current_frame)
                    previous_cube = alternative.get_source_cube()
                    previous_kind, previous_position = alternative.get_cubes()[0]
                    for alternative_kind, alternative_position in alternative.get_cubes()[1:]:
                        alternative_cube = self.__nx_graph.number_of_nodes() + self.__nx_graph.number_of_cubes() + len(self.__alternative_cubes)
                        alternative_bg_cube = BgCube(alternative_kind, alternative_position, cube = alternative_cube)
                        self.__alternative_cubes[alternative_cube] = alternative_bg_cube
                        pipe = tuple(sorted((previous_cube, alternative_cube)))
                        alternative_bg_pipe = BgPipe(
                            previous_kind, previous_position,
                            alternative_kind, alternative_position,
                            EdgeType.IDENTITY, source = previous_cube, target = alternative_cube
                        )
                        self.__alternative_pipes[pipe] = alternative_bg_pipe
                        self.__frame_manager.add_to_frame(current_frame, alternative_bg_pipe, subframe_index = current_subframe)
                        self.__frame_manager.add_to_frame(current_frame, alternative_bg_cube, subframe_index = current_subframe)
                        previous_cube = alternative_cube
                        previous_kind = alternative_kind
                        previous_position = alternative_position

        # Prepare the first frame
        starting_frame = self.__frame_manager.get_frame_count() - 1
        self.__frame_manager.set_current_frame( starting_frame )
        actors = f"[actors={len(self.__plotter.actors)}]"
        console.info(f"Starting at frame {starting_frame+1}/{self.__frame_manager.get_frame_count()} {actors}")
        console.info(f"> {len(self.__cubes)} cubes, {len(self.__pipes)} pipes.")
        console.debug(f"> Actors : {self.__plotter.actors}")
        self.__frame_manager.log_frame_report()
        self.__reset_camera()

    def __reset_camera(self):
        # Initialise the camera for the BG Graph
        self.__plotter.camera.SetPosition(22, 14, 15)
        self.__plotter.camera.SetFocalPoint(0, 0, 0)
        self.__plotter.camera.SetViewUp(0, 0, 1)

    def alter_cube_appearance(self, cube: CubeId, highlight: bool = False):
        if cube in self.__cubes:
            self.__cubes[cube].alter_appearance(highlight = highlight)
        elif cube in self.__alternative_cubes:
            self.__alternative_cubes[cube].alter_appearance(highlight=highlight)
        else:
            console.error(f"Cube #{cube} not found in BG-scene.")

    def alter_pipe_appearance(self, source: CubeId, target: CubeId, highlight: bool = False):
        pipe = tuple(sorted((source, target)))
        if pipe in self.__pipes:
            self.__pipes[pipe].alter_appearance(highlight = highlight)
        elif pipe in self.__alternative_pipes:
            self.__alternative_pipes[pipe].alter_appearance(highlight=highlight)
        else:
            console.error(f"Pipe {pipe} not found in BG-scene.")

    def on_key_press(self, event):
        if   event.keypress == "Left":
            self.__frame_manager.move_frame(count = -1)
        elif event.keypress == "Right":
            self.__frame_manager.move_frame(count = +1)
        elif event.keypress == "Home":
            self.__frame_manager.move_frame(count = -self.__frame_manager.get_frame_count())
        elif event.keypress == "End":
            self.__frame_manager.move_frame(count = +self.__frame_manager.get_frame_count())
        elif event.keypress == "Up":
            self.__frame_manager.move_subframe_forward()
        elif event.keypress == "Down":
            self.__frame_manager.move_subframe_backward()

        self.__plotter.render(resetcam = False)

    # def on_left_click(self, event):
    #     if isinstance(event.object, BgCube):
    #         zx_node = self.__nx_graph.get_node(event.object.bg_cube)
    #         extra = f"[N{zx_node}]" if zx_node is not None else ""
    #         console.debug(f"Clicked on Cube #{event.object.bg_cube} {extra}")
    #         event.object.toggle_highlight()
    #
    #     if isinstance(event.object, BgPipe):
    #         console.debug(f"Clicked on Pipe  {event.object.bg_source}-{event.object.bg_target}")
    #         event.object.toggle_highlight()