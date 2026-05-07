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

from qelebrimbor.common.path import Path
from qelebrimbor.common.components import ZxNode, ZxEdge, BgCube
from qelebrimbor.common.attributes_zx import NodeId, EdgeId, EdgeType
from qelebrimbor.spacetime.chainfinders.depth_first_search import ChainfinderDFS
from qelebrimbor.spacetime.connectivity.sufficient_ports import OpenPortsTracker
from qelebrimbor.deprecated.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.cycle_analyser import ZxChainNodes, CycleAnalyser
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class ZxGraphInflaterRings:
    def __init__(self, graph: VolumetricZxGraph):
        self.__graph = graph
        self.__spacetime = graph.spacetime
        self.__node_realisations = 0
        self.__edge_realisations = 0

        self.__ports_tracker: OpenPortsTracker = OpenPortsTracker(graph)

        self.__ringfinder = RingFinderBFS()
        self.__chainfinder = ChainfinderDFS(self.__graph, self.__ports_tracker)

    def process(self):
        zx_cycles = CycleAnalyser.decompose_nodes(self.__graph, minimal = True)

        realised: set[int] = set()

        count: int = 0
        root_ring = zx_cycles[0]

        # Realise the root ring
        console.info(f"> Root ring identified : {root_ring}")
        excess_volume: int = self.__attempt_ring_realisation(root_ring)
        if excess_volume == -1:
            console.info(f"> Failure [cause:unknown]")
            console.info(f"Cycles processed : {count}/{len(zx_cycles)}.")

        console.info(f"> Realisation successful with excess volume : +{excess_volume} cubes.")
        count += 1

        # Realise all subsequent chains
        candidate: tuple[int, ZxChainNodes] | None = self.__identify_next_chain(realised, zx_cycles)

        while candidate is not None and count < len(zx_cycles):
            index, chain = candidate
            console.info(f"> Next chain identified : {candidate}")

            excess_volume = self.__attempt_ring_completion(chain, maximal_excess = 10)
            if excess_volume == -1:
                console.info(f"> Failure to complete chain : {candidate}")
                break
            console.info(f"> Chain completed with excess volume : +{excess_volume} cubes.")

            self.__ports_tracker.verify_ports()

            count += 1
            realised.add(index)

            candidate = self.__identify_next_chain(realised, zx_cycles)

        console.info(f"Cycles processed : {count}/{len(zx_cycles)}.")

    # TODO: handle case of disjoint rings (i.e. multiple connected components that contain cycles).
    def __identify_next_chain(self, realised: set[int], cycles: list[list[ZxNode]]) -> tuple[int, ZxChainNodes] | None:
        all_chains: list[tuple[int, ZxChainNodes]] = CycleAnalyser.identify_chains(self.__graph, realised, cycles)
        selected_length: int | None = None
        selected_distance: int |None = None
        selected: tuple[int, ZxChainNodes] | None = None
        for index, chain in all_chains:
            start = chain[0].realising_cube
            final = chain[-1].realising_cube
            length = len(chain)
            distance = start.position.get_manhattan_distance(final.position)
            if selected:
                if length < selected_length or (length == selected_length and distance > selected_distance):
                    selected = index, chain
                    selected_length = length
                    selected_distance = distance
            else:
                selected = index, chain
                selected_length = length
                selected_distance = distance

            console.debug(f"> Chain [L:{len(chain)}, D:{distance}] : {chain}")

        return selected

    def __attempt_ring_realisation(self, zx_cycle: list[ZxNode], maximal_overhead: int = 6) -> int:
        nc = len(zx_cycle)

        zx_edges = [
            ZxEdge(
                source = zx_cycle[s], target = zx_cycle[(s + 1) % nc],
                type=self.__graph.get_zx_edge(zx_cycle[s].id, zx_cycle[(s + 1) % nc].id).type
            ) for s in range(nc)
        ]

        # TODO: the following call is the bottleneck of the overall inflation process ...
        realisations = RingFinderBFS.find_minimal_rings(zx_cycle, zx_edges, maximal_overhead = maximal_overhead)
        ring = realisations[0]

        console.debug(f"Found {len(realisations)} realisations for cycle : {zx_cycle}")
        console.debug(f"> Realisation [{ring.volume()}] : {ring}")

        nodes_specifications = ring.to_nodes_specifications(zx_cycle)
        console.debug(f"> Nodes specifications : {nodes_specifications}")

        for node_id, cube in nodes_specifications.items():
            self.__ports_tracker.reserve_ports(cube = cube, required_ports = self.__graph.get_zx_degree(node_id))

        success = BlockGraphConstructor.realise_nodes(graph=self.__graph, specifications=nodes_specifications)

        if not success:
            return -1

        edges_specifications = ring.to_edges_specifications(zx_edges)
        console.debug(f"> Edges specifications :")
        for edge, proposal in edges_specifications.items():
            console.debug(f">> {edge} : {proposal}")
        success = BlockGraphConstructor.realise_edges(graph=self.__graph, specifications=edges_specifications)

        if not success:
            return -1

        for edge_id, path in edges_specifications.items():
            source = self.__graph.get_zx_node(edge_id[0]).realising_cube
            target = self.__graph.get_zx_node(edge_id[1]).realising_cube
            self.__ports_tracker.connect_ports(
                source = (source, path.start_port),
                target = (target, path.final_port)
            )

        for node_id, bg_cube in nodes_specifications.items():
            self.__ports_tracker.occlude_ports(bg_cube.position)

        return len(ring.cubes) - len(zx_cycle)

    def __attempt_ring_completion(self,
        chain: ZxChainNodes,
        maximal_excess: int = 0
    ) -> int:
        start = chain[0]
        final = chain[-1]

        zx_nodes = chain[1:-1]
        zx_edges = [ self.__graph.get_zx_edge(chain[i].id, chain[(i + 1) % len(chain)].id) for i in range(len(zx_nodes)+1) ]

        console.debug(f"> Breaking down into chain : {chain}")
        console.debug(f">> Nodes : {zx_nodes}")
        console.debug(f">> Edges : {zx_edges}")

        if not start.is_realised() or not final.is_realised():
            return -1

        start_cube = start.realising_cube
        final_cube = final.realising_cube
        console.debug(f"Searching completion from {start_cube} to {final_cube}.")
        console.debug(f"> Nodes : {zx_nodes}")
        console.debug(f"> Edges : {zx_edges}")

        if not self.__ports_tracker.reachable(start_cube) or not self.__ports_tracker.reachable(final_cube):
            return -1

        zx_edges = [ self.__graph.get_zx_edge(chain[i].id, chain[(i + 1) % len(chain)].id) for i in range(len(zx_nodes)+1) ]

        excess_volume = self.__attempt_chain_realisation(
            start = start.realising_cube, final = final.realising_cube,
            zx_nodes= chain[1:-1], zx_edges = zx_edges, maximal_excess = maximal_excess)

        return excess_volume

    def __attempt_chain_realisation(
            self, start: BgCube, final: BgCube,
            zx_nodes: list[ZxNode], zx_edges: list[ZxEdge],
            maximal_excess: int = 0
    ) -> int:
        completion = self.__chainfinder.find_minimal_paths(
            source = start, target = final,
            zx_nodes = zx_nodes, zx_edges = zx_edges,
            maximal_excess = maximal_excess
        )

        if completion is None:
            console.error(f"Failed to find a chain for {start} - {zx_nodes} - {final}")
            return -1

        console.debug(f"Completion found : {completion}")

        nodes_specifications: dict[NodeId, BgCube] = dict()
        for idx in range(len(zx_nodes)):
            node = zx_nodes[idx]
            cube = completion.extra_cubes[idx]
            nodes_specifications[node.id] = cube
            self.__ports_tracker.reserve_ports(cube, self.__graph.get_zx_degree(node.id))

        console.debug(f"> Nodes specifications : {nodes_specifications}")
        BlockGraphConstructor.realise_nodes(self.__graph, nodes_specifications)

        edge_count = len(zx_edges)
        extra_count = len(completion.extra_cubes)
        edges_specifications: dict[EdgeId, Path] = {}

        previous_node = completion.start.realised_node
        for edge in zx_edges[:-1]:
            current_node = edge.source if edge.source != previous_node else edge.target
            partial = Path(start = previous_node.realising_cube).extend(current_node.realising_cube, edge.type)
            edges_specifications[ (previous_node.id, current_node.id) ] = partial
            previous_node = current_node

        final_edge = zx_edges[-1]
        source = previous_node
        target = final_edge.source if final_edge.source != previous_node else final_edge.target
        extras = completion.extra_cubes[edge_count-1 : extra_count]
        partial = Path(start = source.realising_cube)
        for cube, pipe in zip(extras, [ EdgeType.IDENTITY for i in range(len(extras)) ]):
            partial = partial.extend(cube, pipe)
        partial = partial.extend(target.realising_cube, final_edge.type)
        edges_specifications[(source.id, target.id)] = partial

        console.debug(f"> Edges specifications :")
        for edge, proposal in edges_specifications.items():
            console.debug(f">> {edge} : {proposal}")

        BlockGraphConstructor.realise_edges(graph=self.__graph, specifications=edges_specifications)

        for edge_id, partial in edges_specifications.items():
            source = self.__graph.get_zx_node(edge_id[0]).realising_cube
            target = self.__graph.get_zx_node(edge_id[1]).realising_cube
            self.__ports_tracker.connect_ports(
                source = (source, partial.start_port),
                target = (target, partial.final_port)
            )

            for cube in partial.extra_cubes:
                self.__ports_tracker.occlude_ports(cube.position)

        for node_id, bg_cube in nodes_specifications.items():
            self.__ports_tracker.occlude_ports(bg_cube.position)

        return completion.volume() - len(zx_nodes) - 1