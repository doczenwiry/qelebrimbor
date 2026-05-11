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

from qelebrimbor.core.components import ZxNode, ZxEdge


class ZxCycle:
    def __init__(self):
        self.__nodes: list[ZxNode] = []
        self.__edges: list[ZxEdge] = []

    @property
    def anchor(self) -> ZxNode:
        return self.__nodes[0]

    @property
    def nodes(self) -> Iterator[ZxNode]:
        return iter(self.__nodes)

    @property
    def edges(self) -> Iterator[ZxEdge]:
        return iter(self.__edges)

    @property
    def length(self) -> int:
        return len(self.__nodes)

    def extend(self, node: ZxNode, edge: ZxEdge):
        self.__nodes.append(node)
        self.__edges.append(edge)

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
