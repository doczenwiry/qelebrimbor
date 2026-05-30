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
from typing import Iterable

from termcolor import colored

from qelebrimbor.analysis.cycles import CycleAnalyser, ZxChain, ZxCycle
from qelebrimbor.core.components import ZxEdge, ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType, NodeId
from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker
from qelebrimbor.spacetime.ringfinders.colorblind_exhaustive_bfs import RingfinderColorblindExhaustiveBFS
from qelebrimbor.spacetime.strandfinders.colorblind_fusion_dfs import StrandfinderColorblindFusionDFS

console = logging.getLogger(__name__)


class ZxGraphInflaterEquivolumetricRings:
    def __init__(self, graph: VolumetricZxGraph, cycles: list[ZxCycle], verbose: bool = False):
        self.__graph: VolumetricZxGraph = graph
        self.__ringfinder = RingfinderColorblindExhaustiveBFS(self.__graph)
        self.__constructions: list[tuple[VolumetricZxGraph, ConnectivityTracker, StrandfinderColorblindFusionDFS]] = []

        self.__verbose: bool = verbose
        self.__zx_cycles: list[ZxCycle] = cycles

    def process(self, abort_on_failure: bool = True, abort_on_index: int = -1) -> int:
        if self.__verbose:
            print(f">> Ringfinder   : {self.__ringfinder.__class__.__name__}")
            print(f">> Strandfinder : {StrandfinderColorblindFusionDFS.__name__}")
        zx_cycles = self.__zx_cycles

        count: int = 0
        primary_cycle: ZxCycle = zx_cycles[0]

        # Realise the primary cycle
        console.info(f"> Primary cycle identified : {primary_cycle}")
        excess_volume: int = self.__attempt_ring_realisation(
            cycle=primary_cycle, maximal_excess=2 if primary_cycle.length == 4 else 0
        )
        if excess_volume == -1:
            console.info("> Failure [cause:unknown]")

        console.info(f"> Realisation successful with excess volume : +{excess_volume} cubes.")
        count += 1

        # Recompute the cycles to take into account the splitting that was performed
        zx_cycles = list(
            filter(
                lambda cc: any(not edge.is_realised() for edge in cc.edges),
                CycleAnalyser.decompose(graph=self.__graph, minimal=True),
            )
        )

        # Realise all subsequent chains
        candidate: ZxChain | None = self.__identify_next_chain(*zx_cycles)

        while candidate is not None and 0 < len(zx_cycles):
            console.info(f"Attempting realisation of chain [index={count}, md={candidate.distance}] : {candidate}")

            if count == abort_on_index:
                console.info("> Premature abort for inspection.")
                return -2

            excess_volume = self.__attempt_chain_realisation(candidate, maximal_excess=20)
            if excess_volume == -1:
                console.info(f"> Failure to complete chain : {candidate}")
                if self.__verbose:
                    print(">>> Failure to find a strand for chain.")
                if abort_on_failure:
                    return -1

            count += 1

            # Recompute the cycles to take into account the splitting that was performed
            zx_cycles = list(
                filter(
                    lambda cc: any(not edge.is_realised() for edge in cc.edges),
                    CycleAnalyser.decompose(graph=self.__graph, minimal=True),
                )
            )

            candidate = ZxGraphInflaterEquivolumetricRings.__identify_next_chain(*zx_cycles)

        console.info(f"Cycles processed : {count}/{len(zx_cycles)}.")
        if self.__verbose:
            print(f">> Cycles realised : {count}/{len(zx_cycles)}")

        return count

    # TODO: handle case of disjoint rings (i.e. multiple connected components that contain cycles).
    @staticmethod
    def __identify_next_chain(*cycles: ZxCycle) -> ZxChain | None:
        all_chains: list[ZxChain] = CycleAnalyser.identify_chains(*cycles)
        console.debug("All chains identified :")
        for chain in all_chains:
            console.debug(f"> Chain : {chain}")
        selected: ZxChain | None = None
        for chain in all_chains:
            if selected:
                if chain.length > selected.length or (
                    chain.length == selected.length and chain.distance > selected.distance
                ):
                    selected = chain
            else:
                selected = chain

        return selected

    def __perform_required_splitting(self, graph: VolumetricZxGraph, nodes: Iterable[ZxNode], split: bool = False):
        nodes_of_interest: set[ZxNode] = set(nodes)
        new_spider_id: NodeId = max(node.id for node in graph.get_zx_nodes()) + 1
        edge_splits: dict[ZxEdge, tuple[ZxEdge, ZxEdge]] = dict()
        # TODO: perform splitting of nodes that have a degree > 4
        for node in nodes_of_interest:
            neighborhood = list(graph.get_zx_neighbors(node))
            if len(neighborhood) > 4:
                console.debug(f">> Node {node} has {len(neighborhood)} neighbors and requires splitting.")
                extracted_nodes = list(
                    filter(
                        lambda node: not node.is_realised() and node not in nodes_of_interest,
                        graph.get_zx_neighbors(node),
                    )
                )
                if not split:
                    console.debug(f">>> Need to move nodes {extracted_nodes} outside the cycle.")
                else:
                    split_node = ZxNode(new_spider_id, node.type, node.qubit, node.layer)
                    split_edge = ZxEdge(node, split_node, EdgeType.IDENTITY)
                    graph.add_node(new_spider_id)
                    graph.nodes[new_spider_id][VolumetricZxGraph.KEY_ZX_NODE] = split_node
                    graph.add_edge(node.id, split_node.id, **{VolumetricZxGraph.KEY_ZX_EDGE: split_edge})
                    console.debug(f">>> Added split node : {split_node}")
                    console.debug(f">>> Added split edge : {split_edge}")
                    for neighbor in filter(lambda nb: nb not in nodes_of_interest, neighborhood):
                        old_edge = graph.get_zx_edge(node.id, neighbor.id)
                        graph.remove_edge(node.id, neighbor.id)
                        passed_edge = ZxEdge(split_node, neighbor, old_edge.type)
                        graph.add_edge(split_node.id, neighbor.id)
                        graph.edges[split_node.id, neighbor.id][VolumetricZxGraph.KEY_ZX_EDGE] = passed_edge
                        console.debug(f">>>> Transferring {neighbor} to {split_node} [edge:{passed_edge}]")
                        edge_splits[old_edge] = (split_edge, passed_edge)
                    new_spider_id += 1

    def __attempt_ring_realisation(self, cycle: ZxCycle, maximal_excess: int = 0) -> int:
        if self.__verbose:
            print(f">> Attempting realisation of cycle [L={cycle.length}] : {cycle}")

        self.__perform_required_splitting(self.__graph, cycle.nodes, split=True)

        # TODO: the following call is the bottleneck of the overall inflation process ...
        rings = self.__ringfinder.find_optimum(cycle, maximal_excess=maximal_excess)

        for ring in rings:
            console.debug(f"Found a ring with volume {ring.volume()} to realise cycle : {cycle}")
            console.debug(f"> : {ring}")

            construction = self.__graph.make_alternative()
            connectivity = OpenPortsTracker(construction)
            strandfinder = StrandfinderColorblindFusionDFS(construction, connectivity, branch_and_bound=True)
            self.__constructions.append((construction, connectivity, strandfinder))

            construction.realise_zx_cycle(cycle, ring)

            excess_volume = ring.volume() - cycle.length

            colored_ev = colored(
                "+" + str(excess_volume), "red" if excess_volume != 0 else "green", attrs=["bold"], force_color=True
            )
            if self.__verbose:
                print(f">>> Realised as ring [EV={colored_ev}] : {ring}")

            # Reserve the ports for all the nodes that were realised as part of this ring.
            for node, _ in cycle:
                # Since each of these node is realised as part of a ring, it already has two of its edges realised.
                realising_cube = construction.get_zx_node(node.id).realising_cube
                connectivity.reserve(realising_cube, required=construction.get_zx_degree(node.id) - 2)

            cubes = list(ring.cubes)
            for cube in cubes[len(cycle) :]:
                connectivity.occlude(cube.position)

        return len(self.__constructions)

    def __attempt_chain_realisation(self, chain: ZxChain, maximal_excess: int = 0) -> int:
        if self.__verbose:
            print(f">> Attempting realisation of chain [L={chain.length}] : {chain}")

        if not chain.source.is_realised() or not chain.source.is_realised():
            console.debug("Endpoints are not realised.")
            return -1

        self.__perform_required_splitting(self.__graph, chain.nodes, split=True)

        # if not self.__connectivity.available(chain.source.realising_cube, chain.target.realising_cube):
        #     console.debug("Insufficient connectivity.")
        #     return -1
        #
        # strand = self.__strandfinder.find_optimum(chain, maximal_excess=maximal_excess)

        # if strand is None:
        #     console.error(f"Failed to find a strand for : {chain}")
        #     return -1
        #
        # excess_volume = strand.length - chain.length
        # colored_ev = colored(
        #     "+" + str(excess_volume), "red" if excess_volume != 0 else "green", attrs=["bold"], force_color=True
        # )
        # console.info(f"Found a suitable strand for chain [EV:+{excess_volume}] : {strand}")
        #
        # self.__graph.realise_zx_chain(chain, strand)
        #
        # if self.__verbose:
        #     print(f">>> Realised as strand [EV:{colored_ev}] : {strand}")
        #
        # # Reserve the ports for all the nodes that were realised as part of this ring.
        # for node in chain.unrealised:
        #     # Since each of these node is part of a ring, it already has two of its edges realised.
        #     self.__connectivity.reserve(node.realising_cube, required=self.__graph.get_zx_degree(node.id) - 2)
        #
        # extra_cubes = list(strand.extras)
        # for cube in extra_cubes[chain.length - 1 :]:
        #     self.__connectivity.occlude(cube.position)

        # return excess_volume
        return -1
