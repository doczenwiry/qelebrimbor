import pyzx as zx

from qelebrimbor.augmented_nx_graph import AugmentedNxGraph
from qelebrimbor.vedo.ang_viewer import AugmentedNxGraphViewer

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('qelebrimbor.utils').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.helpers').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.vedo').setLevel(logging.DEBUG)

from jsonpickle import encode, decode
ANG_PATH = "assets/pickles/"
def ang_write(ang: AugmentedNxGraph, label: str):
    with open(ANG_PATH + label + ".json", "w") as f:
        f.write(encode(ang, indent=2, keys = True, unpicklable=True))

def ang_read(label: str):
    return decode(open(ANG_PATH + label + ".json").read(), keys = True)

if __name__ == '__main__':
    name = "ghz8"
    anx: AugmentedNxGraph = ang_read(label = name)

    print(type(anx))

    viewer = AugmentedNxGraphViewer(anx, label = name)
    viewer.display()