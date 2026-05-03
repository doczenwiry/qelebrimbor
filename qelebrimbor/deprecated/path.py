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

import numpy as np
from functools import total_ordering

from qelebrimbor.common.path import Path as NewPath
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeId, EdgeId, EdgeType
from qelebrimbor.common.components import ZxNode, BgCube, ZxEdge
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.deprecated.paths import PathSpecification
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import SpacetimeHelper

import logging
console = logging.getLogger(__name__)


# TODO: it might be relevant to rename this to Length to avoid confusion
type Distance = int


class Path:
    def __init__(self, source: BgCube, target: BgCube):
        self.source = source
        self.target = target
        self.extras: list[BgCube] = []
        self.occupied = { source.position }

    def get_terminal(self):
        return self.extras[-1] if len(self.extras) > 0 else self.source

    def has_reached_target(self, edge_type: EdgeType = EdgeType.IDENTITY):
        terminal = self.get_terminal()
        return BlockGraphHelper.connectable(terminal, self.target, edge_type)

    def overhead(self):
        return self.manhattan_length() - self.source.position.get_manhattan_distance(self.target.position)

    # @staticmethod
    # def minimal_volume_possible(source: BgCube, target: BgCube, count_endpoints: bool = True) -> int:
    #     return Path.minimal_length_possible(source, target) + (+1 if count_endpoints else -1)

    # @staticmethod
    # def minimal_length_possible(source: BgCube, target: BgCube) -> int:
    #     return source.position.get_manhattan_distance(target.position) + Path.minimal_overhead_possible(source, target)

    # @staticmethod
    # def minimal_overhead_possible(source: BgCube, target: BgCube) -> int:
    #     if source.kind in [ CubeKind.OOO , CubeKind.YYY ] or target.kind in [ CubeKind.OOO , CubeKind.YYY ]:
    #         return 0
    #
    #     overhead = 0
    #
    #     source_reach = source.kind.get_reach()
    #     target_reach = target.kind.get_reach()
    #
    #     manhattan = source.position.get_manhattan_distance(target.position)
    #     relative = target.position - source.position
    #
    #     if np.sign( source_reach.dot(relative) ) == -1:
    #         source_reach *= -1
    #     if np.sign( target_reach.dot(relative) ) == -1:
    #         target_reach *= -1
    #
    #     # TODO: work out the formalisation and justification of the cases for all the overhead values.
    #     if source.kind == target.kind:
    #         if manhattan >= 1 and relative == source_reach.scale(manhattan):
    #             overhead += 2
    #
    #         if manhattan >= 2:
    #             if any(relative == source_reach.scale(manhattan - 1) + step
    #                    for step in SpacetimeHelper.get_step_constellation(source_reach)
    #             ):
    #                 overhead += 2
    #
    #         if manhattan >= 3:
    #             if any(relative == source_reach.scale(manhattan-2) + step + source_reach.cross(step)
    #                    for step in SpacetimeHelper.get_step_constellation(source_reach)
    #             ):
    #                 overhead += 2
    #     else:
    #         differences = source.kind.differences(target.kind)
    #         overhead += sum(2 for i in range(3) if differences[i] == 1 and relative[i] == 0)
    #         if manhattan == 1:
    #             if source.kind.get_type() == target.kind.get_type():
    #                 overhead += 2
    #             elif source_reach == target_reach != relative:
    #                 overhead += 2
    #         elif manhattan == 2 and source.kind.get_type() != target.kind.get_type():
    #             if source_reach == target_reach != relative and source_reach.dot(relative) == 0 and relative.dot(relative) != 4:
    #                 overhead += 2
    #
    #     return overhead

    # def manhattan_distance_remaining(self) -> int:
    #     terminal = self.target if len(self.extras) == 0 else self.extras[-1]
    #     return terminal.position.get_manhattan_distance(self.target.position)

    def manhattan_length(self):
        return len(self.extras) + 1

    # def occupies(self, position: Coordinates):
    #     return position in self.occupied

    def append(self, cube: BgCube):
        self.extras.append(cube)
        self.occupied.add(cube.position)

    def copy(self):
        cp = Path(self.source, self.target)
        cp.extras.extend(self.extras)
        cp.occupied = set(self.occupied)
        return cp

    def to_nodes_specifications(self, nodes: list[ZxNode]) -> dict[NodeId, BgCube]:
        nodes_specifications: dict[NodeId, BgCube] = {}
        for nd in range(len(nodes)):
            nodes_specifications[nodes[nd].id] = self.extras[nd]
        return nodes_specifications

    def to_edges_specifications(self, edges: list[ZxEdge]) -> dict[EdgeId, NewPath]:
        edge_count = len(edges)
        extra_count = len(self.extras)
        edges_specifications: dict[EdgeId, NewPath] = {}

        previous_node = self.source.realised_node
        for edge in edges[:-1]: # range(edge_count-1):
            current_node = edge.source if edge.source != previous_node else edge.target
            path = NewPath(start = previous_node.realising_cube).extend(current_node.realising_cube, edge.type)
            edges_specifications[ (previous_node.id, current_node.id) ] = path
            previous_node = current_node

        final_edge = edges[-1]
        source = previous_node
        target = final_edge.source if final_edge.source != previous_node else final_edge.target
        extras = self.extras[edge_count-1 : extra_count]
        path = NewPath(start = source.realising_cube)
        for cube, pipe in zip(extras, [ final_edge.type if i == 0 else EdgeType.IDENTITY for i in range(extra_count - edge_count + 2)]):
            path = path.extend(cube, pipe)
        path = path.extend(target.realising_cube, EdgeType.IDENTITY)
        edges_specifications[(source.id, target.id)] = path

        return edges_specifications

    def to_specification(self, edge_type: EdgeType | None = None) -> PathSpecification:
        pipes = []
        previous = self.source
        for current in self.extras:
            pipes.append( next(iter(BlockGraphHelper.infer_pipe_type(previous.kind, current.kind))) )
            previous = current
        if self.target.kind == CubeKind.OOO:
            pipes.append( edge_type )
        else:
            pipes.append( next(iter(BlockGraphHelper.infer_pipe_type(previous.kind, self.target.kind))) )
        return PathSpecification(
            source_cube= self.source, target_cube= self.target,
            extras = self.extras, pipes = pipes
        )


    # def __lt__(self, other):
    #     return self.manhattan_distance_remaining() < other.manhattan_distance_remaining()

    def __str__(self):
        if len(self.extras) == 0:
            return str(self.source) + " -> " + str(self.target)
        else:
            return str(self.source) + " -> " + str(self.extras) + " -> " + str(self.target)

    def __repr__(self):
        return str(self.extras)