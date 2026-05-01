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

from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.components import ZxNode, ZxEdge, BgCube
from qelebrimbor.common.attributes_zx import NodeId, EdgeId, EdgeType
from qelebrimbor.common.path import Path


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

    def to_edges_specifications(self, edges: list[ZxEdge]) -> dict[EdgeId, Path]:
        edge_count = len(edges)
        cube_count = len(self.cubes)

        edges_specifications = {}

        for i in range(edge_count-1):
            source = edges[i].source
            target = edges[i].target
            if source.id > target.id:
                source, target = target, source
            path = Path(start = source.realising_cube).extend(target.realising_cube, edges[i].type)
            edges_specifications[ (source.id, target.id) ] = path

        start = edges[-1].target
        final = edges[-1].source
        cubes = self.cubes[edge_count : cube_count]
        if start.id > final.id:
            start, final = final, start
        else:
            cubes = list(reversed(cubes))
        path = Path(start = start.realising_cube)
        for cube, pipe in zip(cubes, [ edges[-1].type if i == 0 else EdgeType.IDENTITY for i in range(cube_count - edge_count + 1)]):
            path = path.extend(cube, pipe)
        path = path.extend(final.realising_cube, EdgeType.IDENTITY)
        edges_specifications[(start.id, final.id)] = path

        return edges_specifications

    def __str__(self):
        return f"{self.cubes[0]} - {self.cubes[1:]}"

    def __repr__(self):
        return str(self)