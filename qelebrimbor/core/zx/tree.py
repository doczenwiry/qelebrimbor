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

from collections import defaultdict, deque

from qelebrimbor.core.components import ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph


class ZxTree:
    def __init__(self, root: ZxNode):
        self.root = root
        self.__following: dict[ZxNode, list[ZxNode]] = defaultdict(list)
        self.__contained: set[ZxNode] = {root}

    @property
    def height(self) -> int:
        h: int = 0

        level: set[ZxNode] = {self.root}
        while len(level) > 0:
            next_level: set[ZxNode] = set()
            for node in level:
                if node not in self.__following:
                    continue
                next_level.update(self.__following[node])
            level = next_level
            h += 1

        return h

    def append(self, preceding: ZxNode, following: ZxNode):
        if preceding not in self.__contained:
            raise Exception("Attempting to append from a node not in the tree.")

        if following in self.__contained:
            raise Exception("Attempting to append a node already in the tree.")

        self.__following[preceding].append(following)
        self.__contained.add(following)

    def contains(self, node: ZxNode) -> bool:
        return node in self.__contained

    def get_level(self, depth: int = 1) -> set[ZxNode]:
        level: set[ZxNode] = {self.root}
        for h in range(depth):
            next_level: set[ZxNode] = set()
            for node in level:
                next_level.update(self.__following[node])
            level = next_level

        return level

    def __str__(self):
        return str(self.__following)

    @staticmethod
    def extract(graph: VolumetricZxGraph, root: ZxNode) -> ZxTree:
        if not root.is_realised():
            raise Exception(f"Attempting to extract a tree from an unrealised node [{root}]")

        tree: ZxTree = ZxTree(root)
        unrealised: deque[ZxNode] = deque([root])
        while len(unrealised) > 0:
            current = unrealised.popleft()
            for neighbor in graph.get_zx_neighbors(current):
                if neighbor.is_realised():
                    continue

                if tree.contains(neighbor):
                    continue

                tree.append(current, neighbor)
                unrealised.append(neighbor)

        return tree
