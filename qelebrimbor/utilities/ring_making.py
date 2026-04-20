from collections import defaultdict, deque

import itertools

from qelebrimbor.common.components import BgCube, ZxNode, ZxEdge
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.common.attributes_zx import NodeId, EdgeId, EdgeType
from qelebrimbor.common.attributes_bg import CubeId, CubeKind

import logging
console = logging.getLogger(__name__)

def find_realisation(graph: VolumetricZxGraph, cycle: list[NodeId], maximal_overhead: int = 0):
    nc = len(cycle)

    zx_nodes = [
        ZxNode(id = cycle[i], type = graph.get_zx_node(cycle[i]).type)
        for i in range(nc)
    ]
    zx_edges = [
        ZxEdge(source = cycle[s], target = cycle[(s+1) % nc], type = graph.get_zx_edge(cycle[s], cycle[(s+1)%nc]).type)
        for s in range(nc)
    ]

    realisations = RingFinderBFS.find_minimal_rings(zx_nodes, zx_edges, maximal_overhead = maximal_overhead)
    ring = realisations[0]

    console.info(f"Found {len(realisations)} realisations for cycle : {cycle}")
    console.info(f"> Realisation [{ring.manhattan_length()}] : {ring}")

    BlockGraphConstructor.realise_nodes(vzx = graph, specifications = ring.to_nodes_specifications(zx_nodes))
    BlockGraphConstructor.realise_edges(vzx = graph, specifications = ring.to_edges_specifications(graph, zx_edges))

# TODO: go beyond assumption that cycle is made of one realised chain and one unrealised chain
# TODO: figure out which edges are missing if all the nodes are already placed
# TODO: after placing a ring, try placing the adjacents of the constituents of the ring
# TODO: only place those constituents if there is only one position for them to be in (i.e. positions determined)
def extract_chain(graph: VolumetricZxGraph, cycle: list[NodeId]) -> list[NodeId]:
    nc = len(cycle)
    chain: list[NodeId] = []

    transition_ru = next(
        (idx+1) % nc for idx in range(nc)
        if graph.is_zx_edge_realised(cycle[idx], cycle[(idx+1) % nc]) and not graph.is_zx_edge_realised(cycle[(idx+1) % nc], cycle[(idx+2) % nc])
    )

    realised = sum(1 for idx in range(nc) if graph.is_zx_edge_realised(cycle[idx], cycle[(idx+1) % nc]))

    return [
        cycle[(transition_ru + idx) % nc] for idx in range(nc - realised + 1)
    ]

def find_completion(
        graph: VolumetricZxGraph, cycle: list[NodeId],
        maximal_overhead: int = 0,
        reservations: dict[Coordinates, CubeId] | None = None
):
    nc = len(cycle)
    chain = extract_chain(graph, cycle)
    start = chain[0]
    extras = chain[1:-1]
    final = chain[-1]

    console.info(f"Breakdown of {cycle} :")
    console.info(f"> {start} - {extras} - {final}")

    zx_nodes = [ graph.get_zx_node(nd) for nd in extras ]
    zx_edges = [ graph.get_zx_edge(chain[i], chain[(i + 1) % nc]) for i in range(len(extras)+1) ]

    start_cube = graph.get_bg_cube(graph.get_zx_node(start).realising_cube)
    final_cube = graph.get_bg_cube(graph.get_zx_node(final).realising_cube)
    console.info(f"Searching completion from {start_cube} to {final_cube}.")
    console.info(f"> Nodes : {zx_nodes}")
    console.info(f"> Edges : {zx_edges}")
    unavailable_positions = graph.occupied.copy()
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
    console.info(f"Realisation : {completion.source} - {completion.extras} - {completion.target}")

    nodes_specifications = completion.to_nodes_specifications(zx_nodes)
    console.info(f"> Nodes specifications : {nodes_specifications}")
    BlockGraphConstructor.realise_nodes(graph, nodes_specifications)
    edges_specifications = completion.to_edges_specifications(graph, zx_edges)
    console.info(f"> Edges specifications : {edges_specifications}")
    BlockGraphConstructor.realise_edges(graph, edges_specifications)

    return True

def extend_unrealised(graph: VolumetricZxGraph):
    schedule: dict[NodeId, list[NodeId]] = defaultdict(list)
    for node in filter(lambda nd : graph.is_zx_node_realised(nd), graph.nodes):
        for neighbor in filter(lambda nd : not graph.is_zx_node_realised(nd), graph.neighbors(node)):
            schedule[node].append( neighbor )

    edges_specifications: dict[EdgeId, PathSpecification] = {}

    for node, neighbors in schedule.items():
        node_kind = graph.get_bg_cube(graph.get_zx_node(node).realising_cube).kind
        cube = graph.get_bg_cube(graph.get_zx_node(node).realising_cube)
        cube_reach = cube.kind.get_reach()
        for neighbor in neighbors:
            available = filter(
                lambda pos : pos not in graph.occupied,
                Spacetime.get_constellation(cube.position, cube.kind.get_reach())
            )
            edge_type = graph.get_zx_edge(node, neighbor).type
            neighbor_position = next(iter(available))
            step_taken = cube.position - neighbor_position
            neighbor_kinds = [
                kind for kind in CubeKind.suitable_kinds(graph.get_zx_node(neighbor).type)
                if Spacetime.contains(kind.get_reach(), step_taken) and Spacetime.contains(cube_reach, step_taken) and
                   edge_type in BlockGraphHelper.infer_pipe_type(node_kind, kind)
            ]
            neighbor_cube = BgCube(neighbor_kinds[0], neighbor_position)
            graph.realise_zx_node(neighbor, neighbor_cube)
            source, target = (node, neighbor) if node < neighbor else (neighbor, node)
            edges_specifications[ source, target ] = PathSpecification(
                source_cube = graph.get_zx_node(source).realising_cube,
                target_cube = graph.get_zx_node(target).realising_cube,
                pipes = [ edge_type ]
            )

    BlockGraphConstructor.realise_edges(graph, edges_specifications)