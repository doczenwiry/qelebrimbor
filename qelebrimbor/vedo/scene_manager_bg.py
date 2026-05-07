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

from vedo.plotter.runtime import Plotter  # type: ignore[import-untyped]

from qelebrimbor.core.components import BgCube, ZxEdge, BgPipe
from qelebrimbor.vedo.bg_painter.default import DefaultBlockGraphPainter
from qelebrimbor.vedo.bg_painter.grayscale import GrayscaleBlockGraphPainter
from qelebrimbor.vedo.bg_painter.shaded import ShadedBlockGraphPainter
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.shapes_bg import VdCube, VdPipe

from logging import getLogger
console = getLogger(__name__)

class BgSceneManager:
    def __init__(self, vzx: VolumetricZxGraph, plotter: Plotter):
        self.__plotter = plotter
        self.__vzx_graph = vzx

        self.__cubes: dict[BgCube, VdCube] = dict()
        self.__pipes: dict[BgPipe, VdPipe] = dict()
        self.__painters = [ ShadedBlockGraphPainter(), DefaultBlockGraphPainter(), GrayscaleBlockGraphPainter()]
        self.__painter_index = 0

        for cube in vzx.get_bg_cubes():
            vd_cube = VdCube(cube = cube, painter = self.__painters[self.__painter_index])
            self.__cubes[ cube ] = vd_cube
            self.__plotter.add( vd_cube )

        for pipe in vzx.get_bg_pipes():
            source_cube = pipe.source
            target_cube = pipe.target
            if source_cube.id > target_cube.id:
                source_cube, target_cube = target_cube, source_cube
            vd_pipe = VdPipe(source_cube, target_cube, pipe.type, pipe, painter = self.__painters[self.__painter_index])
            self.__pipes[ pipe ] = vd_pipe
            self.__plotter.add(vd_pipe)

        # Prepare the first frame
        console.info(f"> {len(self.__cubes)} cubes, {len(self.__pipes)} pipes.")

    def alter_cube_highlighting(self, selected: BgCube, highlight: bool = False):
        if selected is None:
            console.error(f"Cube #{selected} not found in BG-scene.")
        else:
            alpha = 0.025 if highlight else 1.0

            # TODO: adapt to toggle whether all equivalent cubes should be shown or only the "original" one
            # for bg_cube, vd_cube in self.__cubes.items():
            #     if bg_cube != selected:
            #         vd_cube.alpha(alpha)

            equivalent_cubes, connecting_pipes = self.__vzx_graph.get_equivalent_bg_cubes(selected)

            for bg_cube, vd_cube in self.__cubes.items():
                if bg_cube not in equivalent_cubes:
                    vd_cube.alpha(alpha)

            for bg_pipe, vd_pipe in self.__pipes.items():
                if bg_pipe not in connecting_pipes:
                    vd_pipe.alpha(alpha)

    def alter_path_highlighting(self, *pipes: BgPipe, highlight: bool = False):
        cubes: set[BgCube] = set()
        # for pipe in pipes:
        #     cubes.add(pipe.source)
        #     cubes.add(pipe.target)

        piping: set[BgPipe] = set()

        for pipe in pipes:
            equivalent_sources, connecting_sources = self.__vzx_graph.get_equivalent_bg_cubes(pipe.source)
            equivalent_targets, connecting_targets = self.__vzx_graph.get_equivalent_bg_cubes(pipe.target)
            cubes.update( equivalent_sources )
            cubes.update( equivalent_targets )
            piping.update( connecting_sources )
            piping.update( connecting_targets )

        alpha = 0.025 if highlight else 1.0

        for bg_pipe, vd_pipe in self.__pipes.items():
            if bg_pipe not in pipes and bg_pipe not in piping:
                vd_pipe.alpha(alpha)

        for bg_cube, vd_cube in self.__cubes.items():
            if bg_cube not in cubes:
                vd_cube.alpha(alpha)

    def alter_cycle_highlighting(self, cycle: list[ZxEdge], highlight: bool = False):
        pipes = set()
        for edge in cycle:
            pipes.update(edge.realisation)
        self.alter_path_highlighting(*pipes, highlight = highlight)

    def on_key_press(self, event):
        if event.keypress == "p":
            self.__painter_index = (self.__painter_index + 1) % len(self.__painters)
            for cube in self.__cubes.values():
                cube.paint(self.__painters[self.__painter_index])
            for pipe in self.__pipes.values():
                pipe.paint(self.__painters[self.__painter_index])
        self.__plotter.render(resetcam = False)