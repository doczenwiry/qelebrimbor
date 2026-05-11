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

import itertools
from typing import Iterator

from qelebrimbor.core.components import ZxNode, ZxEdge


class ZxChain:
    def __init__(self, source: ZxNode):
        self.__nodes = [source]
        self.__edges = []

    @property
    def source(self) -> ZxNode:
        return self.__nodes[0]

    @property
    def target(self) -> ZxNode:
        return self.__nodes[-1]

    @property
    def nodes(self) -> Iterator[ZxNode]:
        return itertools.islice(self.__nodes, 1, len(self.__nodes)-1)

    @property
    def edges(self) -> Iterator[ZxEdge]:
        return iter(self.__edges)

    @property
    def length(self) -> int:
        return len(self.__edges)

    @property
    def distance(self) -> int:
        return self.source.realising_cube.position.get_manhattan_distance(self.target.realising_cube.position)

    def append(self, node: ZxNode, edge: ZxEdge):
        self.__nodes.append(node)
        self.__edges.append(edge)

    def extend(self, node: ZxNode, edge: ZxEdge) -> ZxChain:
        cp = ZxChain(self.source)
        cp.__nodes.extend(self.__nodes[1:])
        cp.__edges.extend(self.__edges)

        cp.append(node, edge)

        return cp

    def __str__(self) -> str:
        content = f"{self.source}"

        for index in range(1, len(self.__nodes)):
            content += f" --{repr(self.__edges[index-1].type)}-- {self.__nodes[index]}"

        if len(self.__nodes) == 1:
            content += f" [self-loop]"

        return content