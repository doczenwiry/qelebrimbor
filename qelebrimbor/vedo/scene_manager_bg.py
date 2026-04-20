from vedo.plotter.runtime import Plotter

from qelebrimbor.common.attributes_bg import CubeId, PipeId
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.shapes_bg import VdCube, VdPipe

from logging import getLogger
console = getLogger(__name__)

class BgSceneManager:
    def __init__(self, vzx: VolumetricZxGraph, plotter: Plotter):
        self.__plotter = plotter

        self.__cubes = dict()
        self.__pipes = dict()

        for cube in vzx.get_bg_cubes():
            vd_cube = VdCube(cube = cube)
            self.__cubes[ cube.id ] = vd_cube
            self.__plotter.add( vd_cube )

        for bg_pipe in vzx.get_bg_pipes():
            source_cube = vzx.get_bg_cube(bg_pipe.source)
            target_cube = vzx.get_bg_cube(bg_pipe.target)
            if source_cube.id > target_cube.id:
                source_cube, target_cube = target_cube, source_cube
            vd_pipe = VdPipe(source_cube, target_cube, bg_pipe.type)
            self.__pipes[ source_cube.id, target_cube.id ] = vd_pipe
            self.__plotter.add( vd_pipe )

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
        if cube != -1:
            if cube in self.__cubes:
                self.__cubes[cube].alter_appearance(highlight = highlight)
            else:
                console.error(f"Cube #{cube} not found in BG-scene.")

    def alter_pipes_appearance(self, *pipes: PipeId, highlight: bool = False):
        for pipe in pipes:
            if pipe in self.__pipes:
                source, target = pipe
                self.__cubes[ source ].alter_appearance(highlight = highlight)
                self.__cubes[ target ].alter_appearance(highlight = highlight)
                self.__pipes[ *pipe ].alter_appearance(highlight = highlight)
            else:
                console.error(f"Pipe {pipe} not found in BG-scene.")

    def on_key_press(self, event):
        self.__plotter.render(resetcam = False)