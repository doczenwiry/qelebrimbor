from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.components import ZxNode, ZxEdge, BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph


class Ring:
    def __init__(self, anchor: BgCube, nodes: list[ZxNode], edges: list[ZxEdge]):
        self.nodes = nodes
        self.edges = edges
        self.cubes: list[BgCube] = [ anchor ]
        self.occupied = { anchor.position }

    def get_terminal(self):
        return self.cubes[-1]

    def manhattan_distance_anchor(self) -> int:
        return self.cubes[0].position.get_manhattan_distance(self.cubes[-1].position)

    def manhattan_length(self):
        return len(self.cubes)

    def occupies(self, position: Coordinates):
        return position in self.occupied

    def append(self, cube: BgCube):
        self.cubes.append(cube)
        self.occupied.add(cube.position)

    def copy(self):
        cp = Ring(self.cubes[0], self.nodes, self.edges)
        cp.cubes.extend(self.cubes[1:])
        cp.occupied = set(self.occupied)
        return cp

    def to_nodes_specifications(self):
        return { self.nodes[nd].id: self.cubes[nd] for nd in range(len(self.nodes)) }

    def to_edges_specifications(self, graph: VolumetricZxGraph):
        node_count = len(self.nodes)
        cube_count = len(self.cubes)

        edges_specifications = {}

        for i in range(node_count-1):
            source = self.nodes[ i ]
            target = self.nodes[i+1]
            edges_specifications[ (source.id, target.id) ] = PathSpecification(
                source_cube = graph.get_zx_node(source.id).realising_cube,
                target_cube = graph.get_zx_node(target.id).realising_cube,
                extras = [], pipes = [self.edges[i].type]
            )

        start = self.nodes[ 0 ].id
        final = self.nodes[-1 ].id
        cubes = self.cubes[node_count : cube_count]
        if start > final:
            start, final = final, start
        else:
            cubes = list(reversed(cubes))
        edges_specifications[(start, final)] = PathSpecification(
                source_cube = graph.get_zx_node(start).realising_cube,
                target_cube = graph.get_zx_node(final).realising_cube,
                extras = cubes,
                pipes = [ self.edges[-1].type if i == 0 else EdgeType.IDENTITY for i in range(cube_count - node_count + 1)]
        )

        return edges_specifications

    def __str__(self):
        return f"{self.cubes[0]} - {self.cubes[1:]}"

    def __repr__(self):
        return str(self)