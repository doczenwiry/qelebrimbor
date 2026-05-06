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

from typing import cast

import math
import networkx as nx

from qelebrimbor.common.components import ZxEdge, ZxNode
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

type ZxCycle = list[tuple[ZxNode, ZxEdge]]
type ZxChainNodes = list[ZxNode]
type ZxChainEdges = list[ZxEdge]

class CycleAnalyser:
    @staticmethod
    def has_cycles(graph: VolumetricZxGraph) -> bool:
        try:
            nx.find_cycle(cast(nx.Graph, graph))
            return True
        except nx.NetworkXNoCycle:
            return False

    @staticmethod
    def string(cycle: ZxCycle) -> str:
        content = ""

        for link in cycle:
            node, edge = link
            content += f"{str(node)} --{repr(edge.type)}-- "

        if len(cycle) > 0:
            content += f"{cycle[0][0]}"

        return content

    @staticmethod
    def analyse(graph: VolumetricZxGraph, minimal: bool = False):
        print(f"Cycle basis [{"" if minimal else "non-"}minimal]:")
        zx_cycles = CycleAnalyser.decompose(graph, minimal)
        max_digits = max(int(math.log10(len(cycle))) for cycle in zx_cycles) + 1
        for index in range(len(zx_cycles)):
            zx_cycle = zx_cycles[index]
            print(f"Cycle {index} [length={str(len(zx_cycle)).rjust(max_digits, ' ')}] : {CycleAnalyser.string(zx_cycle)}")

    @staticmethod
    def decompose(graph: VolumetricZxGraph, minimal: bool = False) -> list[ZxCycle]:
        zx_cycles: list[ZxCycle] = []

        nxg = cast(nx.Graph, graph)
        cycle_basis = nx.minimum_cycle_basis(nxg) if minimal else nx.cycle_basis(nxg)

        for cycle in cycle_basis:
            zx_cycle = []

            for index in range(len(cycle)):
                current_node = graph.get_zx_node(cycle[index])
                current_edge = graph.get_zx_edge(cycle[index], cycle[(index + 1) % len(cycle)])
                zx_cycle.append( (current_node, current_edge ))

            zx_cycles.append( zx_cycle )

        return list(sorted(zx_cycles, key = len, reverse = True))

    @staticmethod
    def decompose_nodes(vzx: VolumetricZxGraph, minimal: bool = False) -> list[list[ZxNode]]:
        nxg = cast(nx.Graph, vzx)
        cycle_basis = nx.minimum_cycle_basis(nxg) if minimal else nx.cycle_basis(nxg)
        return list(map(
            lambda cycle: list(map(vzx.get_zx_node, cycle)),
            sorted(cycle_basis, key = len, reverse = True)
        ))

    @staticmethod
    def decompose_edges(vzx: VolumetricZxGraph, minimal: bool = False) -> list[list[ZxEdge]]:
        decomposition: list[list[ZxEdge]] = []
        for cycle in CycleAnalyser.decompose_nodes(vzx, minimal):
            nc = len(cycle)
            current: list[ZxEdge] = []
            for index in range(len(cycle)):
                source, target = (cycle[index], cycle[(index+1) % nc])
                current.append( vzx.get_zx_edge(source.id, target.id) )
            decomposition.append(current)
        return decomposition

    @staticmethod
    def breakdown(graph: VolumetricZxGraph, cycle: list[ZxNode]) -> ZxChainNodes:
        chain: ZxChainNodes = []

        console.debug(f"> Breaking down cycle {cycle}")
        nc = len(cycle)

        # Identify the start of the chain where the preceding edge is realised but the following one is not
        index = 0
        preceding: ZxEdge = graph.get_zx_edge(cycle[index].id, cycle[(index-1)% nc].id)
        following: ZxEdge = graph.get_zx_edge(cycle[index].id, cycle[(index+1)% nc].id)
        while not (preceding.is_realised() and not following.is_realised()):
            index += 1
            preceding = following
            following = graph.get_zx_edge(cycle[index].id, cycle[(index+1)% nc].id)

        # Construct the chain from index until the following edge that is realised
        while not following.is_realised():
            chain.append( cycle[index] )
            index = (index + 1) % nc
            following = graph.get_zx_edge(cycle[index].id, cycle[(index+1)% nc].id)

        # Add the final node of the chain
        chain.append( cycle[index] )

        console.info(f"Chain identified : {chain}")

        return chain

    @staticmethod
    def cycle_node_realisation_rate(graph: VolumetricZxGraph, minimal: bool = False) -> float:
        all_cycle_nodes = set()
        for cycle in CycleAnalyser.decompose_nodes(graph, minimal = minimal):
            all_cycle_nodes.update(cycle)
        realised_nodes: int = sum(1 for node in all_cycle_nodes if node.is_realised())
        return realised_nodes / len(all_cycle_nodes)

    @staticmethod
    def cycle_edge_realisation_rate(graph: VolumetricZxGraph, minimal: bool = False) -> float:
        all_cycle_edges = set()
        for cycle in CycleAnalyser.decompose_edges(graph, minimal = minimal):
            all_cycle_edges.update(cycle)
        realised_edges: int = sum(1 for edge in all_cycle_edges if edge.is_realised())
        return realised_edges / len(all_cycle_edges)