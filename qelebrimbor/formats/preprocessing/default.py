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

from itertools import batched

import pyzx.graph.base

from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.core.components import ZxNode
from qelebrimbor.core.zx.attributes import NodeId
from qelebrimbor.formats.preprocessing.abstract import Preprocessor
from qelebrimbor.formats.pyzx import PYZX


# TODO: guarantee determinism of process(..) method !
class DefaultPreprocessor(Preprocessor):
    @staticmethod
    def process(input: pyzx.graph.base.BaseGraph) -> None:
        pyzx.full_reduce(input)

        vzx = PYZX.from_pyzx_graph(input)
        next_node_id: int = max(node.id for node in vzx.get_zx_nodes()) + 1

        cycles = CycleAnalyser.decompose(vzx, minimal=True)

        nodes_to_split: list[tuple[ZxNode, set[NodeId], set[NodeId]]] = list()
        for node in vzx.get_zx_nodes():
            node_degree = vzx.get_zx_degree(node.id)
            if node_degree > 4:
                cycle_neighbors: set[NodeId] = set()
                other_neighbors: set[NodeId] = set()
                for neighbor in vzx.get_zx_neighbors(node):
                    if any(cycle.contains(neighbor) for cycle in cycles):
                        cycle_neighbors.add(neighbor.id)
                    else:
                        other_neighbors.add(neighbor.id)
                nodes_to_split.append((node, cycle_neighbors, other_neighbors))

        for node, c_neighbors, o_neighbors in nodes_to_split:
            # print(f">> Node {node} has cycle-degree {len(c_neighbors)} and other-degree {len(o_neighbors)}")
            # print(f">>> Cycle neighbors : {c_neighbors}")
            # print(f">>> Other neighbors : {o_neighbors}")
            # node_degree = vzx.get_zx_degree(node.id)
            # excess = (node_degree + (node_degree % 2) - 4) // 2
            # print(f"> Node {node} has degree {node_degree} and needs unfusing into {excess + 1} nodes.")

            # pyzx.draw(input, labels=True)

            if len(c_neighbors) <= 3:
                new = input.add_vertex(index=next_node_id, ty=input.type(node.id))
                next_node_id += 1
                input.add_edge((node.id, new), pyzx.EdgeType.SIMPLE)
                for neighbor_id in o_neighbors:
                    edge = min(node.id, neighbor_id), max(node.id, neighbor_id)
                    edge_type = input.edge_type(edge)
                    input.remove_edge(edge)
                    input.add_edge((new, neighbor_id), edge_type)

            else:  # len(c_neighbors) >= 4:
                # Unfuse the node and distribute the cycle-neighbors among the resulting nodes.
                for index, neighbors in enumerate(batched(c_neighbors, 2)):
                    # Keep the first pair of neighbors to itself and pass on the remaining pairs
                    if index > 0:
                        # print(f">> Edges pass : {edges}")
                        new = input.add_vertex(index=next_node_id, ty=input.type(node.id))
                        next_node_id += 1
                        input.add_edge((node.id, new), pyzx.EdgeType.SIMPLE)
                        for neighbor_id in neighbors:
                            source, target = min(node.id, neighbor_id), max(node.id, neighbor_id)
                            edge = input.edge(source, target)
                            edge_type = input.edge_type(edge)
                            input.remove_edge(edge)
                            input.add_edge((new, neighbor_id), edge_type)
