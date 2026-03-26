from qelebrimbor.augmented_nx_graph import AugmentedNxGraph

from jsonpickle import encode, decode
ANG_PATH = "../assets/pickles/"
def ang_write(graph: AugmentedNxGraph, label: str):
    with open(ANG_PATH + label + ".json", "w") as f:
        f.write(encode(graph, indent=2, keys = True, unpicklable=True))

def ang_read(label: str) -> AugmentedNxGraph:
    return decode(open(ANG_PATH + label + ".json").read(), keys = True)

if __name__ == "__main__":
    ang = AugmentedNxGraph.from_file("../assets/ang/ghz8.ang")
    print(list(ang.get_nodes()))
    print(list(ang.get_edges()))
    print(list(ang.get_qubits()))
    print(list(ang.get_layers()))
    print(list(ang.get_node_realisation_order()))
    print(list(ang.get_edge_realisation_order()))
    print(list(ang.get_cubes()))
    print(list(ang.get_pipes()))

    for edge in ang.get_edges():
        print(f"> {edge} : {ang.get_edge_realisation(*edge)}")

    ang.into_file("../assets/ang/ghz8-alternative.ang")