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

from typing import Iterator

from qelebrimbor.core.components import ZxEdge, ZxNode
from qelebrimbor.core.zx.attributes import EdgeType, NodeType


class ZxCycle:
    def __init__(self) -> None:
        self.__nodes: list[ZxNode] = []
        self.__edges: list[ZxEdge] = []

    @property
    def nodes(self) -> Iterator[ZxNode]:
        return iter(self.__nodes)

    @property
    def edges(self) -> Iterator[ZxEdge]:
        return iter(self.__edges)

    @property
    def length(self) -> int:
        return len(self.__nodes)

    def contains(self, node: ZxNode) -> bool:
        return node in self.nodes

    def involves(self, edge: ZxEdge) -> bool:
        return edge in self.edges

    def append(self, node: ZxNode, edge: ZxEdge):
        # TODO: validate the node/edge against self.
        self.__nodes.append(node)
        self.__edges.append(edge)

    def is_alternating(self) -> bool:
        for index in range(self.length):
            same_colors = self.__nodes[index].type == self.__nodes[(index + 1) % self.length].type
            is_hadamard = self.__edges[index].type == EdgeType.HADAMARD

            if same_colors != is_hadamard:
                return False
        return True

    @staticmethod
    def make(node_types: list[NodeType], edge_types: list[EdgeType]) -> ZxCycle:
        if len(node_types) != len(edge_types):
            raise ValueError("A ZxCycle must contain as many nodes as edges.")
        cycle = ZxCycle()
        nodes = [ZxNode(node_id, node_types[node_id]) for node_id in range(len(node_types))]
        edges = [
            ZxEdge(nodes[node_id], nodes[(node_id + 1) % len(nodes)], edge_types[node_id])
            for node_id in range(len(nodes))
        ]

        for node, edge in zip(nodes, edges):
            cycle.append(node, edge)

        return cycle

    def __len__(self):
        return len(self.__nodes)

    def __iter__(self):
        return zip(self.__nodes, self.__edges)

    def __str__(self) -> str:
        content = ""

        for node, edge in zip(self.__nodes, self.__edges):
            content += f"{str(node)} --{repr(edge.type)}-- "

        if self.length > 0:
            content += f"{self.__nodes[0]}"

        return content
