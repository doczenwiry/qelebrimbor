from qelebrimbor.augmented_nx_graph import AugmentedNxGraph

from jsonpickle import encode, decode
ANG_PATH = "../assets/pickles/"
def ang_write(graph: AugmentedNxGraph, label: str):
    with open(ANG_PATH + label + ".json", "w") as f:
        f.write(encode(graph, indent=2, keys = True, unpicklable=True))

def ang_read(label: str) -> AugmentedNxGraph:
    return decode(open(ANG_PATH + label + ".json").read(), keys = True)

if __name__ == "__main__":
    ang = ang_read("ghz8")
    ang.into_file("../assets/ang/ghz8.ang")

    ang2 = AugmentedNxGraph.from_file("../assets/ang/ghz8.ang")
    print(list(ang2.get_nodes()))
    print(list(ang2.get_edges()))
    print(list(ang2.get_qubits()))
    print(list(ang2.get_layers()))
    print(list(ang2.get_node_realisation_order()))
    print(list(ang2.get_edge_realisation_order()))
    print(list(ang2.get_cubes()))
    print(list(ang2.get_pipes()))