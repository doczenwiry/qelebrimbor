import random
import pyzx as zx
import networkx as nx

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph

SEED = 42
QUBITS = 5
LAYERS = 10

if __name__ == "__main__":
    random.seed(SEED)
    pyzx_graph = zx.generate.cnots(qubits = QUBITS, depth = LAYERS)
    zx.draw(pyzx_graph, labels = True)
    azx = AugmentedZxGraph.from_pyzx_graph(pyzx_graph)

    cycles = [sorted(cycle) for cycle in nx.cycle_basis(azx)]
    cycles = sorted(cycles, key = len, reverse = True)
    for cycle in cycles:
        print(f"> {cycle}")