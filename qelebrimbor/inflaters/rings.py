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

from functools import total_ordering
from recordclass import RecordClass

from qelebrimbor.common.path import Path
from qelebrimbor.common.components import ZxNode, ZxEdge, BgCube
from qelebrimbor.common.attributes_zx import NodeId, EdgeId, EdgeType
from qelebrimbor.common.attributes_bg import CubeId
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.deprecated.pathfinder_dfs import PathFinderDFS
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.least_cycle_analyser import MinimalCycleBasisAnalyser
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

@total_ordering
class Vertex(RecordClass):
    cube: BgCube
    required_ports: int
    available_ports: set[Coordinates]

    @property
    def remaining_ports(self):
        return len(self.available_ports) - self.required_ports

    def __lt__(self, other):
        return self.remaining_ports < other.remaining_ports if self.remaining_ports != other.remaining_ports else self.required_ports <= other.required_ports

    def __str__(self):
        return f"{self.cube} [rq:{self.required_ports},av:{len(self.available_ports)}]"

    def __repr__(self):
        return str(self)

class ZxGraphInflaterRings:
    def __init__(self, graph: VolumetricZxGraph):
        self.__graph = graph
        self.__node_realisations = 0
        self.__edge_realisations = 0

        self.__vertices: dict[BgCube, Vertex] = {}
        self.__reservations: dict[Coordinates, BgCube] = dict()

    def __occlude_ports(self, position: Coordinates):
        if position in self.__reservations:
            holder = self.__vertices[self.__reservations[position]]
            holder.available_ports.remove(position)
            self.__reservations.pop(position)

    def __reserve_ports(self, cube: BgCube):
        vertex = Vertex(
            cube = cube, required_ports = self.__graph.get_zx_degree(cube.realised_node.id), available_ports = set()
        )
        constellation = SpacetimeHelper.get_constellation(cube.position, cube.kind.get_reach())
        for position in constellation:
            if position in self.__reservations:
                console.warning(f"Position {position} already reserved by {self.__reservations[position]} [requester={cube}]")
                continue

            if position not in self.__graph.occupied:
                self.__reservations[position] = cube
                vertex.available_ports.add(position)

        self.__vertices[cube] = vertex

    def __verify_ports(self):
        for vertex in self.__vertices.values():
            if vertex.remaining_ports == 0:
                console.warning(f"VP> Time to prioritize {vertex}")
            elif vertex.remaining_ports < 0:
                console.error(f"VP> TOO LATE for {vertex}")

    def process(self):
        MinimalCycleBasisAnalyser.analyse(self.__graph)
        zx_cycles = MinimalCycleBasisAnalyser.decompose_nodes(self.__graph)

        for zx_cycle in zx_cycles:
            console.info(f"> Cycle : {zx_cycle}")
            try:
                if all(not zxn.is_realised() for zxn in zx_cycle):
                    self.__attempt_ring_realisation(zx_cycle)
                else:
                    self.__attempt_ring_completion(zx_cycle, maximal_excess= 10)
            except Exception as e:
                console.error(f"FAILURE of attempt to construct cycle {zx_cycle}")
                raise e

            self.__verify_ports()

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

        for node_id, bg_cube in nodes_specifications.items():
            self.__occlude_ports(bg_cube.position)

        for node in zx_nodes:
            self.__reserve_ports(node.realising_cube)

        edges_specifications = ring.to_edges_specifications(zx_edges)
        console.info(f"> Edges specifications :")
        for edge, proposal in edges_specifications.items():
            console.info(f">> {edge} : {proposal}")
        BlockGraphConstructor.realise_edges(graph=self.__graph, specifications=edges_specifications)

        for edge_id, path in edges_specifications.items():
            source = self.__graph.get_zx_node(edge_id[0]).realising_cube
            target = self.__graph.get_zx_node(edge_id[1]).realising_cube
            self.__vertices[source].required_ports -= 1
            self.__vertices[target].required_ports -= 1

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
        maximal_excess: int = 0,
        reservations: dict[Coordinates, CubeId] | None = None
    ):
        nc = len(cycle)
        chain = self.__extract_chain(cycle)
        start = chain[0]
        final = chain[-1]

        zx_nodes = chain[1:-1]
        zx_edges = [ self.__graph.get_zx_edge(chain[i].id, chain[(i + 1) % nc].id) for i in range(len(zx_nodes)+1) ]

        console.info(f"Breakdown of {cycle} :")
        console.info(f"> {start} - {zx_nodes} - {final}")

        if not start.is_realised() or not final.is_realised():
            return False

        start_cube = start.realising_cube
        final_cube = final.realising_cube
        console.info(f"Searching completion from {start_cube} to {final_cube}.")
        console.info(f"> Nodes : {zx_nodes}")
        console.info(f"> Edges : {zx_edges}")
        unavailable_positions = self.__graph.occupied.copy()
        if reservations is not None:
            unavailable_positions.update(reservations.keys())

        if self.__vertices[start_cube].remaining_ports < 0 or self.__vertices[final_cube].remaining_ports < 0:
            return False

        completion = PathFinderDFS.find_minimal_paths(
            source= start_cube, target= final_cube,
            zx_nodes = zx_nodes,
            zx_edges = zx_edges,
            unavailable_positions = unavailable_positions,
            graph = self.__graph,
            reservations = self.__reservations,
            maximal_excess = maximal_excess
        )

        if completion is None:
            console.error(f"Failed to find any completion for cycle {cycle}")
            return False

        console.info(f"Completion : {completion}")

        nodes_specifications: dict[NodeId, BgCube] = dict()
        for idx in range(len(zx_nodes)):
            nodes_specifications[zx_nodes[idx].id] = completion.extra_cubes[idx]

        console.info(f"> Nodes specifications : {nodes_specifications}")
        BlockGraphConstructor.realise_nodes(self.__graph, nodes_specifications)

        for node_id, bg_cube in nodes_specifications.items():
            self.__occlude_ports(bg_cube.position)

        for node in zx_nodes:
            self.__reserve_ports(node.realising_cube)

        edge_count = len(zx_edges)
        extra_count = len(completion.extra_cubes)
        edges_specifications: dict[EdgeId, Path] = {}

        previous_node = completion.start.realised_node
        for edge in zx_edges[:-1]:
            current_node = edge.source if edge.source != previous_node else edge.target
            path = Path(start = previous_node.realising_cube).extend(current_node.realising_cube, edge.type)
            edges_specifications[ (previous_node.id, current_node.id) ] = path
            previous_node = current_node

        final_edge = zx_edges[-1]
        source = previous_node
        target = final_edge.source if final_edge.source != previous_node else final_edge.target
        extras = completion.extra_cubes[edge_count-1 : extra_count]
        path = Path(start = source.realising_cube)
        for cube, pipe in zip(extras, [ final_edge.type if i == 0 else EdgeType.IDENTITY for i in range(extra_count - edge_count + 2)]):
            path = path.extend(cube, pipe)
        path = path.extend(target.realising_cube, EdgeType.IDENTITY)
        edges_specifications[(source.id, target.id)] = path

        console.info(f"> Edges specifications :")
        for edge, proposal in edges_specifications.items():
            console.info(f">> {edge} : {proposal}")
        BlockGraphConstructor.realise_edges(graph=self.__graph, specifications=edges_specifications)

        for edge_id, path in edges_specifications.items():
            source = self.__graph.get_zx_node(edge_id[0]).realising_cube
            target = self.__graph.get_zx_node(edge_id[1]).realising_cube
            self.__vertices[source].required_ports -= 1
            self.__vertices[target].required_ports -= 1

            for cube in path.extra_cubes:
                self.__occlude_ports(cube.position)

        return True