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
from qelebrimbor.common.attributes_bg import CubeId
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.deprecated.pathfinder_dfs import PathFinderDFS
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.spacetime.connectivity.sufficient_ports import OpenPortsTracker
from qelebrimbor.spacetime.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser
from qelebrimbor.utilities.ring_making import extract_chain
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

    def process(self):
        CycleBasisAnalyser.analyse(self.__graph, minimal = True)
        zx_cycles = CycleBasisAnalyser.decompose_nodes(self.__graph, minimal = True)

        index = 0
        for zx_cycle in zx_cycles:
            console.info(f"> Cycle {index} : {zx_cycle}")
            index += 1

            if all(not zxn.is_realised() for zxn in zx_cycle):
                if not self.__attempt_ring_realisation(zx_cycle):
                    console.error(f"Failure to realise ring : {zx_cycle}")
                    break
            else:
                if not self.__attempt_ring_completion(zx_cycle, maximal_excess= 10):
                    console.error(f"Failure to realise ring : {zx_cycle}")
                    break

            self.__ports_tracker.verify_ports()

        console.info(f"All {len(zx_cycles)} cycles processed.")

    def __attempt_ring_realisation(self, zx_nodes: list[ZxNode], maximal_overhead: int = 6) -> bool:
        nc = len(zx_nodes)

        zx_edges = [
            ZxEdge(source=zx_nodes[s], target=zx_nodes[(s + 1) % nc],
                   type=self.__graph.get_zx_edge(zx_nodes[s].id, zx_nodes[(s + 1) % nc].id).type)
            for s in range(nc)
        ]

        realisations = RingFinderBFS.find_minimal_rings(zx_nodes, zx_edges, maximal_overhead = maximal_overhead)
        ring = realisations[0]

        console.info(f"Found {len(realisations)} realisations for cycle : {zx_nodes}")
        console.info(f"> Realisation [{ring.manhattan_length()}] : {ring}")

        nodes_specifications = ring.to_nodes_specifications(zx_nodes)
        console.info(f"> Nodes specifications : {nodes_specifications}")
        success = BlockGraphConstructor.realise_nodes(graph=self.__graph, specifications=nodes_specifications)

        console.info(f"> Nodes realisations : {success}")

        if not success:
            return False

        for node_id, bg_cube in nodes_specifications.items():
            self.__ports_tracker.occlude_ports(bg_cube.position)

        for node in zx_nodes:
            self.__ports_tracker.reserve_ports(node.realising_cube)

        edges_specifications = ring.to_edges_specifications(zx_edges)
        console.info(f"> Edges specifications :")
        for edge, proposal in edges_specifications.items():
            console.info(f">> {edge} : {proposal}")
        success = BlockGraphConstructor.realise_edges(graph=self.__graph, specifications=edges_specifications)

        console.info(f"> Edges realisations : {success}")

        if not success:
            return False

        for edge_id, path in edges_specifications.items():
            source = self.__graph.get_zx_node(edge_id[0]).realising_cube
            target = self.__graph.get_zx_node(edge_id[1]).realising_cube
            self.__ports_tracker.close_ports(source, 1)
            self.__ports_tracker.close_ports(target, 1)

        return True

    def __extract_chain(self, cycle: list[ZxNode]) -> list[ZxNode]:
        nc = len(cycle)

        transition_ru = next(
            (idx+1) % nc for idx in range(nc)
            if self.__graph.get_zx_edge(cycle[idx].id, cycle[(idx+1) % nc].id).is_realised() and not self.__graph.get_zx_edge(cycle[(idx+1) % nc].id, cycle[(idx+2) % nc].id).is_realised()
        )

        realised = sum(1 for idx in range(nc) if self.__graph.get_zx_edge(cycle[idx].id, cycle[(idx+1) % nc].id).is_realised())

        return [
            cycle[(transition_ru + idx) % nc] for idx in range(nc - realised + 1)
        ]

    def __attempt_ring_completion(self,
        cycle: list[ZxNode],
        maximal_excess: int = 0
    ):
        nc = len(cycle)
        chain = self.__extract_chain(cycle)
        start = chain[0]
        final = chain[-1]

        zx_nodes = chain[1:-1]
        zx_edges = [ self.__graph.get_zx_edge(chain[i].id, chain[(i + 1) % nc].id) for i in range(len(zx_nodes)+1) ]

        console.info(f"Breakdown : {start} - {zx_nodes} - {final}")

        if not start.is_realised() or not final.is_realised():
            return False

        start_cube = start.realising_cube
        final_cube = final.realising_cube
        console.info(f"Searching completion from {start_cube} to {final_cube}.")
        console.info(f"> Nodes : {zx_nodes}")
        console.info(f"> Edges : {zx_edges}")

        if not self.__ports_tracker.reachable(start_cube) or not self.__ports_tracker.reachable(final_cube):
            return False

        completion = PathFinderDFS.find_minimal_paths(
            source = start_cube, target = final_cube,
            zx_nodes = zx_nodes,
            zx_edges = zx_edges,
            graph = self.__graph,
            maximal_excess = maximal_excess
        )

        if completion is None:
            console.error(f"Failed to find a path for {start} - {zx_nodes} - {final}")
            return False

        console.info(f"Completion found : {completion}")

        nodes_specifications: dict[NodeId, BgCube] = dict()
        for idx in range(len(zx_nodes)):
            nodes_specifications[zx_nodes[idx].id] = completion.extra_cubes[idx]

        console.info(f"> Nodes specifications : {nodes_specifications}")
        BlockGraphConstructor.realise_nodes(self.__graph, nodes_specifications)

        for node_id, bg_cube in nodes_specifications.items():
            self.__ports_tracker.occlude_ports(bg_cube.position)

        for node in zx_nodes:
            self.__ports_tracker.reserve_ports(node.realising_cube)

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

        console.info(f"> Edges specifications :")
        for edge, proposal in edges_specifications.items():
            console.info(f">> {edge} : {proposal}")

        BlockGraphConstructor.realise_edges(graph=self.__graph, specifications=edges_specifications)

        for edge_id, completion in edges_specifications.items():
            source = self.__graph.get_zx_node(edge_id[0]).realising_cube
            target = self.__graph.get_zx_node(edge_id[1]).realising_cube
            self.__ports_tracker.close_ports(source, 1)
            self.__ports_tracker.close_ports(target, 1)

            for cube in completion.extra_cubes:
                self.__ports_tracker.occlude_ports(cube.position)

        return True