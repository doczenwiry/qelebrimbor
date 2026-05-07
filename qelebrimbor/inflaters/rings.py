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

from qelebrimbor.core.attributes_zx import EdgeType, NodeType
from qelebrimbor.core.path import Path

from qelebrimbor.spacetime.ringfinders.depth_first_search import RingfinderDFS
from qelebrimbor.spacetime.ringfinders.breadth_first_search import RingfinderBFS
from qelebrimbor.spacetime.chainfinders.depth_first_search import ChainfinderDFS
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker

from qelebrimbor.utilities.cycle_analyser import CycleAnalyser, ZxCycle, ZxChain
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class ZxGraphInflaterRings:
    def __init__(self, graph: VolumetricZxGraph):
        self.__graph = graph
        self.__spacetime = graph.spacetime
        self.__node_realisations = 0
        self.__edge_realisations = 0

        self.__ports_tracker: OpenPortsTracker = OpenPortsTracker(graph)

        self.__ringfinder = RingfinderBFS(self.__graph)
        self.__chainfinder = ChainfinderDFS(self.__graph, self.__ports_tracker)

    def process(self):
        zx_cycles = CycleAnalyser.decompose(self.__graph, minimal = True)

        realised: set[int] = set()

        count: int = 0
        root_cycle: ZxCycle = zx_cycles[0]

        # Realise the root ring
        console.info(f"> Root ring identified : {root_cycle}")
        excess_volume: int = self.__attempt_ring_realisation(root_cycle, maximal_excess = 6)
        if excess_volume == -1:
            console.info(f"> Failure [cause:unknown]")
            console.info(f"Cycles processed : {count}/{len(zx_cycles)}.")

        console.info(f"> Realisation successful with excess volume : +{excess_volume} cubes.")
        count += 1

        # Realise all subsequent chains
        candidate: tuple[int, ZxChain] | None = self.__identify_next_chain(realised, zx_cycles)

        while candidate is not None and count < len(zx_cycles):
            index, chain = candidate
            console.debug(f"> Next chain identified : {candidate}")

            excess_volume = self.__attempt_chain_realisation(chain, maximal_excess = 6)
            if excess_volume == -1:
                console.info(f"> Failure to complete chain : {candidate}")
                break

            self.__ports_tracker.verify_ports()

            count += 1
            realised.add(index)

            candidate = self.__identify_next_chain(realised, zx_cycles)

        console.info(f"Cycles processed : {count}/{len(zx_cycles)}.")

    # TODO: handle case of disjoint rings (i.e. multiple connected components that contain cycles).
    def __identify_next_chain(self, realised: set[int], cycles: list[ZxCycle]) -> tuple[int, ZxChain] | None:
        all_chains: list[tuple[int, ZxChain]] = CycleAnalyser.identify_chains(self.__graph, realised, cycles)
        selected_length: int | None = None
        selected_distance: int | None = None
        selected: tuple[int, ZxChain] | None = None
        for index, chain in all_chains:
            start, chain_nodes, chain_edges, final = chain
            length = len(chain_edges)
            distance = start.realising_cube.position.get_manhattan_distance(final.realising_cube.position)
            if selected:
                if length < selected_length or (length == selected_length and distance > selected_distance):
                    selected = index, chain
                    selected_length = length
                    selected_distance = distance
            else:
                selected = index, chain
                selected_length = length
                selected_distance = distance

            console.debug(f"> Chain [L:{len(chain_edges)}, D:{distance}] : {start} - {chain_nodes} - {final}")

        return selected

    def __attempt_ring_realisation(self, zx_cycle: ZxCycle, maximal_excess: int = 0) -> int:
        # TODO: the following call is the bottleneck of the overall inflation process ...
        ring = self.__ringfinder.find_optimum(zx_cycle, maximal_excess = maximal_excess)

        if ring is None:
            return -1

        console.debug(f"Found a ring with volume {ring.volume()} to realise cycle : {zx_cycle}")
        console.debug(f"> : {ring}")

        self.__graph.realise_zx_cycle(zx_cycle, ring)

        # Reserve the ports for all the nodes that were realised as part of this ring.
        for node, _ in zx_cycle:
            # Since each of these node is part of a ring, it already has two of its edges realised.
            self.__ports_tracker.reserve_ports(
                cube = node.realising_cube, required_ports = self.__graph.get_zx_degree(node.id) - 2
            )

        return len(ring.cubes) - len(zx_cycle)

    def __attempt_chain_realisation(self, chain: ZxChain, maximal_excess: int = 0) -> int:
        start, nodes, edges, final = chain

        console.info(f"Attempting realisation of chain : {chain}")

        if not start.is_realised() or not final.is_realised():
            return -1

        if not self.__ports_tracker.reachable(start.realising_cube):
            return -1

        if not self.__ports_tracker.reachable(final.realising_cube):
            return -1

        node_restrictions: list[NodeType] = list(map(lambda zxn: zxn.type, nodes))
        edge_restrictions: list[EdgeType] = list(map(lambda zxe: zxe.type, edges))
        completion = self.__chainfinder.find_optimum(
            source = start.realising_cube, target = final.realising_cube,
            restrictions = (node_restrictions, edge_restrictions),
            maximal_excess = maximal_excess
        )

        if completion is None:
            console.error(f"Failed to find a chain for {start} - {nodes} - {final}")
            return -1

        excess_volume = completion.manhattan_length() - len(nodes) - 1
        console.info(f"Found a realisation for chain [EV:+{excess_volume}] : {Path.string(completion)}")

        self.__graph.realise_zx_chain(chain, completion)

        # Reserve the ports for all the nodes that were realised as part of this ring.
        for node in nodes:
            # Since each of these node is part of a ring, it already has two of its edges realised.
            self.__ports_tracker.reserve_ports(
                cube = node.realising_cube, required_ports = self.__graph.get_zx_degree(node.id) - 2
            )

        return excess_volume