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
from pyzx.local_search.congruences import unfuse

from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.core.components import ZxEdge, ZxNode
from qelebrimbor.formats.preprocessing.abstract import Preprocessor
from qelebrimbor.formats.pyzx import PYZX


# TODO: guarantee determinism of process(..) method !
class DefaultPreprocessor(Preprocessor):
    @staticmethod
    def process(input: pyzx.graph.base.BaseGraph) -> None:
        pyzx.full_reduce(input)

        vzx = PYZX.from_pyzx_graph(input)

        cycles = CycleAnalyser.decompose(vzx, minimal=True)

        nodes_to_split: set[ZxNode] = set()
        for cycle in cycles:
            # print(f"Cycle [{cycle.length}] : {cycle}")
            for node in cycle.nodes:
                node_degree = vzx.get_zx_degree(node.id)
                if node_degree > 4:
                    nodes_to_split.add(node)

        for node in nodes_to_split:
            # node_degree = vzx.get_zx_degree(node.id)
            # excess = (node_degree + (node_degree % 2) - 4) // 2
            # print(f"> Node {node} has degree {node_degree} and needs unfusing into {excess + 1} nodes.")

            all_cycle_edges: set[ZxEdge] = set()
            all_other_edges: set[ZxEdge] = set()
            for cycle in cycles:
                for edge in cycle.edges:
                    if edge.source == node or edge.target == node:
                        all_cycle_edges.add(edge)
                    else:
                        all_other_edges.add(edge)
            # print(f">> Cycle edges : {all_cycle_edges}")
            # print(f">> Other edges : {all_other_edges}")
            for index, edges in enumerate(batched(all_cycle_edges, 2)):
                if index == 0:
                    # print(f">> Edges kept : {edges}")
                    pass
                else:
                    # print(f">> Edges pass : {edges}")
                    new = unfuse(input, node.id)
                    for edge in edges:
                        source = edge[0].id
                        target = edge[1].id
                        other = target if source == node.id else source
                        edge_type = input.edge_type((source, target))
                        input.remove_edge((source, target))
                        input.add_edge((new, other), edge_type)
