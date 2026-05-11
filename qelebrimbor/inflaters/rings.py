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

from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker

from qelebrimbor.spacetime.ringfinders.depth_first_search import RingfinderDFS
from qelebrimbor.spacetime.strandfinders.depth_first_search import StrandfinderDFS

from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker

from qelebrimbor.analysis.cycles import CycleAnalyser, ZxCycle, ZxChain
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class ZxGraphInflaterRings:
    def __init__(self, graph: VolumetricZxGraph, cycles: list[ZxCycle]):
        self.__graph = graph
        self.__spacetime = graph.spacetime
        self.__connectivity: ConnectivityTracker = OpenPortsTracker(graph)
        self.__ringfinder = RingfinderDFS(self.__graph, branch_and_bound = True)
        self.__strandfinder = StrandfinderDFS(self.__graph, self.__connectivity)

        self.__zx_cycles = cycles

    def process(self, abort_on_failure: bool = False, abort_on_index: int = -1):
        zx_cycles = self.__zx_cycles

        index: int = 0
        root_cycle: ZxCycle = zx_cycles[0]

        # Realise the root ring
        console.info(f"> Root ring identified : {root_cycle}")
        excess_volume: int = self.__attempt_ring_realisation(root_cycle, maximal_excess = 6)
        if excess_volume == -1:
            console.info(f"> Failure [cause:unknown]")

        console.info(f"> Realisation successful with excess volume : +{excess_volume} cubes.")
        index += 1

        # Realise all subsequent chains
        candidate: ZxChain | None = self.__identify_next_chain(*zx_cycles)

        while candidate is not None and index < len(zx_cycles):
            console.info(f"Attempting realisation of chain [index={index}, md={candidate.distance}] : {candidate}")

            if index == abort_on_index:
                console.info(f"> Premature abortion for inspection of specific example.")
                # TODO: fix occlusion of ports by realisation of long path.
                self.__connectivity.report(verbose = True)
                break

            excess_volume = self.__attempt_chain_realisation(candidate, maximal_excess = 12)
            if excess_volume == -1:
                console.info(f"> Failure to complete chain : {candidate}")
                if abort_on_failure:
                    break

            self.__connectivity.report()
            index += 1

            candidate = ZxGraphInflaterRings.__identify_next_chain(*zx_cycles)

        console.info(f"Cycles processed : {index}/{len(zx_cycles)}.")

    # TODO: handle case of disjoint rings (i.e. multiple connected components that contain cycles).
    @staticmethod
    def __identify_next_chain(*cycles: ZxCycle) -> ZxChain | None:
        all_chains: list[ZxChain] = CycleAnalyser.identify_chains(*cycles)
        console.critical(f"All chains identified :")
        for chain in all_chains:
            console.critical(f"> Chain : {chain}")
        selected: ZxChain | None = None
        for chain in all_chains:
            if selected:
                if chain.length < selected.length or (chain.length == selected.length and chain.distance > selected.distance):
                    selected = chain
            else:
                selected = chain

        console.debug(f"> Chain : {str(selected) if selected is not None else None}")

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
            # Since each of these node is realised as part of a ring, it already has two of its edges realised.
            self.__connectivity.reserve(node.realising_cube, required = self.__graph.get_zx_degree(node.id) - 2)

        for cube in ring.cubes[len(zx_cycle):]:
            self.__connectivity.occlude(cube.position)

        return len(ring.cubes) - len(zx_cycle)

    def __attempt_chain_realisation(self, chain: ZxChain, maximal_excess: int = 0) -> int:
        # start, nodes, edges, final = chain

        if not chain.source.is_realised() or not chain.source.is_realised():
            return -1

        if not self.__connectivity.available(chain.source.realising_cube, chain.source.realising_cube):
            return -1

        strand = self.__strandfinder.find_optimum(chain, maximal_excess = maximal_excess)

        if strand is None:
            console.error(f"Failed to find a strand for : {chain}")
            return -1

        excess_volume = strand.length - chain.length - 1
        console.info(f"Found a suitable strand for chain [EV:+{excess_volume}] : {strand}")

        self.__graph.realise_zx_chain(chain, strand)

        # Reserve the ports for all the nodes that were realised as part of this ring.
        for node in chain.nodes:
            # Since each of these node is part of a ring, it already has two of its edges realised.
            self.__connectivity.reserve(node.realising_cube, required =self.__graph.get_zx_degree(node.id) - 2)

        for cube in strand.extra_cubes[chain.length-1:]:
            self.__connectivity.occlude(cube.position)

        return excess_volume