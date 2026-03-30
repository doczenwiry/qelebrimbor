from typing import Iterable

import pyzx as zx
from pyzx import VertexType
import networkx as nx
import matplotlib.pyplot as plt

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_bg import PipeId, CubeKind
from qelebrimbor.common.components_zx import NodeId, EdgeId, NodeType, EdgeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
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

# TODO: split into two parameters; cubes and pipes
def realise_ring(
    azx: AugmentedZxGraph,
    cubes: list[tuple[CubeKind, Coordinates]],
    connections: Iterable[tuple[EdgeId, PipeId]] = None
):
    for i in range(len(cubes)):
        azx.realise_node(i, *cubes[i])

    if connections is None:
        connections = []
        for edge in azx.get_edges():
            pipe = tuple(sorted( (azx.get_cube(edge[0]), azx.get_cube(edge[1])) ))
            connections.append( (edge , pipe) )

    for edge, pipe in connections:
        source, target = edge
        source_cube, target_cube = pipe
        azx.connect_pipe(source_cube, target_cube, pipe_type = EdgeType.IDENTITY)
        azx.get_edge_data(source, target)[AugmentedZxGraph.KEY_ZX_EDGE_BG_PATH] = [ pipe ]
        azx.get_edge_realisation_order().append( (source, target) )

def convert_ring(cubes: list[str], steps: list[str] = None, positions: list[tuple[int,int,int]] = None):
    ring = []
    connections = None
    if steps is not None:
        if len(cubes) != len(steps) + 1:
            raise Exception("Inconsistent path specification.")

        position = Spacetime.ORIGIN
        ring.append( (CubeKind[cubes[0]], position) )
        for idx in range(len(steps)):
            position += Step[steps[idx]].value
            ring.append( (CubeKind[cubes[idx+1]] , position) )
    elif positions is not None:
        if len(cubes) != len(positions):
            raise Exception("Inconsistent path realisation.")

        for cube, position in zip(cubes, positions):
            ring.append( (CubeKind[cube], Coordinates.from_tuple(position)) )

        connections = []

    return ring, connections

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
        cubes = [ 'XZZ' for _ in range(N) ],
        steps = [ 'YP', 'YP', 'ZP', 'ZP', 'YM', 'YM', 'ZM' ]
    ),
    1 : convert_ring(
        cubes=['ZZX', 'ZXX', 'ZZX', 'ZZX', 'ZZX', 'ZZX', 'ZZX', 'ZZX'],
        steps=['YP', 'YP', 'XP', 'XP', 'YM', 'YM', 'XM']
    ),
    2 : convert_ring(
        cubes=['ZXX', 'ZXX', 'ZZX', 'ZZX', 'ZZX', 'ZZX', 'ZZX', 'ZZX'],
        steps=['YP', 'YP', 'XP', 'YM', 'YM', 'YM', 'XM']
    ),
    3 : convert_ring(
        cubes=['ZZX', 'ZXX', 'ZZX', 'ZZX', 'ZZX', 'ZZX', 'ZZX', 'XZX'],
        steps=['YP', 'YP', 'XP', 'XP', 'YM', 'YM', 'XM']
    ),
    4 : convert_ring(
        cubes=['XZX', 'ZZX', 'ZZX', 'XZX', 'XZZ', 'XZZ', 'XZZ', 'XZZ'],
        steps=['XP', 'YP', 'XM', 'ZP', 'ZP', 'YM', 'ZM']
    ),
    5 : convert_ring(
        cubes=['XZZ', 'XZZ', 'XZZ', 'XZX', 'XZZ', 'XZZ', 'XZZ', 'XZX'],
        steps=['YP', 'YP', 'ZP', 'ZP', 'YM', 'YM', 'ZM']
    ),
    9 : convert_ring(
        cubes=['ZZX', 'ZZX', 'ZZX', 'XZX', 'ZZX', 'ZXX', 'ZZX', 'XZX'],
        steps=['YP', 'YP', 'XP', 'XP', 'YM', 'YM', 'XM']
    ),
    10 : convert_ring(
        cubes = ['XZX', 'ZZX', 'ZZX', 'ZXX', 'ZXZ', 'XXZ', 'XZZ', 'XZZ'],
        steps = ['XP', 'YP', 'YP', 'ZP', 'XM', 'YM', 'YM']
    ),
    13 : convert_ring(
        cubes = [ 'XXZ', 'XXZ', 'XXZ' ],
        positions = [ (0,0,0), (0,1,0), (1,1,0) ]
    ),
    14 : convert_ring(
        cubes = ['XZX', 'ZZX', 'ZXX', 'ZXX', 'ZXZ', 'XXZ', 'XZZ', 'XZZ'],
        steps = [ 'XP', 'YP', 'ZP', 'ZP', 'XM', 'YM', 'ZM' ]
    ),
    16 : convert_ring(
        cubes = [ 'ZXX', 'ZXX', 'ZXZ', 'ZXZ', 'ZXX', 'ZXX', 'ZXZ', 'ZXZ' ],
        steps = ['YP', 'ZP', 'ZP', 'ZP', 'YM', 'ZM', 'ZM']
    ),
    17 : convert_ring(
        cubes = [ 'ZXX', 'ZZX', 'ZXX', 'ZXZ', 'ZXX', 'ZZX', 'ZXX', 'ZXZ' ],
        steps = ['YP', 'YP', 'ZP', 'ZP', 'YM', 'YM', 'ZM']
    )
}

skipped_cases = range(13)

if __name__ == "__main__":
    missing = 0
    for c in range(len(zx_rings)):
        pyzx_ring = zx_rings[c]
        graph = AugmentedZxGraph.from_pyzx_graph(pyzx_ring)
        print(f"Case #{c} [PS:{count_plane_switches(graph)}]")
        if c in bg_cases and c not in skipped_cases:
            cubes, connections = bg_cases[c]
            realise_ring(graph, cubes, connections)
            viewer = AugmentedZxGraphViewer(graph, label=f"Case {c}")
            viewer.display()
        else:
            zx.draw(pyzx_ring, labels=True)
            print(f"> Missing realisation.")
            missing += 1

    print(f"Total number of cases: {len(zx_rings)}")
    print(f"Missing realisations : {missing}")