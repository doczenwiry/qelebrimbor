from itertools import repeat

import pyzx as zx
from pyzx import VertexType

import networkx as nx

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.components_zx import NodeId, NodeType, EdgeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.path import Path
from qelebrimbor.helpers.spacetime import Spacetime, Step
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

def convert_ring(cubes: list[CubeKind], steps: list[Coordinates]):
    if len(cubes) != len(steps) + 1:
        raise Exception("Inconsistent path specification.")

    position = Spacetime.ORIGIN
    ring = [ (cubes[0], position) ]
    for idx in range(len(steps)):
        position += steps[idx]
        ring.append( (cubes[idx+1] , position) )
    return ring

def count_plane_switches(azx: AugmentedZxGraph):
    return sum(nx.number_connected_components(
            azx.subgraph(filter(lambda nd: azx.get_node_type(nd) == node_type, azx.nodes()))
        ) for node_type in [ NodeType.X, NodeType.Z ]
    )

n = 8
zx_cases = [
    # Case 0
    [ VertexType.X for _ in range(n) ],
    # Case 1
    [ VertexType.Z if i in [1] else VertexType.X for i in range(n) ],
    # Case 2
    [VertexType.Z if i in [0, 1] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [1, 7] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 3] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [3, 7] else VertexType.X for i in range(n)],
    # Case 3
    [VertexType.Z if i in [0, 1, 2] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 1, 3] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 1, 4] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [3, 5, 7] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 3, 5] else VertexType.X for i in range(n)],
    # Case 4
    [VertexType.Z if i in [0, 1, 2, 3] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 1, 2, 4] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 1, 2, 5] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 2, 3, 5] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 2, 3, 6] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 1, 4, 5] else VertexType.X for i in range(n)],
    [VertexType.Z if i in [0, 2, 4, 6] else VertexType.X for i in range(n)]
]

bg_cases = {
    0 : convert_ring(
        cubes = [ CubeKind.XZZ for _ in range(n) ],
        steps = [ Step[stp].value for stp in ['YP', 'YP', 'ZP', 'ZP', 'YM', 'YM', 'ZM'] ]
    ),
    1 : convert_ring(
        cubes=[ CubeKind[knd] for knd in ['ZZX', 'ZXX', 'ZZX', 'ZZX', 'ZZX', 'ZZX', 'ZZX', 'ZZX'] ],
        steps=[ Step[stp].value for stp in ['YP', 'YP', 'XP', 'XP', 'YM', 'YM', 'XM'] ]
    ),
    2 : convert_ring(
        cubes=[ CubeKind[knd] for knd in ['ZXX', 'ZXX', 'ZZX', 'ZZX', 'ZZX', 'ZZX', 'ZZX', 'ZZX'] ],
        steps=[ Step[stp].value for stp in ['YP', 'YP', 'XP', 'YM', 'YM', 'YM', 'XM'] ]
    ),
    3 : convert_ring(
        cubes=[ CubeKind[knd] for knd in ['ZZX', 'ZXX', 'ZZX', 'ZZX', 'ZZX', 'ZZX', 'ZZX', 'XZX'] ],
        steps=[ Step[stp].value for stp in ['YP', 'YP', 'XP', 'XP', 'YM', 'YM', 'XM'] ]
    ),
    4 : convert_ring(
        cubes=[ CubeKind[knd] for knd in ['XZX', 'ZZX', 'ZZX', 'XZX', 'XZZ', 'XZZ', 'XZZ', 'XZZ'] ],
        steps=[ Step[stp].value for stp in ['XP', 'YP', 'XM', 'ZP', 'ZP', 'YM', 'ZM'] ]
    ),
    5 : convert_ring(
        cubes=[ CubeKind[knd] for knd in ['XZZ', 'XZZ', 'XZZ', 'XZX', 'XZZ', 'XZZ', 'XZZ', 'XZX'] ],
        steps=[ Step[stp].value for stp in ['YP', 'YP', 'ZP', 'ZP', 'YM', 'YM', 'ZM'] ]
    ),
    9 : convert_ring(
        cubes=[ CubeKind[knd] for knd in ['ZZX', 'ZZX', 'ZZX', 'XZX', 'ZZX', 'ZXX', 'ZZX', 'XZX'] ],
        steps=[ Step[stp].value for stp in ['YP', 'YP', 'XP', 'XP', 'YM', 'YM', 'XM'] ]
    ),
    10 : convert_ring(
        cubes = [ CubeKind[knd] for knd in ['XZX', 'ZZX', 'ZZX', 'ZXX', 'ZXZ', 'XXZ', 'XZZ', 'XZZ'] ],
        steps = [ Step[stp].value for stp in ['XP', 'YP', 'YP', 'ZP', 'XM', 'YM', 'YM'] ]
    ),
    14 : convert_ring(
        cubes = [ CubeKind[knd] for knd in ['XZX', 'ZZX', 'ZXX', 'ZXX', 'ZXZ', 'XXZ', 'XZZ', 'XZZ'] ],
        steps = [ Step[stp].value for stp in [ 'XP', 'YP', 'ZP', 'ZP', 'XM', 'YM', 'ZM' ] ]
    ),
    17 : convert_ring(
        cubes = [ CubeKind[knd] for knd in [ 'ZXX', 'ZZX', 'ZXX', 'ZXZ', 'ZXX', 'ZZX', 'ZXX', 'ZXZ' ] ],
        steps = [ Step[stp].value for stp in ['YP', 'YP', 'ZP', 'ZP', 'YM', 'YM', 'ZM'] ]
    )
}

ignored_cases = range(18)

if __name__ == "__main__":
    for c in range(len(zx_cases)):
        pyzx_graph = generate_ring(vtypes = zx_cases[c])
        graph = AugmentedZxGraph.from_pyzx_graph(pyzx_graph)
        zx.draw(pyzx_graph, labels=True)
        print(f"Case #{c} [PS:{count_plane_switches(graph)}]")
        if c in bg_cases:
            realise_ring(graph, bg_cases[c])
            viewer = AugmentedZxGraphViewer(graph, label=f"Case {c}")
            viewer.display()
        elif c not in ignored_cases:
            print(f"> Missing realisation.")

    print(f"Total number of cases: {len(zx_cases)}")