from qelebrimbor.augmented_zx_graph import AugmentedZxGraph

if __name__ == "__main__":
    ang = AugmentedZxGraph.from_file("../assets/ang/ghz8.ang")
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