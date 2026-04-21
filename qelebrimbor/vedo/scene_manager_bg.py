from collections import deque

from vedo.plotter.runtime import Plotter  # type: ignore[import-untyped]

from qelebrimbor.common.attributes_zx import EdgeId
from qelebrimbor.common.attributes_bg import CubeId, PipeId
from qelebrimbor.vedo.bg_painter.default import DefaultBlockGraphPainter
from qelebrimbor.vedo.bg_painter.grayscale import GrayscaleBlockGraphPainter
from qelebrimbor.vedo.bg_painter.shaded import ShadedBlockGraphPainter
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.shapes_bg import VdCube, VdPipe

from logging import getLogger
console = getLogger(__name__)

class BgSceneManager:
    def __init__(self, vzx: VolumetricZxGraph, plotter: Plotter):
        self.__plotter = plotter
        self.__vzx_graph = vzx

        self.__cubes = dict()
        self.__pipes = dict()
        self.__painters = [ ShadedBlockGraphPainter(), DefaultBlockGraphPainter(), GrayscaleBlockGraphPainter()]
        self.__painter_index = 0

        for cube in vzx.get_bg_cubes():
            vd_cube = VdCube(cube = cube, painter = self.__painters[self.__painter_index])
            self.__cubes[ cube.id ] = vd_cube
            self.__plotter.add( vd_cube )

        for bg_pipe in vzx.get_bg_pipes():
            source_cube = vzx.get_bg_cube(bg_pipe.source)
            target_cube = vzx.get_bg_cube(bg_pipe.target)
            if source_cube.id > target_cube.id:
                source_cube, target_cube = target_cube, source_cube
            vd_pipe = VdPipe(source_cube, target_cube, bg_pipe.type, painter = self.__painters[self.__painter_index])
            self.__pipes[ source_cube.id, target_cube.id ] = vd_pipe
            self.__plotter.add( vd_pipe )

        # Prepare the first frame
        console.info(f"> {len(self.__cubes)} cubes, {len(self.__pipes)} pipes.")
        console.debug(f"> Actors : {self.__plotter.actors}")

    def alter_cube_appearance(self, selected: CubeId, highlight: bool = False):
        if selected == -1:
            console.error(f"Cube #{selected} not found in BG-scene.")
        else:
            alpha = 0.025 if highlight else 1.0

            equivalent_cubes, connecting_pipes = self.__vzx_graph.get_equivalent_bg_cubes(selected)

            for cube in self.__cubes:
                if cube not in equivalent_cubes:
                    self.__cubes[cube].alpha(alpha)

            for pipe in self.__pipes:
                if pipe not in connecting_pipes:
                    self.__pipes[pipe].alpha(alpha)

    def alter_pipes_appearance(self, *pipes: PipeId, highlight: bool = False):
        cubes: set[CubeId] = set()
        piping: set[PipeId] = set()

        for source, target in pipes:
            equivalent_sources, connecting_sources = self.__vzx_graph.get_equivalent_bg_cubes(source)
            equivalent_targets, connecting_targets = self.__vzx_graph.get_equivalent_bg_cubes(target)
            cubes.update( equivalent_sources )
            cubes.update( equivalent_targets )
            piping.update( connecting_sources )
            piping.update( connecting_targets )

        alpha = 0.025 if highlight else 1.0

        for pipe in self.__pipes:
            if pipe not in piping and pipe not in pipes:
                self.__pipes[ *pipe ].alpha(alpha)

        for cube in self.__cubes:
            if cube not in cubes:
                self.__cubes[ cube ].alpha(alpha)

    def alter_cycle_appearance(self, cycle: list[EdgeId], highlight: bool = False):
        pipes = set()
        for edge in cycle:
            pipes.update(self.__vzx_graph.get_zx_edge(*edge).realisation)
        self.alter_pipes_appearance(*pipes, highlight = highlight)

    def on_key_press(self, event):
        if event.keypress == "p":
            self.__painter_index = (self.__painter_index + 1) % len(self.__painters)
            for cube in self.__cubes.values():
                cube.paint(self.__painters[self.__painter_index])
            for pipe in self.__pipes.values():
                pipe.paint(self.__painters[self.__painter_index])
        self.__plotter.render(resetcam = False)