import pyzx as zx
from pyzx import VertexType

def generate_ring(vtypes : list[VertexType]):
    graph = zx.Graph()

    graph.add_vertex(ty = vtypes[0], qubit = 0, row = 1)
    graph.add_vertex(ty = vtypes[1], qubit = 1, row = 1)
    graph.add_vertex(ty = vtypes[2], qubit = 1, row = 2)
    graph.add_vertex(ty = vtypes[3], qubit = 2, row = 2)
    graph.add_vertex(ty = vtypes[4], qubit = 2, row = 3)
    graph.add_vertex(ty = vtypes[5], qubit = 3, row = 3)
    graph.add_vertex(ty = vtypes[6], qubit = 3, row = 4)
    graph.add_vertex(ty = vtypes[7], qubit = 0, row = 4)

    for i in range(n):
        graph.add_edge( (i, (i+1) % n) )

    # Add boundaries
    for q in range(4):
        graph.add_vertex(ty = VertexType.BOUNDARY, qubit = q, row = 0)
        graph.add_vertex(ty = VertexType.BOUNDARY, qubit = q, row = 5)

    graph.add_edge( (0,  8) )
    graph.add_edge( (1, 10) )
    graph.add_edge( (2, 11) )
    graph.add_edge( (3, 12) )
    graph.add_edge( (4, 13) )
    graph.add_edge( (5, 14) )
    graph.add_edge( (6, 15) )
    graph.add_edge( (7,  9) )

    return graph

n = 8
cases = [
    # Case 0
    [
        [ VertexType.X for _ in range(n) ]
    ],
    # Case 1
    [
        [ VertexType.Z if i in [0] else VertexType.X for i in range(n) ]
    ],
    # Case 2
    [
        [VertexType.Z if i in [0, s+1] else VertexType.X for i in range(n)] for s in range(4)
    ],
    # Case 3
    [
        [VertexType.Z if i in [0, 1, s+2] else VertexType.X for i in range(n)] for s in range(3)
    ] + [
        [VertexType.Z if i in [0, 2, s+4] else VertexType.X for i in range(n)] for s in range(2)
    ],
    # Case 4
    [
        [VertexType.Z if i in [0, 1, 2, s+3] else VertexType.X for i in range(n)] for s in range(3)
    ] + [
        [VertexType.Z if i in [0, 2, 3, s+5] else VertexType.X for i in range(n)] for s in range(2)
    ] + [
        [VertexType.Z if i in [0, 1, 4, 5] else VertexType.X for i in range(n)],
        [VertexType.Z if i in [0, 2, 4, 6] else VertexType.X for i in range(n)],
    ]
]

if __name__ == "__main__":
    total = 0
    for c in range( len(cases) ):
        print(f"Case {c} : #{len(cases[c])}")
        total += len(cases[c])
        for sc in range( len(cases[c]) ):
            zx_graph = generate_ring(vtypes = cases[c][sc])
            zx.draw(zx_graph, labels = True)
    print(f"Total number of cases: {total}")