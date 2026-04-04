import random
import pyzx as zx

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.utilities.cycle_analyser import CycleAnalyser

SEED = 42
QUBITS = 4
LAYERS = 10

import logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    random.seed(SEED)
    pyzx_graph = zx.generate.cnots(qubits = QUBITS, depth = LAYERS)
    zx.draw(pyzx_graph, labels = True)
    zx.full_reduce(pyzx_graph)
    zx.draw(pyzx_graph, labels = True)
    azx = AugmentedZxGraph.from_pyzx_graph(pyzx_graph)

    CycleAnalyser.analyse(azx)