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

import networkx as nx
import matplotlib.pyplot as plt

from qelebrimbor.common.components import BgCube

import logging
console = logging.getLogger(__name__)

class SpacetimeTracer:
    def __init__(self):
        self.__nodes : dict[BgCube, int] = dict()
        self.__nodes_extended: set[BgCube] = set()
        self.__trace: nx.Graph = nx.Graph()

    def add_node(self, vertex):
        current_id = len(self.__nodes)
        self.__nodes[vertex] = current_id
        self.__trace.add_node( current_id )

    def add_edge(self, source, target):
        self.__trace.add_edge(self.__nodes[source], self.__nodes[target])

    def report(self, cubes_to_label : list[BgCube]):
        labels = {
            self.__nodes[cube] : str(cube)
            for cube in cubes_to_label
        }
        layout = nx.drawing.layout.bfs_layout(self.__trace, start = 0)

        points_discovered = len(self.__nodes)
        points_considered = sum(1 for vt in self.__trace.nodes if self.__trace.degree[vt] > 1)
        console.info(f"> Number of points considered : {points_considered}")
        console.info(f"> Number of points discovered : {points_discovered}")

        nx.draw(self.__trace, layout, node_size = 1)
        nx.draw_networkx_labels(self.__trace, layout, labels)
        plt.show()
