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

from termcolor import colored

from qelebrimbor.analysis.cycles import CycleAnalyser, ZxChain, ZxCycle
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker
from qelebrimbor.spacetime.ringfinders.breadth_first_search import RingfinderBFS
from qelebrimbor.spacetime.strandfinders.colorblind_fusion_dfs import StrandfinderColorblindFusionDFS

console = logging.getLogger(__name__)


class ZxGraphInflaterRings:
    def __init__(self, graph: VolumetricZxGraph, cycles: list[ZxCycle], verbose: bool = False):
        self.__graph = graph
        self.__connectivity: ConnectivityTracker = OpenPortsTracker(graph)
        self.__ringfinder = RingfinderBFS(self.__graph)
        self.__strandfinder = StrandfinderColorblindFusionDFS(self.__graph, self.__connectivity, branch_and_bound=True)

        self.__verbose = verbose
        self.__zx_cycles = cycles

    def process(self, abort_on_failure: bool = True, abort_on_index: int = -1) -> int:
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

        # Realise all subsequent chains
        candidate: ZxChain | None = self.__identify_next_chain(*zx_cycles)

        while candidate is not None and count < len(zx_cycles):
            console.info(f"Attempting realisation of chain [index={count}, md={candidate.distance}] : {candidate}")

            if count == abort_on_index:
                console.info("> Premature abortion for inspection of specific example.")
                # TODO: fix occlusion of ports by realisation of long path.
                self.__connectivity.report(verbose=True)
                return -2

            excess_volume = self.__attempt_chain_realisation(candidate, maximal_excess=20)
            if excess_volume == -1:
                console.info(f"> Failure to complete chain : {candidate}")
                if self.__verbose:
                    print(">>> Failure to find a strand for chain.")
                if abort_on_failure:
                    return -1

            self.__connectivity.report()
            count += 1

            candidate = ZxGraphInflaterRings.__identify_next_chain(*zx_cycles)

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
                if chain.length < selected.length or (
                    chain.length == selected.length and chain.distance > selected.distance
                ):
                    selected = chain
            else:
                selected = chain

        return selected

    def __attempt_ring_realisation(self, cycle: ZxCycle, maximal_excess: int = 0) -> int:
        # TODO: the following call is the bottleneck of the overall inflation process ...
        if self.__verbose:
            print(f">> Attempting realisation of cycle [L={cycle.length}] : {cycle}")
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
            self.__connectivity.reserve(node.realising_cube, required=self.__graph.get_zx_degree(node.id) - 2)

        cubes = list(ring.cubes)
        for cube in cubes[len(cycle) :]:
            self.__connectivity.occlude(cube.position)

        return excess_volume

    def __attempt_chain_realisation(self, chain: ZxChain, maximal_excess: int = 0) -> int:
        if self.__verbose:
            print(f">> Attempting realisation of chain [L={chain.length}] : {chain}")

        if not chain.source.is_realised() or not chain.source.is_realised():
            return -1

        if not self.__connectivity.available(chain.source.realising_cube, chain.source.realising_cube):
            return -1

        strand = self.__strandfinder.find_optimum(chain, maximal_excess=maximal_excess)

        if strand is None:
            console.error(f"Failed to find a strand for : {chain}")
            return -1

        excess_volume = strand.length - chain.length - 1
        console.info(f"Found a suitable strand for chain [EV:+{excess_volume}] : {strand}")

        self.__graph.realise_zx_chain(chain, strand)

        if self.__verbose:
            print(f">>> Realised as strand [EV:+{excess_volume}] : {strand}")

        # Reserve the ports for all the nodes that were realised as part of this ring.
        for node in chain.nodes:
            # Since each of these node is part of a ring, it already has two of its edges realised.
            self.__connectivity.reserve(node.realising_cube, required=self.__graph.get_zx_degree(node.id) - 2)

        extra_cubes = list(strand.extras)
        for cube in extra_cubes[chain.length - 1 :]:
            self.__connectivity.occlude(cube.position)

        return excess_volume
