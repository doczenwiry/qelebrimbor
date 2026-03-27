import pyzx as zx
from pyzx import VertexType

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.path import Path
from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.vedo.azg_viewer import AugmentedZxGraphViewer

qubits = [0, 0, 0, 1, 2, 2, 2, 1]
layers = [0, 1, 2, 2, 2, 1, 0, 0]

def generate_ring(vtypes : list[VertexType]):
    graph = zx.Graph()

    for i in range(len(vtypes)):
        graph.add_vertex(ty = vtypes[i], qubit = qubits[i], row = layers[i])

    for i in range(n):
        graph.add_edge( (i, (i+1) % n) )

    return graph

def realise_ring(azx: AugmentedZxGraph, cubes: list[tuple[CubeKind, Coordinates]]):
    for i in range(azx.number_of_nodes()):
        azx.realise_node(i, *cubes[i])

    for source, target in azx.edges():
        azx.realise_edge(source, target, Path(source, target))

n = 8
zx_cases = [
    # Case 0
    [ VertexType.X for _ in range(n) ],
    # Case 1
    [ VertexType.Z if i in [0] else VertexType.X for i in range(n) ],
    # Case 2
    [VertexType.Z if i in [0, 1] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 2] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 3] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 4] else VertexType.X for i in range(n)],
    # Case 3
    [VertexType.Z if i in [0, 1, 2] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 1, 3] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 1, 4] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 2, 4] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 2, 5] else VertexType.X for i in range(n)],
    # Case 4
    [VertexType.Z if i in [0, 1, 2, 3] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 1, 2, 4] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 1, 2, 5] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 2, 3, 5] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 2, 3, 6] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 1, 4, 5] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 2, 4, 6] else VertexType.X for i in range(n)]
]

bg_cases = [
    [ (CubeKind.XZZ, position) for position in [
        Coordinates(0,0,0), Coordinates(0,1,0), Coordinates(0,2,0), Coordinates(0,2,1),
        Coordinates(0,2,2), Coordinates(0,1,2), Coordinates(0,0,2), Coordinates(0,0,1)
    ]],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [ (CubeKind.ZXX, Coordinates(0,0,0)), (CubeKind.ZZX, Coordinates(0,1,0)), (CubeKind.ZXX, Coordinates(0,2,0)),
      (CubeKind.ZXZ, Coordinates(0,2,1)), (CubeKind.ZXX, Coordinates(0,2,2)), (CubeKind.ZZX, Coordinates(0,1,2)),
      (CubeKind.ZXX, Coordinates(0,0,2)), (CubeKind.ZXZ, Coordinates(0,0,1))
    ]
]

cases_shown = [0, 17]

if __name__ == "__main__":
    for c in range(len(zx_cases)):
        pyzx_graph = generate_ring(vtypes = zx_cases[c])
        zx.draw(pyzx_graph, labels = True)
        graph = AugmentedZxGraph.from_pyzx_graph(pyzx_graph)
        if len(bg_cases[c]) > 0:
            realise_ring(graph, bg_cases[c])
        for cube in graph.get_cubes():
            print(f"Cube #{cube} : {graph.get_cube_kind(cube)}@{graph.get_cube_position(cube)}")
        if c in cases_shown:
            viewer = AugmentedZxGraphViewer(graph, label = f"Case {c}")
            viewer.display()
    print(f"Total number of cases: {len(zx_cases)}")