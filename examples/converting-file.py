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