from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('qelebrimbor.utils').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.helpers').setLevel(logging.CRITICAL)
logging.getLogger("qelebrimbor.volumetric_zx_graph").setLevel(logging.DEBUG)
logging.getLogger('qelebrimbor.vedo').setLevel(logging.INFO)

if __name__ == '__main__':
    vzx: VolumetricZxGraph = VolumetricZxGraph.from_file("assets/vzx/ghz8.vzx")

    vzx.print_summary()

    viewer = VolumetricZxGraphViewer(vzx, label ="ghz8")
    viewer.display()