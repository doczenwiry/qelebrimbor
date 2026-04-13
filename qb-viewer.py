import sys

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

    viewer = VolumetricZxGraphViewer(vzx, label = filepath)
    viewer.display()