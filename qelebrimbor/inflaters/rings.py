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
from qelebrimbor.spacetime.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.cycle_analyser import CycleAnalyser
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.deprecated.pathfinder_dfs import PathFinderDFS

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
        self.__chainfinder = PathFinderDFS() #ChainfinderDFS(tracing = True)

    def process(self):
        CycleAnalyser.analyse(self.__graph, minimal = True)
        zx_cycles = CycleAnalyser.decompose_nodes(self.__graph, minimal = True)

        realised: set[int] = set()

        count: int = 0

        # Realise the root ring
        excess_volume: int = self.__attempt_ring_realisation(zx_cycles[0])
        if excess_volume == -1:
            console.info(f"> Failure to realise ring : {zx_cycles[0]}")
            console.info(f"Cycles processed : {count}/{len(zx_cycles)}.")

        console.info(f"> Ring realised with excess volume : +{excess_volume} cubes.")
        count += 1

        # Realise the remaining completions
        index: int = self.__select_candidate(realised, zx_cycles)

        while index != -1 and count < len(zx_cycles):
            zx_cycle = zx_cycles[index]
            console.info(f"Cycle {index} : {zx_cycle}")

            if all(not zxn.is_realised() for zxn in zx_cycle):
                raise NotImplementedError(f"Support for disjoint rings not currently implemented.")

            excess_volume = self.__attempt_ring_completion(zx_cycle, maximal_excess = 10)
            if excess_volume == -1:
                console.info(f"> Failure to complete ring : {zx_cycle}")
                break
            console.info(f"> Ring completed with excess volume : +{excess_volume} cubes.")

            count += 1
            realised.add(index)

            index = self.__select_candidate(realised, zx_cycles)

        console.info(f"Cycles processed : {count}/{len(zx_cycles)}.")

    def __select_candidate(self, realised: set[int], cycles: list[list[ZxNode]]):
        minimal_distance = None
        selected = -1

        for index in range(len(cycles)):
            if index in realised:
                continue

            cycle = cycles[index]

            if all( self.__graph.get_zx_edge(cycle[index].id, cycle[(index+1) % len(cycle)].id).is_realised()
                    for index in range(len(cycle))
            ):
                console.debug(f"> Cycle {cycle} is already complete. Skipping.")
                continue

            if any(node.is_realised() for node in cycle):
                console.debug(f"> Cycle {cycle} intersects current construct.")
                chain = CycleAnalyser.breakdown(self.__graph, cycle)
                source = chain[0].realising_cube
                target = chain[-1].realising_cube
                extras = chain[1:-1]

                console.debug(f"> Breakdown : {source} -> {extras} -> {target}")

                distance = source.position.get_manhattan_distance(target.position)
                console.debug(f"> Endpoints {source} - {target} : distance={distance}, chain={len(extras)}")

                if minimal_distance is None or distance < minimal_distance:
                    minimal_distance = distance
                    selected = index

        return selected

    def __attempt_ring_realisation(self, zx_nodes: list[ZxNode], maximal_overhead: int = 6) -> int:
        nc = len(zx_nodes)

        zx_edges = [
            ZxEdge(source=zx_nodes[s], target=zx_nodes[(s + 1) % nc],
                   type=self.__graph.get_zx_edge(zx_nodes[s].id, zx_nodes[(s + 1) % nc].id).type)
            for s in range(nc)
        ]

        # TODO: the following call is the bottleneck of the overall inflation process ...
        realisations = RingFinderBFS.find_minimal_rings(zx_nodes, zx_edges, maximal_overhead = maximal_overhead)
        ring = realisations[0]

        console.debug(f"Found {len(realisations)} realisations for cycle : {zx_nodes}")
        console.debug(f"> Realisation [{ring.manhattan_length()}] : {ring}")

        nodes_specifications = ring.to_nodes_specifications(zx_nodes)
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

        return len(ring.cubes) - len(zx_nodes)

    def __attempt_ring_completion(self,
        cycle: list[ZxNode],
        maximal_excess: int = 0
    ) -> int:
        chain = CycleAnalyser.breakdown(self.__graph, cycle)
        return self.__attempt_chain_realisation(chain, maximal_excess)

    def __attempt_chain_realisation(self, chain: list[ZxNode], maximal_excess: int = 0) -> int:
        start = chain[0]
        final = chain[-1]

        zx_nodes = chain[1:-1]
        zx_edges = [ self.__graph.get_zx_edge(chain[i].id, chain[(i + 1) % len(chain)].id) for i in range(len(zx_nodes)+1) ]

        console.info(f"> Breaking down into chain : {chain}")
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

        completion = self.__chainfinder.find_minimal_paths(
            source = start_cube, target = final_cube,
            zx_nodes = zx_nodes, zx_edges = zx_edges,
            graph = self.__graph,
            maximal_excess = maximal_excess
        )

        if completion is None:
            console.error(f"Failed to find a path for {start} - {zx_nodes} - {final}")
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

        return completion.manhattan_length() - len(zx_nodes) - 1