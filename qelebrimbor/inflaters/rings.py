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

from qelebrimbor.common.components import ZxNode, ZxEdge
from qelebrimbor.common.attributes_bg import CubeId
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.deprecated.pathfinder_dfs import PathFinderDFS
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

console = logging.getLogger(__name__)

class ZxGraphInflaterRings:
    def __init__(self, graph: VolumetricZxGraph):
        self.__graph = graph
        self.__node_realisations = 0
        self.__edge_realisations = 0

    def process(self):
        cycles = CycleBasisAnalyser.decompose_nodes(self.__graph)

        console.info(f"Found {len(cycles)} cycles")
        count = 0
        for cycle in cycles:
            console.info(f"> Cycle : {cycle}")
            if count == 0:
                self.__attempt_ring_realisation(cycle)
            else:
                self.__attempt_ring_completion(cycle, maximal_overhead = 10)
            count += 1

    def __attempt_ring_realisation(self, zx_nodes: list[ZxNode], maximal_overhead: int = 6):
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
        BlockGraphConstructor.realise_nodes(graph=self.__graph, specifications=nodes_specifications)

        edges_specifications = ring.to_edges_specifications(zx_edges)
        console.info(f"> Edges specifications :")
        for edge, proposal in edges_specifications.items():
            console.info(f">> {edge} : {proposal}")
        BlockGraphConstructor.realise_edges(graph=self.__graph, specifications=edges_specifications)

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
            cycle: list[ZxNode], maximal_overhead: int = 0, reservations: dict[Coordinates, CubeId] | None = None
    ):
        nc = len(cycle)
        chain = self.__extract_chain(cycle)
        start = chain[0]
        final = chain[-1]

        zx_nodes = chain[1:-1]
        zx_edges = [ self.__graph.get_zx_edge(chain[i].id, chain[(i + 1) % nc].id) for i in range(len(zx_nodes)+1) ]

        console.info(f"Breakdown of {cycle} :")
        console.info(f"> {start} - {zx_nodes} - {final}")

        start_cube = start.realising_cube
        final_cube = final.realising_cube
        console.info(f"Searching completion from {start_cube} to {final_cube}.")
        console.info(f"> Nodes : {zx_nodes}")
        console.info(f"> Edges : {zx_edges}")
        unavailable_positions = self.__graph.occupied.copy()
        if reservations is not None:
            unavailable_positions.update(reservations.keys())
        completions = PathFinderDFS.find_minimal_paths(
            start = start_cube, final = final_cube,
            node_types = [ node.type for node in zx_nodes ],
            edge_types = [ edge.type for edge in zx_edges ],
            unavailable_positions = unavailable_positions,
            maximal_overhead = maximal_overhead
        )

        console.info(f"Found {len(completions)} completions for chain {chain}")

        completion = completions[0]
        console.info(f"Completion : {completion.source} - {completion.extras} - {completion.target}")

        nodes_specifications = completion.to_nodes_specifications(zx_nodes)
        console.info(f"> Nodes specifications : {nodes_specifications}")
        BlockGraphConstructor.realise_nodes(self.__graph, nodes_specifications)

        edges_specifications = completion.to_edges_specifications(zx_edges)
        console.info(f"> Edges specifications :")
        for edge, proposal in edges_specifications.items():
            console.info(f">> {edge} : {proposal}")
        BlockGraphConstructor.realise_edges(self.__graph, edges_specifications)

        return True