import sys

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise Exception("Filepath to a *.vzx file required.")

    filepath = sys.argv[1]
    console.info(f"Visualisation of {filepath}.")

    vzx: VolumetricZxGraph = VolumetricZxGraph.from_file(filepath)
    vzx.log_summary()

    excess_volume = 0
    for edge in vzx.edges:
        volume = len(vzx.get_edge_realisation(*edge)) - 1
        if volume > 0:
            console.info(f"Edge {edge} [+v={volume}] : {vzx.get_edge_realisation(*edge)}")
        excess_volume += volume

    boundaries = len(list(vzx.get_cubes(cube_kind = CubeKind.OOO)))
    console.info(f"Total volume : {vzx.number_of_cubes() - boundaries}")
    console.info(f"Excess volume: {excess_volume}")

    viewer = VolumetricZxGraphViewer(vzx, label = filepath)
    viewer.display()