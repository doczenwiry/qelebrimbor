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
import logging
from collections import defaultdict
from time import time
from typing import cast

import matplotlib.pyplot as plt
import networkx as nx
import pandas
import seaborn
from matplotlib.ticker import MaxNLocator

from qelebrimbor.analysis.cycle_sharing import CycleSharingGraph
from qelebrimbor.core.components import ZxEdge, ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.chain import ZxChain
from qelebrimbor.core.zx.cycle import ZxCycle

console = logging.getLogger(__name__)


class CycleAnalyser:
    @staticmethod
    def has_cycles(graph: VolumetricZxGraph) -> bool:
        try:
            nx.find_cycle(cast(nx.Graph, graph))
            return True
        except nx.NetworkXNoCycle:
            return False

    @staticmethod
    def analyse(graph: VolumetricZxGraph, plot: bool = False, minimal: bool = True) -> list[ZxCycle]:
        start = time()
        zx_cycles = CycleAnalyser.decompose(graph, minimal)
        runtime = round(time() - start, 2)

        if len(zx_cycles) == 0:
            print("No cycles detected.")
        else:
            if plot:
                ax = seaborn.histplot(data=pandas.Series(map(len, zx_cycles), dtype=int), discrete=True)
                ax.yaxis.set_major_locator(MaxNLocator(integer=True))
                plt.title(
                    f"Cycle basis [{'non-' if minimal is False else ''}minimal, computed in {str(runtime).rjust(2, ' ')}]"  # noqa: E501
                )
                plt.xlabel("Number of nodes")
                plt.ylabel("Number of cycles")
                plt.show()

                CycleSharingGraph.plot(zx_cycles)

            else:
                histogram: dict[int, int] = defaultdict(int)
                for index in range(len(zx_cycles)):
                    zx_cycle = zx_cycles[index]
                    histogram[len(zx_cycle)] += 1
                size = sorted(histogram.keys(), reverse=True)[0]
                print(f"> Cyclomatic number : {len(zx_cycles)}")
                print(f"> Largest cycle : {len(zx_cycles[0])}")
                print(
                    f"> Cycle basis ({'minimal' if minimal else 'non-minimal'}, computed in {runtime}s) has largest cycle of size {size} [count={histogram[size]}]"  # noqa: E501
                )
                for cycle in zx_cycles:
                    print(f">> Cycle [{CycleAnalyser.weight(cycle, zx_cycles)}] : {cycle}")

        return zx_cycles

    @staticmethod
    def weight(cycle: ZxCycle, cycles: list[ZxCycle]) -> int:
        return sum(1 for other, edge in itertools.product(cycles, cycle.edges) if other.involves(edge))

    @staticmethod
    def __cycle_sharing_weight(csg, node) -> int:
        weight: int = 0
        for neighbor in csg.neighbors(node):
            edge = csg.edges[node, neighbor]
            weight += edge["weight"]
        return weight

    @staticmethod
    def convert(graph: VolumetricZxGraph, basis) -> list[ZxCycle]:
        zx_cycles: list[ZxCycle] = []

        for cycle in basis:
            zx_cycle = ZxCycle()

            for index in range(len(cycle)):
                zx_cycle.append(
                    node=graph.get_zx_node(cycle[index]),
                    edge=graph.get_zx_edge(cycle[index], cycle[(index + 1) % len(cycle)]),
                )

            zx_cycles.append(zx_cycle)

        return zx_cycles

    @staticmethod
    def decompose(graph: VolumetricZxGraph, minimal: bool = True) -> list[ZxCycle]:
        nxg = cast(nx.Graph, graph)
        zx_cycles: list[ZxCycle] = CycleAnalyser.convert(
            graph, nx.minimum_cycle_basis(nxg) if minimal else nx.cycle_basis(nxg)
        )

        csg, _ = CycleSharingGraph.cycle_sharing_graph(zx_cycles)
        indices = sorted(csg.nodes, key=lambda nd: CycleAnalyser.__cycle_sharing_weight(csg, nd), reverse=True)

        return list(zx_cycles[index] for index in indices)

    @staticmethod
    def extract(cycle: ZxCycle) -> ZxChain | None:
        if len(cycle) < 2:
            raise Exception("Cannot breakdown cycle with less than 2 edges.")

        nodes = list(cycle.nodes)
        edges = list(cycle.edges)

        chain_nodes: list[ZxNode] = []
        chain_edges: list[ZxEdge] = []

        console.debug(f"> Breaking down cycle {cycle}")

        # Identify the start of the chain where the preceding node is realised but its following edge is not
        preceding_node: ZxNode = nodes[0]
        following_edge: ZxEdge = edges[0]
        index = 0
        count = 0
        while not (preceding_node.is_realised() and not following_edge.is_realised()) and count < len(cycle):
            index = (index + 1) % len(cycle)
            preceding_node = nodes[index]
            following_edge = edges[index]
            count += 1

        if count == cycle.length:
            console.debug(f"> Cycle {cycle} has no unrealised chain.")
            return None

        chain = ZxChain(source=preceding_node)
        index = (index + 1) % cycle.length
        following_node: ZxNode = nodes[index]
        console.debug(f"Found start of chain : {chain.source}")

        # Construct the chain from index up to and including the last edge that is realised
        count = 0
        while not following_node.is_realised() and count < len(cycle):
            chain.append(following_node, following_edge)
            following_edge = edges[index]
            index = (index + 1) % cycle.length
            following_node = nodes[index]
            count += 1

        chain.append(following_node, following_edge)

        console.debug(f"Found final of chain : {chain.target}")
        console.debug(f"Chain identified : {chain_nodes} , {chain_edges}")

        return chain

    @staticmethod
    def breakdown(cycle: ZxCycle) -> ZxChain | None:
        if len(cycle) < 2:
            raise Exception("Cannot breakdown cycle with less than 2 edges.")

        nodes = list(cycle.nodes)
        edges = list(cycle.edges)

        chain_nodes: list[ZxNode] = []
        chain_edges: list[ZxEdge] = []

        console.debug(f"> Breaking down cycle {cycle}")

        # Identify the start of the chain where the preceding edge is realised but the following one is not
        preceding: ZxEdge = edges[-1]
        following: ZxEdge = edges[0]
        index = 0
        while not (preceding.is_realised() and not following.is_realised()) and index < len(cycle):
            preceding = following
            following = edges[(index + 1) % len(cycle)]
            index += 1

        if index == cycle.length:
            console.debug(f"> Cycle {cycle} has no unrealised chain.")
            return None

        chain = ZxChain(source=nodes[index])
        console.debug(f"Found start of chain : {chain.source}")
        current = edges[index]

        # Construct the chain from index up to and including the last edge that is realised
        while not current.is_realised():
            index = (index + 1) % cycle.length
            chain.append(nodes[index], current)
            current = edges[index]

        console.debug(f"Found final of chain : {chain.target}")
        console.debug(f"Chain identified : {chain_nodes} , {chain_edges}")

        return chain

    @staticmethod
    def identify_chains(*cycles: ZxCycle) -> list[ZxChain]:
        chains: list[ZxChain] = []
        for index in range(len(cycles)):
            cycle = cycles[index]
            console.info(f"Identifying chains in cycle : {cycle}")
            nodes, edges = zip(*cycle)

            if all(edge.is_realised() for edge in edges):
                console.debug(f"> Cycle {cycle} is already complete. Skipping.")
                continue

            if any(node.is_realised() for node in nodes):
                console.debug(f"> Cycle {cycle} intersects current construct.")
                chain: ZxChain | None = CycleAnalyser.extract(cycle)
                if chain is not None:
                    console.debug(f"> Chain found : {chain}")
                    chains.append(chain)

        chains = sorted(chains, key=lambda c: c.length)

        return chains

    @staticmethod
    def cycle_node_realisation_rate(graph: VolumetricZxGraph, minimal: bool = False) -> float:
        all_cycle_nodes: set[ZxNode] = set()
        for cycle in CycleAnalyser.decompose(graph, minimal=minimal):
            nodes, _ = zip(*cycle)
            all_cycle_nodes.update(nodes)
        realised_nodes: int = sum(1 for node in all_cycle_nodes if node.is_realised())
        return realised_nodes / len(all_cycle_nodes)

    @staticmethod
    def cycle_edge_realisation_rate(graph: VolumetricZxGraph, minimal: bool = False) -> float:
        all_cycle_edges: set[ZxEdge] = set()
        for cycle in CycleAnalyser.decompose(graph, minimal=minimal):
            _, edges = zip(*cycle)
            all_cycle_edges.update(edges)
        realised_edges: int = sum(1 for edge in all_cycle_edges if edge.is_realised())
        return realised_edges / len(all_cycle_edges)
