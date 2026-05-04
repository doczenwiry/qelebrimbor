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

from collections import defaultdict

from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.attributes_zx import NodeId, EdgeId, EdgeType
from qelebrimbor.common.attributes_bg import CubeId, CubeKind
from qelebrimbor.common.components import BgCube, ZxNode, ZxEdge
from qelebrimbor.common.path import Path

from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.spacetime.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.deprecated.pathfinder_dfs import PathFinderDFS

import logging
console = logging.getLogger(__name__)

def find_realisation(graph: VolumetricZxGraph, zx_nodes: list[ZxNode], maximal_overhead: int = 0):
    nc = len(zx_nodes)

    zx_edges = [
        ZxEdge(source = zx_nodes[s], target = zx_nodes[(s+1) % nc], type = graph.get_zx_edge(zx_nodes[s].id, zx_nodes[(s+1)%nc].id).type)
        for s in range(nc)
    ]

    realisations = RingFinderBFS.find_minimal_rings(zx_nodes, zx_edges, maximal_overhead = maximal_overhead)
    ring = realisations[0]

    console.info(f"Found {len(realisations)} realisations for cycle : {zx_nodes}")
    console.info(f"> Realisation [{ring.manhattan_length()}] : {ring}")

    nodes_specifications = ring.to_nodes_specifications(zx_nodes)
    console.info(f"> Nodes specifications : {nodes_specifications}")
    BlockGraphConstructor.realise_nodes(graph= graph, specifications = nodes_specifications)

    edges_specifications = ring.to_edges_specifications(zx_edges)
    console.info(f"> Edges specifications :")
    for edge, proposal in edges_specifications.items():
        console.info(f">> {edge} : {proposal}")
    BlockGraphConstructor.realise_edges(graph= graph, specifications = edges_specifications)

# TODO: go beyond assumption that cycle is made of one realised chain and one unrealised chain
# TODO: figure out which edges are missing if all the nodes are already placed
# TODO: after placing a ring, try placing the adjacents of the constituents of the ring
# TODO: only place those constituents if there is only one position for them to be in (i.e. positions determined)
def extract_chain(graph: VolumetricZxGraph, cycle: list[ZxNode]) -> list[ZxNode]:
    nc = len(cycle)

    transition_ru = next(
        (idx+1) % nc for idx in range(nc)
        if graph.get_zx_edge(cycle[idx].id, cycle[(idx+1) % nc].id).is_realised() and not graph.get_zx_edge(cycle[(idx+1) % nc].id, cycle[(idx+2) % nc].id).is_realised()
    )

    realised = sum(1 for idx in range(nc) if graph.get_zx_edge(cycle[idx].id, cycle[(idx+1) % nc].id).is_realised())

    return [
        cycle[(transition_ru + idx) % nc] for idx in range(nc - realised + 1)
    ]

def find_completion(
        graph: VolumetricZxGraph, cycle: list[ZxNode],
        maximal_overhead: int = 0,
        reservations: dict[Coordinates, ZxNode] | None = None
) -> bool:
    nc = len(cycle)
    chain = extract_chain(graph, cycle)
    start = chain[0]
    final = chain[-1]

    zx_nodes = chain[1:-1]
    zx_edges = [ graph.get_zx_edge(chain[i].id, chain[(i + 1) % nc].id) for i in range(len(zx_nodes)+1) ]

    console.info(f"Breakdown of {cycle} :")
    console.info(f"> {start} - {zx_nodes} - {final}")

    start_cube = start.realising_cube
    final_cube = final.realising_cube
    console.info(f"Searching completion from {start_cube} to {final_cube}.")
    console.info(f"> Nodes : {zx_nodes}")
    console.info(f"> Edges : {zx_edges}")
    completion = PathFinderDFS.find_minimal_paths(
        source = start_cube, target = final_cube,
        zx_nodes = zx_nodes,
        zx_edges = zx_edges,
        graph = graph,
        reservations = reservations,
        maximal_excess = maximal_overhead
    )

    if completion is None:
        return False

    console.info(f"Completion : {completion.start} - {completion.extra_cubes} - {completion.final}")

    nodes_specifications: dict[NodeId, BgCube] = {}
    for nd in range(len(zx_nodes)):
        nodes_specifications[zx_nodes[nd].id] = completion.extra_cubes[nd]
    console.info(f"> Nodes specifications : {nodes_specifications}")
    BlockGraphConstructor.realise_nodes(graph, nodes_specifications)

    edge_count = len(zx_edges)
    extra_count = len(completion.extra_cubes)
    edges_specifications: dict[EdgeId, Path] = {}

    previous_node = completion.start.realised_node
    for edge in zx_edges[:-1]:
        current_node = edge.source if edge.source != previous_node else edge.target
        path = Path(start=previous_node.realising_cube).extend(current_node.realising_cube, edge.type)
        edges_specifications[(previous_node.id, current_node.id)] = path
        previous_node = current_node

    final_edge = zx_edges[-1]
    source = previous_node
    target = final_edge.source if final_edge.source != previous_node else final_edge.target
    extras = completion.extra_cubes[edge_count - 1: extra_count]
    path = Path(start=source.realising_cube)
    for cube, pipe in zip(extras, [final_edge.type if i == 0 else EdgeType.IDENTITY for i in
                                   range(extra_count - edge_count + 2)]):
        path = path.extend(cube, pipe)
    path = path.extend(target.realising_cube, EdgeType.IDENTITY)
    edges_specifications[(source.id, target.id)] = path

    console.info(f"> Edges specifications :")
    for edge, proposal in edges_specifications.items():
        console.info(f">> {edge} : {proposal}")
    BlockGraphConstructor.realise_edges(graph=graph, specifications=edges_specifications)

    return True

def extend_unrealised(graph: VolumetricZxGraph):
    schedule: dict[ZxNode, list[ZxNode]] = defaultdict(list)
    for node in filter(lambda nd: nd.is_realised(), graph.get_zx_nodes()):
        for neighbor in filter(lambda nb : not nb.is_realised(), graph.get_zx_neighbors(node)):
            schedule[node].append( neighbor )

    edges_specifications: dict[EdgeId, Path] = {}

    for node, neighbors in schedule.items():
        cube = node.realising_cube
        cube_reach = cube.kind.get_reach()
        for neighbor in neighbors:
            available = filter(
                lambda pos : graph.spacetime.available(pos),
                SpacetimeHelper.get_constellation(cube.position, cube_reach)
            )
            edge_type = graph.get_zx_edge(node.id, neighbor.id).type

            try:
                neighbor_position = next(iter(available))
            except StopIteration:
                console.warning(f"No position available for neighbor {neighbor} of {node}")
                continue

            step_taken = cube.position - neighbor_position
            neighbor_kinds = [
                kind for kind in CubeKind.suitable_kinds(neighbor.type)
                if SpacetimeHelper.contains(kind.get_reach(), step_taken) and SpacetimeHelper.contains(cube_reach, step_taken) and
                   edge_type in BlockGraphHelper.infer_pipe_type(cube.kind, kind)
            ]
            neighbor_cube = BgCube(neighbor_kinds[0], neighbor_position)
            graph.realise_zx_node(neighbor, neighbor_cube)
            source, target = (node, neighbor) if node.id < neighbor.id else (neighbor, node)
            edges_specifications[ source.id, target.id ] = Path(start = source.realising_cube).extend(target.realising_cube, edge_type)

    BlockGraphConstructor.realise_edges(graph, edges_specifications)