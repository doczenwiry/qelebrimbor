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
from qelebrimbor.utilities.statistics import portless_nodes_count

console = logging.getLogger(__name__)

type Construction = tuple[VolumetricZxGraph, ConnectivityTracker, StrandfinderColorblindFusionDFS]


class ZxGraphInflaterEquivolumetricRings:
    def __init__(self, graph: VolumetricZxGraph, cycles: list[ZxCycle], verbose: bool = False):
        self.__graph: VolumetricZxGraph = graph
        self.__ringfinder = RingfinderColorblindExhaustiveBFS(self.__graph)
        self.__zx_cycles: list[ZxCycle] = cycles

        self.__verbose: bool = verbose

    def process(self, abort_on_index: int = -1) -> list[Construction]:
        if self.__verbose:
            print(f">> Ringfinder   : {self.__ringfinder.__class__.__name__}")
            print(f">> Strandfinder : {StrandfinderColorblindFusionDFS.__name__}")

        epoch: int = 0
        completed_constructions: list[Construction] = []
        primary_cycle: ZxCycle = self.__zx_cycles[0]

        # Realise the primary cycle
        console.info(f"> Primary cycle identified : {primary_cycle}")
        # TODO: determine maximal_excess considering cycles with less than 4 spiders.
        incomplete_constructions: list[Construction] = self.__attempt_ring_realisation(
            cycle=primary_cycle, maximal_excess=2 if primary_cycle.length == 4 else 0
        )

        if self.__verbose:
            print(f">> Epoch {epoch} : found {len(incomplete_constructions)} alternative primary rings.")

        if len(incomplete_constructions) == 0:
            console.info("> Failure [cause:unknown]")
            return completed_constructions

        console.info(f"> Realisation successful with {len(incomplete_constructions)} alternatives primary rings.")
        epoch += 1

        console.info(f"> Remaining cycles: {len(self.__zx_cycles) - 1}")

        # Iterate over epochs, realising an additional chain everytime
        while len(incomplete_constructions) > 0:
            if epoch == abort_on_index:
                console.info("> Premature abort for inspection.")
                return incomplete_constructions

            remaining_constructions: list[Construction] = []
            for construction in incomplete_constructions:
                graph, connectivity, strandfinder = construction
                # Recompute the cycles to take into account the splitting that was performed
                remaining_cycles = list(
                    filter(
                        lambda cc: any(not edge.is_realised() for edge in cc.edges),
                        CycleAnalyser.decompose(graph=graph, minimal=True),
                    )
                )

                if len(remaining_cycles) == 0:
                    completed_constructions.append(construction)
                    continue

                candidate = ZxGraphInflaterEquivolumetricRings.__identify_next_chain(*remaining_cycles)

                if candidate is None:
                    raise Exception("No candidate chain found.")

                self.__perform_required_splitting(graph, candidate.nodes, split=True)

                console.info(f"Attempting realisation of chain [index={epoch}, md={candidate.distance}] : {candidate}")

                excess_volume = self.__attempt_chain_realisation(construction, candidate, maximal_excess=20)
                if excess_volume >= 0 and portless_nodes_count(construction[0]) == 0:
                    remaining_constructions.append(construction)
                else:
                    console.info(f"> Failure to complete chain : {candidate}")

            incomplete_constructions.clear()
            incomplete_constructions.extend(remaining_constructions)

            if self.__verbose:
                print(f">> Epoch {epoch} : alternatives remaining : {len(incomplete_constructions)} incomplete", end="")
                print(f", {len(completed_constructions)} ring-complete.")

            epoch += 1

        minimal_volume = min(graph.volume() for graph, _, _ in completed_constructions)
        minimal_constructions = list(
            filter(lambda construction: construction[0].volume() == minimal_volume, completed_constructions)
        )

        console.info(f"Total number of epochs  : {epoch}.")
        if self.__verbose:
            print(f">> Number of minimal constructions : {len(minimal_constructions)}")

        return minimal_constructions

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
        nodes_of_interest: set[ZxNode] = set(graph.get_zx_node(node.id) for node in nodes)
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

    def __attempt_ring_realisation(self, cycle: ZxCycle, maximal_excess: int = 0) -> list[Construction]:
        if self.__verbose:
            print(f">> Attempting realisation of cycle [L={cycle.length}] : {cycle}")

        self.__perform_required_splitting(self.__graph, cycle.nodes, split=True)

        # TODO: the following call is the bottleneck of the overall inflation process ...
        rings = self.__ringfinder.find_optimum(cycle, maximal_excess=maximal_excess)

        constructions: list[Construction] = []

        for ring in rings:
            console.debug(f"Found a ring with volume {ring.volume()} to realise cycle : {cycle}")
            console.debug(f"> : {ring}")

            construction = self.__graph.make_alternative()
            connectivity = OpenPortsTracker(construction)
            strandfinder = StrandfinderColorblindFusionDFS(construction, connectivity, branch_and_bound=True)
            construction.realise_zx_cycle(cycle, ring)

            excess_volume = ring.volume() - cycle.length
            constructions.append((construction, connectivity, strandfinder))

            colored_ev = colored(
                "+" + str(excess_volume), "red" if excess_volume != 0 else "green", attrs=["bold"], force_color=True
            )
            console.info(f">>> Found candidate primary ring [EV={colored_ev}] : {ring}")

            # Reserve the ports for all the nodes that were realised as part of this ring.
            for node, _ in cycle:
                # Since each of these node is realised as part of a ring, it already has two of its edges realised.
                realising_cube = construction.get_zx_node(node.id).realising_cube
                connectivity.reserve(realising_cube, required=construction.get_zx_degree(node.id) - 2)

            cubes = list(ring.cubes)
            for cube in cubes[len(cycle) :]:
                connectivity.occlude(cube.position)

        if self.__verbose:
            print(f">> Found {len(constructions)} alternatives for primary ring.")

        return constructions

    def __attempt_chain_realisation(self, construction: Construction, chain: ZxChain, maximal_excess: int = 0) -> int:
        console.info(f">> Attempting realisation of chain [L={chain.length}] : {chain}")

        if not chain.source.is_realised() or not chain.source.is_realised():
            console.debug("Endpoints are not realised.")
            return -1

        graph, connectivity, strandfinder = construction

        if not connectivity.available(chain.source.realising_cube, chain.target.realising_cube):
            console.debug("Insufficient connectivity.")
            return -1

        strand = strandfinder.find_optimum(chain, maximal_excess=maximal_excess)

        if strand is None:
            console.error(f"Failed to find a strand for : {chain}")
            return -1

        excess_volume = strand.length - chain.length
        colored_ev = colored(
            "+" + str(excess_volume), "red" if excess_volume != 0 else "green", attrs=["bold"], force_color=True
        )
        console.info(f"Found a suitable strand for chain [EV:+{excess_volume}] : {strand}")

        graph.realise_zx_chain(chain, strand)

        if self.__verbose:
            console.info(f">>> Realised as strand [EV:{colored_ev}] : {strand}")

        # Reserve the ports for all the nodes that were realised as part of this ring.
        for node in chain.unrealised:
            # Since each of these node is part of a ring, it already has two of its edges realised.
            connectivity.reserve(node.realising_cube, required=graph.get_zx_degree(node.id) - 2)

        extra_cubes = list(strand.extras)
        for cube in extra_cubes[chain.length - 1 :]:
            connectivity.occlude(cube.position)

        return excess_volume
