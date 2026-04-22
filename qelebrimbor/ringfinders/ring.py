from qelebrimbor.common.attributes_zx import NodeId, EdgeId, EdgeType
from qelebrimbor.common.components import ZxNode, ZxEdge, BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph


class Ring:
    def __init__(self, anchor: BgCube):
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
        cp = Ring(self.cubes[0])
        cp.cubes.extend(self.cubes[1:])
        cp.occupied = set(self.occupied)
        return cp

    def to_nodes_specifications(self, nodes: list[ZxNode]) -> dict[NodeId, BgCube]:
        return { nodes[nd].id : self.cubes[nd] for nd in range(len(nodes)) }

    def to_edges_specifications(self, graph: VolumetricZxGraph, edges: list[ZxEdge]) -> dict[EdgeId, PathSpecification]:
        edge_count = len(edges)
        cube_count = len(self.cubes)

        edges_specifications = {}

        for i in range(edge_count-1):
            source = edges[i].source
            target = edges[i].target
            if source > target:
                source, target = target, source
            edges_specifications[ (source.id, target.id) ] = PathSpecification(
                source_cube = source.realising_cube,
                target_cube = target.realising_cube,
                extras = [], pipes = [ edges[i].type ]
            )

        start = edges[-1].target
        final = edges[-1].source
        cubes = self.cubes[edge_count : cube_count]
        if start.id > final.id:
            start, final = final, start
        else:
            cubes = list(reversed(cubes))
        edges_specifications[(start.id, final.id)] = PathSpecification(
                source_cube = start.realising_cube,
                target_cube = final.realising_cube,
                extras = cubes,
                pipes = [ edges[-1].type if i == 0 else EdgeType.IDENTITY for i in range(cube_count - edge_count + 1)]
        )

        return edges_specifications

    def __str__(self):
        return f"{self.cubes[0]} - {self.cubes[1:]}"

    def __repr__(self):
        return str(self)