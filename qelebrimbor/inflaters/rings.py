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
from qelebrimbor.spacetime.ringfinders.colorblind_bfs import RingfinderColorblindBFS
from qelebrimbor.spacetime.strandfinders.colorblind_fusion_dfs import StrandfinderColorblindFusionDFS

console = logging.getLogger(__name__)


class ZxGraphInflaterRings:
    def __init__(self, graph: VolumetricZxGraph, cycles: list[ZxCycle], verbose: bool = False):
        self.__graph = graph
        self.__connectivity: ConnectivityTracker = OpenPortsTracker(graph)
        self.__ringfinder = RingfinderColorblindBFS(self.__graph)
        self.__strandfinder = StrandfinderColorblindFusionDFS(self.__graph, self.__connectivity, branch_and_bound=True)

        self.__verbose = verbose
        self.__zx_cycles = cycles

    def process(self, abort_on_index: int = -1) -> int:
        if self.__verbose:
            print(f">> Ringfinder   : {self.__ringfinder.__class__.__name__}")
            print(f">> Strandfinder : {self.__strandfinder.__class__.__name__}")
        zx_cycles = self.__zx_cycles

        count: int = 0
        root_cycle: ZxCycle = zx_cycles[0]

        # Realise the root ring
        console.info(f"> Root ring identified : {root_cycle}")
        excess_volume: int = self.__attempt_ring_realisation(root_cycle, maximal_excess=6)
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
        candidate: ZxChain | None = ZxGraphInflaterRings.__select_next_chain(*zx_cycles)

        while candidate is not None and 0 < len(zx_cycles):
            console.info(f"Attempting realisation of chain [index={count}, md={candidate.distance}] : {candidate}")

            if count == abort_on_index:
                console.info("> Premature abort for inspection.")
                # TODO: fix occlusion of ports by realisation of long path.
                self.__connectivity.report(verbose=True)
                return -2

            excess_volume = self.__attempt_chain_realisation(candidate, maximal_excess=6)
            if excess_volume == -1:
                console.info(f"> Failure to complete chain : {candidate}")
                if self.__verbose:
                    print(">>> Failure to find a strand for chain.")
                return -1

            self.__connectivity.report()
            count += 1

            # Recompute the cycles to take into account the splitting that was performed
            zx_cycles = list(
                filter(
                    lambda cc: any(not edge.is_realised() for edge in cc.edges),
                    CycleAnalyser.decompose(graph=self.__graph, minimal=True),
                )
            )

            candidate = ZxGraphInflaterRings.__select_next_chain(*zx_cycles)

        console.info(f"Cycles processed : {count}/{len(self.__zx_cycles)}.")
        if self.__verbose:
            print(f">> Cycles realised : {count}/{len(self.__zx_cycles)}")

        return count

    @staticmethod
    def __select_next_chain(*cycles: ZxCycle) -> ZxChain | None:
        for cycle in cycles:
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
                    return chain

        return None

    # TODO: handle case of disjoint rings (i.e. multiple connected components that contain cycles).
    @staticmethod
    # TODO: respect the order of the cycles to identify the next chain to be realised !!!
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

    def __perform_required_splitting(self, nodes: Iterable[ZxNode], split: bool = False):
        nodes_of_interest: set[ZxNode] = set(nodes)
        new_spider_id: NodeId = max(node.id for node in self.__graph.get_zx_nodes()) + 1
        edge_splits: dict[ZxEdge, tuple[ZxEdge, ZxEdge]] = dict()
        # TODO: perform splitting of nodes that have a degree > 4
        for node in nodes_of_interest:
            neighborhood = list(self.__graph.get_zx_neighbors(node))
            if len(neighborhood) > 4:
                console.debug(f">> Node {node} has {len(neighborhood)} neighbors and requires splitting.")
                extracted_nodes = list(
                    filter(
                        lambda node: not node.is_realised() and node not in nodes_of_interest,
                        self.__graph.get_zx_neighbors(node),
                    )
                )
                if not split:
                    console.debug(f">>> Need to move nodes {extracted_nodes} outside the cycle.")
                else:
                    split_node = ZxNode(new_spider_id, node.type, node.qubit, node.layer)
                    split_edge = ZxEdge(node, split_node, EdgeType.IDENTITY)
                    self.__graph.add_node(new_spider_id)
                    self.__graph.nodes[new_spider_id][VolumetricZxGraph.KEY_ZX_NODE] = split_node
                    self.__graph.add_edge(node.id, split_node.id, **{VolumetricZxGraph.KEY_ZX_EDGE: split_edge})
                    console.debug(f">>> Added split node : {split_node}")
                    console.debug(f">>> Added split edge : {split_edge}")
                    for neighbor in filter(lambda nb: nb not in nodes_of_interest, neighborhood):
                        old_edge = self.__graph.get_zx_edge(node.id, neighbor.id)
                        self.__graph.remove_edge(node.id, neighbor.id)
                        passed_edge = ZxEdge(split_node, neighbor, old_edge.type)
                        self.__graph.add_edge(split_node.id, neighbor.id)
                        self.__graph.edges[split_node.id, neighbor.id][VolumetricZxGraph.KEY_ZX_EDGE] = passed_edge
                        console.debug(f">>>> Transferring {neighbor} to {split_node} [edge:{passed_edge}]")
                        edge_splits[old_edge] = (split_edge, passed_edge)
                    new_spider_id += 1

    def __attempt_ring_realisation(self, cycle: ZxCycle, maximal_excess: int = 0) -> int:
        if self.__verbose:
            print(f">> Attempting realisation of cycle [L={cycle.length}] : {cycle}")

        # TODO: carefully relocate when the splitting is performed.
        # self.__perform_required_splitting(cycle.nodes, split=True)

        # TODO: the following call is the bottleneck of the overall inflation process ...
        ring = self.__ringfinder.find_optimum(cycle, maximal_excess=maximal_excess)

        if ring is None:
            if self.__verbose:
                print(f">>> {colored('FAILURE', 'red', attrs=['bold'], force_color=True)}")
            return -1

        console.debug(f"Found a ring with volume {ring.volume()} to realise cycle : {cycle}")
        console.debug(f"> : {ring}")

        self.__graph.realise_zx_cycle(cycle, ring)

        excess_volume = ring.volume() - cycle.length

        colored_ev = colored(
            "+" + str(excess_volume), "red" if excess_volume != 0 else "green", attrs=["bold"], force_color=True
        )
        if self.__verbose:
            print(f">>> Realised as ring [EV={colored_ev}] : {ring}")

        # Reserve the ports for all the nodes that were realised as part of this ring.
        for node, _ in cycle:
            # Since each of these node is realised as part of a ring, it already has two of its edges realised.
            self.__connectivity.reserve(node.realising_cube, required=node.degree - 2)

        cubes = list(ring.cubes)
        for cube in cubes[len(cycle) :]:
            self.__connectivity.occlude(cube.position)

        return excess_volume

    def __attempt_chain_realisation(self, chain: ZxChain, maximal_excess: int = 0) -> int:
        if self.__verbose:
            print(f">> Attempting realisation of chain [L={chain.length}] : {chain}")

        if not chain.source.is_realised() or not chain.source.is_realised():
            console.debug("Endpoints are not realised.")
            return -1

        # TODO: carefully relocate when the splitting is performed.
        # self.__perform_required_splitting(chain.nodes, split=True)

        if not self.__connectivity.available(chain.source.realising_cube, chain.target.realising_cube):
            console.debug("Insufficient connectivity.")
            return -1

        strand = self.__strandfinder.find_optimum(chain, maximal_excess=maximal_excess)

        if strand is None:
            console.error(f"Failed to find a strand for : {chain}")
            return -1

        excess_volume = strand.length - chain.length
        colored_ev = colored(
            "+" + str(excess_volume), "red" if excess_volume != 0 else "green", attrs=["bold"], force_color=True
        )
        console.info(f"Found a suitable strand for chain [EV:+{excess_volume}] : {strand}")

        self.__graph.realise_zx_chain(chain, strand)

        if self.__verbose:
            nun = strand.number_of_unfusable_nodes()
            print(f">>> Realised as strand [EV:{colored_ev}/US:{nun}/LC:{chain.length + 1}] : {strand}")

        # Reserve the ports for all the nodes that were realised as part of this ring.
        for node in chain.unrealised:
            # Since each of these node is part of a ring, it already has two of its edges realised.
            self.__connectivity.reserve(node.realising_cube, required=node.degree - 2)

        extra_cubes = list(strand.extras)
        for cube in extra_cubes[chain.length - 1 :]:
            self.__connectivity.occlude(cube.position)

        return excess_volume
