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
        if not root.is_realised():
            raise Exception(f"Attempting to create a tree from an unrealised root [{root}]")

        self.root = root
        self.__following: dict[ZxNode, list[ZxNode]] = defaultdict(list)
        self.__preceding: dict[ZxNode, ZxNode | None] = {root: None}

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
        if preceding not in self.__preceding:
            raise Exception(f"Attempting to append from a node not in the tree [{preceding}, {following}]")

        if following in self.__preceding:
            raise Exception(f"Attempting to append a node already in the tree [{preceding}, {following}]")

        self.__following[preceding].append(following)
        self.__preceding[following] = preceding

    def contains(self, node: ZxNode) -> bool:
        return node in self.__preceding

    def preceding(self, node: ZxNode) -> ZxNode:
        preceding: ZxNode | None = self.__preceding[node]
        if preceding is None:
            raise Exception(f"The root of a tree has no preceding node [{node}].")

        return preceding

    def following(self, node: ZxNode) -> list[ZxNode]:
        return self.__following[node]

    def level(self, level: int = 0) -> list[ZxNode]:
        current: list[ZxNode] = [self.root]
        for h in range(level):
            next_level: list[ZxNode] = list()
            for node in current:
                next_level.extend(self.__following[node])
            current = next_level

        return current

    def __str__(self) -> str:
        string = ""
        for level in range(self.height):
            current = self.level(level)
            entries: list[str] = []
            for index, node in enumerate(current):
                entry = f"{node}"
                if len(self.__following[node]) > 0:
                    entry += f" -> {{{','.join(map(str, self.__following[node]))}}}"
                entries.append(entry)

            if len(entries) > 0:
                if level > 0:
                    string += ": "
                string += f"L{level}[[{'; '.join(entries)}]]"

        return string

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
