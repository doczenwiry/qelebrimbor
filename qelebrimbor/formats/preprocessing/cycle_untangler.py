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

import logging
from typing import cast

import networkx as nx
import pyzx.graph.base

from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.core.components import ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.formats.preprocessing.abstract import Preprocessor
from qelebrimbor.formats.pyzx import PYZX

console = logging.getLogger(__name__)


# TODO: guarantee determinism of process(..) method !!
class CycleUntangler(Preprocessor):
    @staticmethod
    def __count_cycle_degree(graph: VolumetricZxGraph, node: ZxNode):
        count = 0
        nxg = cast(nx.Graph, graph)
        neighbors = list(graph.get_zx_neighbors(node))
        for neighbor in neighbors:
            if not graph.has_edge(node.id, neighbor.id):
                pass

            edge = graph.get_zx_edge(node.id, neighbor.id)
            graph.remove_edge(node.id, neighbor.id)
            if nx.has_path(nxg, node.id, neighbor.id):
                count += 1
            graph.add_edge(node.id, neighbor.id, **{VolumetricZxGraph.KEY_ZX_EDGE: edge})

        # graph.get_zx_degree(node.id)
        return count

    @staticmethod
    def process(input: pyzx.graph.base.BaseGraph) -> None:
        vzx = PYZX.from_pyzx_graph(input)
        new_spider_id: int = max(node.id for node in vzx.get_zx_nodes()) + 1
        cycles = CycleAnalyser.decompose(vzx, minimal=True)

        completed: bool = False
        while not completed:
            spider_to_split: tuple[ZxNode, ZxNode, ZxNode] | None = None
            for cycle in cycles:
                console.debug(f"> Cycle : {cycle}")
                for node in cycle.nodes:
                    cycle_degree = CycleUntangler.__count_cycle_degree(vzx, node)
                    # Need to determine the cycle-degree; number of neighbours involved in a cycle the node belongs to.
                    # Split a spider only if its cycle-degree is >= 4
                    if cycle_degree >= 4:
                        spider_to_split = (node, cycle.preceding(node), cycle.following(node))
                if spider_to_split is not None:
                    break

            if spider_to_split is None:
                completed = True
            else:
                spider, preceding, following = spider_to_split
                console.debug(
                    f"Spider to be split : {spider_to_split} [{CycleUntangler.__count_cycle_degree(vzx, spider)}]"
                )
                # Split the spider; create a new spider of the same type connected to the old through an identity edge.
                # Make the new spider inherit the edges from the old spider that are in the cycle.

                input.add_vertex(index=new_spider_id, ty=input.type(spider.id))
                console.debug(f"> New spider : {new_spider_id} / {input.type(spider.id)}")
                input.add_edge((spider.id, new_spider_id), edgetype=pyzx.EdgeType.SIMPLE)

                console.debug(f"> Old spider : {preceding.id} -> {spider.id} -> {following.id}")

                source, target = min(spider.id, preceding.id), max(spider.id, preceding.id)
                input.add_edge((new_spider_id, preceding.id), edgetype=input.edge_type((source, target)))
                input.remove_edge((source, target))

                source, target = min(spider.id, following.id), max(spider.id, following.id)
                input.add_edge((new_spider_id, following.id), edgetype=input.edge_type((source, target)))
                input.remove_edge((source, target))

                new_spider_id += 1

            # Recompute the cycles
            vzx = PYZX.from_pyzx_graph(input)
            cycles = CycleAnalyser.decompose(vzx, minimal=True)

            # if any(cycle.length % 2 != 0 for cycle in cycles):
            #     for cycle in cycles:
            #         console.debug(f"> Cycle [{cycle.length}] : {cycle}")
            #     raise Exception("Odd cycle present ...")
