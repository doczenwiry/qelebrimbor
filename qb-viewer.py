from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.vedo.azg_viewer import AugmentedZxGraphViewer

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('qelebrimbor.utils').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.helpers').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.vedo').setLevel(logging.DEBUG)

if __name__ == '__main__':
    ang: AugmentedZxGraph = AugmentedZxGraph.from_file("assets/ang/ghz8.ang")

    print(type(ang))

    viewer = AugmentedZxGraphViewer(ang, label ="ghz8")
    viewer.display()