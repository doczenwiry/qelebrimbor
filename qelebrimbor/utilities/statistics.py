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

from collections import defaultdict

from qelebrimbor.core.common import Port
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import NodeType
from qelebrimbor.helpers.spacetime import SpacetimeHelper


class VolumetricZxGraphStatistics:
    @staticmethod
    def unrealised(graph: VolumetricZxGraph) -> tuple[int, int]:
        unrealised_nodes_count: int = sum(1 for node in graph.get_zx_nodes() if not node.is_realised())
        unrealised_edges_count: int = sum(1 for edge in graph.get_zx_edges() if not edge.is_realised())
        return unrealised_nodes_count, unrealised_edges_count


def portless_nodes_count(graph: VolumetricZxGraph) -> int:
    count: int = 0

    for node in graph.get_zx_nodes():
        if not (node.is_realised() and node.type in {NodeType.X, NodeType.Z}):
            continue

        if all(graph.get_zx_edge(node.id, neighbor.id).is_realised() for neighbor in graph.get_zx_neighbors(node)):
            continue

        cube = node.realising_cube
        open_ports: dict[BgCube, set[Port]] = defaultdict(set)
        for equivalent in graph.get_equivalent_bg_cubes(cube):
            for position in SpacetimeHelper.get_constellation(equivalent.position, equivalent.kind.get_reach()):
                if not graph.spacetime.occupied(position):
                    open_ports[equivalent].add(position)

        if len(open_ports) == 0:
            count += 1

    return count
