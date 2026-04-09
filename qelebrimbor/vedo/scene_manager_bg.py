from vedo.plotter.runtime import Plotter

from qelebrimbor.common.components_bg import CubeId
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.shapes_bg import BgCube, BgPipe

from logging import getLogger
console = getLogger(__name__)

class BgSceneManager:
    def __init__(self, vzx: VolumetricZxGraph, plotter: Plotter):
        self.__nx_graph = vzx
        self.__plotter = plotter

        self.__cubes = dict()
        self.__pipes = dict()

        for cube in vzx.get_cubes():
            bg_cube = BgCube(kind = self.__nx_graph.get_cube_kind(cube),
                             position = self.__nx_graph.get_cube_position(cube),
                             nodes= self.__nx_graph.get_realised_nodes(cube),
                             cube = cube)
            self.__cubes[cube] = bg_cube

        for source, target in vzx.get_pipes():
            pipe = tuple(sorted((source, target)))
            source_kind = self.__nx_graph.get_cube_kind(source)
            target_kind = self.__nx_graph.get_cube_kind(target)
            source_position = self.__nx_graph.get_cube_position(source)
            target_position = self.__nx_graph.get_cube_position(target)
            pipe_type = self.__nx_graph.get_pipe_kind(source, target)
            bg_pipe = BgPipe(source_kind, source_position, target_kind, target_position, pipe_type, source, target)
            self.__pipes[pipe] = bg_pipe

        for _, bg_cube in self.__cubes.items():
            self.__plotter.add(bg_cube)

        for _, bg_pipe in self.__pipes.items():
            self.__plotter.add(bg_pipe)

        # Prepare the first frame
        console.info(f"> {len(self.__cubes)} cubes, {len(self.__pipes)} pipes.")
        console.debug(f"> Actors : {self.__plotter.actors}")
        self.__reset_camera()

    def __reset_camera(self):
        # Initialise the camera for the BG Graph
        self.__plotter.camera.SetPosition(22, 14, 15)
        self.__plotter.camera.SetFocalPoint(0, 0, 0)
        self.__plotter.camera.SetViewUp(0, 0, 1)

    def alter_cube_appearance(self, cube: CubeId, highlight: bool = False):
        if cube in self.__cubes:
            self.__cubes[cube].alter_appearance(highlight = highlight)
        else:
            console.error(f"Cube #{cube} not found in BG-scene.")

    def alter_pipe_appearance(self, source: CubeId, target: CubeId, highlight: bool = False):
        pipe = tuple(sorted((source, target)))
        if pipe in self.__pipes:
            self.__pipes[pipe].alter_appearance(highlight = highlight)
        else:
            console.error(f"Pipe {pipe} not found in BG-scene.")

    def on_key_press(self, event):
        self.__plotter.render(resetcam = False)