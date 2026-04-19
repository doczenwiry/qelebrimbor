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

    transition_ru = next(
        idx for idx in range(nc)
        if graph.is_zx_node_realised(cycle[idx]) and not graph.is_zx_node_realised(cycle[(idx + 1) % nc])
    )

    realised = sum(1 for idx in range(nc) if graph.is_zx_node_realised(cycle[idx]))

    return [
        cycle[(transition_ru + idx) % nc] for idx in range(nc - realised + 2)
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

    console.info(f"Breakdown of {cycle} : {start} - {extras} - {final}")
    console.info(f"> Chain : {chain}")

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
    nr = len(completion.extras)
    console.info(f"Realisation : {completion.source} - {completion.extras} - {completion.target}")

    BlockGraphConstructor.realise_nodes(graph, completion.to_nodes_specifications(zx_nodes))
    BlockGraphConstructor.realise_edges(graph, completion.to_edges_specifications(graph, zx_edges))

    # terminal_cube_id = extras[-1]
    # source, target = final, terminal_cube_id
    # extra_cubes: list[BgCube]
    # if final > terminal_cube_id:
    #     source, target = target, source
    #     extra_cubes = completion.extras[len(extras) + 1:nr - 1]
    # else:
    #     extra_cubes = list(reversed(completion.extras[len(extras) + 1:nr - 1]))
    #
    # BlockGraphConstructor.realise_edges(graph, {
    #     (source, target): PathSpecification(
    #         source_cube= graph.get_zx_node(source).realising_cube,
    #         target_cube= graph.get_zx_node(target).realising_cube,
    #         extras = extra_cubes,
    #         pipes = [ pipes1[-1] if i == 0 else EdgeType.IDENTITY for i in range(nr)]
    #     )
    # })

    return True

def __find_realising_cubes(graph: VolumetricZxGraph, cube: BgCube):
    all_cubes: list[BgCube] = [ cube ]
    queue = deque([cube])
    while queue:
        current = queue.popleft()
        for neighbor in graph.get_cube_neighbours(current.id):
            neighbor_cube = graph.get_bg_cube(neighbor)
            if neighbor_cube.kind == cube.kind:
                all_cubes.append(neighbor_cube)
                if neighbor_cube not in all_cubes:
                    queue.append(neighbor_cube)
    return all_cubes

def extend_unrealised(graph: VolumetricZxGraph, edge_specifications: dict[EdgeId, PathSpecification | None] | None = None):
    schedule: dict[NodeId, list[NodeId]] = defaultdict(list)
    for node in filter(lambda nd : graph.is_zx_node_realised(nd), graph.nodes):
        for neighbor in filter(lambda nd : not graph.is_zx_node_realised(nd), graph.neighbors(node)):
            schedule[node].append( neighbor )

    for node, neighbors in schedule.items():
        node_kind = graph.get_bg_cube(graph.get_zx_node(node).realising_cube).kind
        cube = graph.get_bg_cube(graph.get_zx_node(node).realising_cube)
        cube_reach = cube.kind.get_reach()
        realising_cubes = __find_realising_cubes(graph, cube)
        for neighbor in neighbors:
            available = [
                pos for pos in itertools.chain.from_iterable([
                    Spacetime.get_constellation(cube.position, cube.kind.get_reach()) for cube in realising_cubes
                ]) if pos not in graph.occupied
            ]
            edge_type = graph.get_zx_edge(node, neighbor).type
            neighbor_position = available[0]
            step_taken = cube.position - neighbor_position
            neighbor_kinds = [
                kind for kind in CubeKind.suitable_kinds(graph.get_zx_node(neighbor).type)
                if Spacetime.contains(kind.get_reach(), step_taken) and Spacetime.contains(cube_reach, step_taken) and
                   edge_type in BlockGraphHelper.infer_pipe_type(node_kind, kind)
            ]
            neighbor_cube = BgCube(neighbor_kinds[0], neighbor_position)
            graph.realise_zx_node(neighbor, neighbor_cube)

    BlockGraphConstructor.realise_edges(graph, edge_specifications or dict())