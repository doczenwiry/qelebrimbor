#   Copyright 2026 Seweryn Dynerowicz
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import pyzx
import networkx as nx

from qelebrimbor.common.components import BgCube
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeId, EdgeId, NodeType, EdgeType
from qelebrimbor.common.coordinates import Coordinates

from qelebrimbor.helpers.spacetime import SpacetimeHelper, Step

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.formats.pyzx import PYZX
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

N = 8
QUBITS = [0, 0, 0, 1, 2, 2, 2, 1]
LAYERS = [0, 1, 2, 2, 2, 1, 0, 0]

def generate_ring(n, zs: list[NodeId]):
    ring = pyzx.Graph()
    vtypes = [ pyzx.VertexType.Z if i in zs else pyzx.VertexType.X for i in range(n) ]

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
        vzx.realise_zx_node(vzx.get_zx_node(i), BgCube(*cubes[i]))

    for zx_edge in vzx.get_zx_edges():
        source = zx_edge.source.id
        target = zx_edge.target.id
        edge = (source, target)
        source_cube = vzx.get_zx_node(links[edge][0] if edge in links else source).realising_cube
        target_cube = vzx.get_zx_node(links[edge][1] if edge in links else target).realising_cube
        pipe = (source_cube.id, target_cube.id)
        vzx.connect_pipe(source_cube, target_cube, pipe_type = EdgeType.IDENTITY)
        vzx.get_zx_edge(source, target).realisation = [pipe]

def convert_ring(
        cubes: list[str],
        steps: list[str] | None = None,
        positions: list[tuple[int,int,int]] | None = None
) -> list[tuple[CubeKind, Coordinates]]:
    ring: list[tuple[CubeKind, Coordinates]] = []
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
            ring.append( (CubeKind[cube], Coordinates(*pos)) )

    return ring

def count_plane_switches(vzx: VolumetricZxGraph):
    return sum(nx.number_connected_components(
            vzx.subgraph(filter(lambda nd: vzx.get_zx_node(nd).type == node_type, vzx.nodes()))
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
    6 : convert_ring(
        cubes = ['XXZ', 'XXZ', 'XXZ' , 'ZXZ', 'ZXZ', 'ZXZ', 'ZXZ', 'ZXZ'],
        positions = [(0,-1,0), (0,0,0), (0,1,0), (1,0,0), (1,0,-1), (0,0,-1), (-1,0,-1), (-1,0,0) ]
    ),
    8 : convert_ring(
        cubes = [ 'XXZ', 'XXZ', 'XZZ', 'XZZ', 'XXZ', 'XZZ', 'XZZ', 'XZZ' ],
        steps = [ 'YP', 'YP', 'ZM', 'YM', 'YM', 'YM', 'ZP']
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
        cubes = [ 'XXZ', 'XXZ', 'XXZ', 'XZZ', 'XZZ', 'XXZ', 'ZXZ', 'ZXZ' ],
        positions = [ (0,-1,0), (0,0,0), (-1,0,0), (0,1,0), (0,1,-1), (0,0,-1), (1,0,-1), (1,0,0) ]
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

# Represents the displacement of edges to reduce overall volume when needed
bg_links = {
    6 : {
        (0,7) : (1,7),
        (2,3) : (1,3)
    },
    13 : {
        (0,7) : (1,7),
        (2,3) : (1,3)
    }
}

skipped_cases: list[int] = [] #range(13)

if __name__ == "__main__":
    missing = 0
    for c in range(len(zx_rings)):
        pyzx_ring = zx_rings[c]
        graph = PYZX.from_pyzx_graph(pyzx_ring)
        pyzx.draw(pyzx_ring, labels=True)
        print(f"Case #{c} [PS:{count_plane_switches(graph)}]")
        if c in bg_cases:
            if c in skipped_cases:
                continue
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