import random
import pyzx as zx

from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

SEED = 42
QUBITS = 4
LAYERS = 10

import logging
logging.basicConfig(level=logging.INFO)

random.seed(SEED)
if __name__ == "__main__":
    pyzx_graph = zx.generate.cnots(qubits = QUBITS, depth = LAYERS)
    zx.draw(pyzx_graph, labels = True)
    zx.full_reduce(pyzx_graph)
    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_graph)

    CycleBasisAnalyser.analyse(vzx)

    viewer = VolumetricZxGraphViewer(vzx, label = f"random-s{SEED}-q{QUBITS}-d{LAYERS}")
    viewer.display()