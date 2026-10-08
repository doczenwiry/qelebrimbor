from unittest import TestCase

from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType
from qelebrimbor.formats.tqec import TQEC


class TestTQEC(TestCase):
    def test_into_dae_file(self):
        graph = VolumetricZxGraph()

        cube1 = BgCube(CubeKind.XZZ, Coordinates(0, 0, 0))
        cube2 = BgCube(CubeKind.XZZ, Coordinates(1, 0, 0))

        graph.place_cube(cube1)
        graph.place_cube(cube2)
        graph.connect_pipe(cube1, cube2, EdgeType.IDENTITY)

        output_file = "test_output.dae"

        TQEC.into_dae_file(graph, output_file)

        from pathlib import Path

        self.assertTrue(Path(output_file).exists())