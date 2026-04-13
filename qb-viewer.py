from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('qelebrimbor.utils').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.helpers').setLevel(logging.CRITICAL)
logging.getLogger("qelebrimbor.volumetric_zx_graph").setLevel(logging.DEBUG)
logging.getLogger('qelebrimbor.vedo').setLevel(logging.INFO)

if __name__ == '__main__':
    circuit_name = "random_42_5_10"
    vzx: VolumetricZxGraph = VolumetricZxGraph.from_file(f"assets/vzx/{circuit_name}.vzx")

    vzx.log_summary()

    viewer = VolumetricZxGraphViewer(vzx, label = circuit_name)
    viewer.display()