import pyzx as zx
from pyzx import VertexType
import networkx as nx
import matplotlib.pyplot as plt

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.components_zx import NodeId, NodeType, EdgeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.path import Path
from qelebrimbor.helpers.spacetime import Spacetime, Step
from qelebrimbor.vedo.azg_viewer import AugmentedZxGraphViewer

N = 8
QUBITS = [0, 0, 0, 1, 2, 2, 2, 1]
LAYERS = [0, 1, 2, 2, 2, 1, 0, 0]

def generate_ring(n, zs: list[NodeId]):
    ring = zx.Graph()
    vtypes = [ VertexType.Z if i in zs else VertexType.X for i in range(n) ]

    for i in range(len(vtypes)):
        ring.add_vertex(ty = vtypes[i], qubit = QUBITS[i], row = LAYERS[i])

    for i in range(N):
        ring.add_edge((i, (i+1) % N))

    return ring

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

zx_rings = [
    # Case 0
    generate_ring(N, zs = []),
    # Case 1
    generate_ring(N, zs = [1]),
    # Case 2
    generate_ring(N, zs = [0, 1]),
    generate_ring(N, zs = [1, 7]),
    generate_ring(N, zs = [0, 3]),
    generate_ring(N, zs = [3, 7]),
    # Case 3
    generate_ring(N, zs = [0, 1, 2]),
    generate_ring(N, zs = [0, 1, 3]),
    generate_ring(N, zs = [0, 1, 4]),
    generate_ring(N, zs = [3, 5, 7]),
    generate_ring(N, zs = [0, 3, 5]),
    # Case 4
    generate_ring(N, zs = [0, 1, 2, 3]),
    generate_ring(N, zs = [0, 1, 2, 4]),
    generate_ring(N, zs = [0, 1, 2, 5]),
    generate_ring(N, zs = [0, 2, 3, 5]),
    generate_ring(N, zs = [0, 2, 3, 6]),
    generate_ring(N, zs = [0, 1, 4, 5]),
    generate_ring(N, zs = [0, 2, 4, 6]),
]

bg_cases = {
    0 : convert_ring(
        cubes = [CubeKind.XZZ for _ in range(N)],
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
    16 : convert_ring(
        cubes = [ CubeKind[knd] for knd in [ 'ZXX', 'ZXX', 'ZXZ', 'ZXZ', 'ZXX', 'ZXX', 'ZXZ', 'ZXZ' ] ],
        steps = [ Step[stp].value for stp in ['YP', 'ZP', 'ZP', 'ZP', 'YM', 'ZM', 'ZM'] ]
    ),
    17 : convert_ring(
        cubes = [ CubeKind[knd] for knd in [ 'ZXX', 'ZZX', 'ZXX', 'ZXZ', 'ZXX', 'ZZX', 'ZXX', 'ZXZ' ] ],
        steps = [ Step[stp].value for stp in ['YP', 'YP', 'ZP', 'ZP', 'YM', 'YM', 'ZM'] ]
    )
}

if __name__ == "__main__":
    missing = 0
    for c in range(len(zx_rings)):
        pyzx_ring = zx_rings[c]
        graph = AugmentedZxGraph.from_pyzx_graph(pyzx_ring)
        print(f"Case #{c} [PS:{count_plane_switches(graph)}]")
        if c in bg_cases:
            realise_ring(graph, bg_cases[c])
            viewer = AugmentedZxGraphViewer(graph, label=f"Case {c}")
            viewer.display()
        else:
            zx.draw(pyzx_ring, labels=True)
            print(f"> Missing realisation.")
            missing += 1

    print(f"Total number of cases: {len(zx_rings)}")
    print(f"Missing realisations : {missing}")