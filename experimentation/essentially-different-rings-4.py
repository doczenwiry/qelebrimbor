import pyzx as zx
from pyzx import VertexType

import networkx as nx

from qelebrimbor.common.components import BgCube
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeId, NodeType, EdgeId, EdgeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import SpacetimeHelper, Step
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

N = 4
QUBITS = [0, 0, 1, 1]
LAYERS = [0, 1, 1, 0]

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
    vzx: VolumetricZxGraph,
    cubes: list[tuple[CubeKind, Coordinates]],
    links: dict[EdgeId, EdgeId] | None = None
):
    if links is None:
        links = dict()

    for i in range(len(cubes)):
        vzx.realise_zx_node(i, BgCube(*cubes[i]))

    for zx_edge in vzx.get_zx_edges():
        edge = (zx_edge.source, zx_edge.target)
        source, target = links[edge] if edge in links else edge
        source_cube = vzx.get_bg_cube(vzx.get_zx_node(source).realising_cube)
        target_cube = vzx.get_bg_cube(vzx.get_zx_node(target).realising_cube)
        pipe = (source_cube.id, target_cube.id)
        vzx.connect_pipe(source_cube, target_cube, pipe_type = EdgeType.IDENTITY)
        vzx.get_zx_edge(source, target).realisation = [pipe]

def convert_ring(
        cubes: list[str],
        steps: list[str] | None = None,
        positions: list[tuple[int,int,int]] | None = None
) -> list[tuple[CubeKind, Coordinates]]:
    ring = []
    if steps is not None:
        if len(cubes) != len(steps) + 1:
            raise Exception("Inconsistent path specification.")

        position = SpacetimeHelper.ORIGIN
        ring.append( (CubeKind[cubes[0]], position) )
        for idx in range(len(steps)):
            position += Step[steps[idx]].value
            ring.append( (CubeKind[cubes[idx+1]] , position) )
    elif positions is not None:
        if len(cubes) != len(positions):
            raise Exception("Inconsistent path realisation.")

        for cube, pos in zip(cubes, positions):
            ring.append( (CubeKind[cube], Coordinates.from_tuple(pos)) )

    return ring

def count_plane_switches(azx: VolumetricZxGraph):
    return sum(nx.number_connected_components(
            azx.subgraph(filter(lambda nd: azx.get_zx_node(nd).type == node_type, azx.nodes()))
        ) for node_type in [ NodeType.X, NodeType.Z ]
    )

zx_rings = [
    # Case 0
    generate_ring(N, []),
    # Case 1
    generate_ring(N, [0]),
    # Case 2
    generate_ring(N, [0,1]),
    generate_ring(N, [0,2])
]

bg_cases = {
    0 : convert_ring(
        cubes = [ 'XZZ' for _ in range(N) ],
        positions = [ (0,0,0) , (0,1,0) , (0,1,1) , (0,0,1) ]
    ),
    # 1 : convert_ring(
    #     cubes = [ 'XXZ', 'ZXZ', 'ZXZ', 'ZXZ', 'ZXZ' ,'ZXZ' ],
    #     steps = [ 'XP', 'ZP', 'XM', 'XM', 'ZM' ]
    # )
}

# Represents the displacement of edges to reduce overall volume when needed
bg_links: dict[int, dict[EdgeId, EdgeId]] = {

}

if __name__ == "__main__":
    missing = 0
    for c in range(len(zx_rings)):
        pyzx_ring = zx_rings[c]
        graph = VolumetricZxGraph.from_pyzx_graph(pyzx_ring)
        zx.draw(pyzx_ring, labels=True)
        print(f"Case #{c} [PS:{count_plane_switches(graph)}]")
        if c in bg_cases:
            cubes = bg_cases[c]
            links = bg_links[c] if c in bg_links else None
            realise_ring(graph, cubes, links)
            viewer = VolumetricZxGraphViewer(graph, label=f"Case {c}")
            viewer.display()
        else:
            print(f"> Missing realisation.")
            missing += 1

    print(f"Total number of cases: {len(zx_rings)}")
    print(f"Missing realisations : {missing}")