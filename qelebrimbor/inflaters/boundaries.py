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

from qelebrimbor.core.zx.attributes import NodeType
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.spacetime.placefinders.breadth_first_search import PlacefinderBFS

import logging
console = logging.getLogger(__name__)


class ZxGraphInflaterBoundaries:
    def __init__(self, graph: VolumetricZxGraph):
        self.__graph = graph
        self.__spacetime = graph.spacetime

        self.__placefinder = PlacefinderBFS(self.__graph)

    def process(self):
        # Extend the boundaries
        for node in self.__graph.get_zx_nodes():
            if not node.is_realised() or node.type not in { NodeType.X, NodeType.Z }:
                continue

            for neighbor in self.__graph.get_zx_neighbors(node):
                if neighbor.is_realised() or neighbor.type != NodeType.O:
                    continue

                placement = self.__placefinder.find_closest_realisation(node.realising_cube, neighbor)

                if placement is None:
                    continue

                # Realise the target cube and the path connecting it to the source cube
                self.__graph.realise_zx_node(neighbor, placement.final)
                self.__graph.realise_zx_edge(node.id, neighbor.id, placement)