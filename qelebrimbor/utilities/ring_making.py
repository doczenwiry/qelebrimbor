from collections import defaultdict

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

    nodes = list(map(lambda nd : graph.get_zx_node(nd).type, cycle))
    edges = [(cycle[i], cycle[(i + 1) % nc]) for i in range(nc)]
    pipes = list(map(lambda ed : graph.get_zx_edge(*ed).type, edges))
    console.debug(f"> Nodes : {" ".join(map(lambda nd: str(nd) + ':' + str(graph.get_zx_node(nd).type), cycle))}")
    console.debug(f"> Edges : {" ".join(map(lambda ed: str(graph.get_zx_edge(*ed).type)[0] + str(ed).replace(' ', ''), edges))}")

    realisations = RingFinderBFS.find_minimal_rings(nodes, pipes, maximal_overhead = maximal_overhead)
    ring = realisations[0]

    console.info(f"Found {len(realisations)} realisations for cycle : {cycle}")
    console.info(f"> Realisation [{len(ring.cubes)}] : {ring}")

    BlockGraphConstructor.realise_nodes(graph, {cycle[nd]: ring.cubes[nd] for nd in range(nc)})

    start = cycle[0]
    final = cycle[nc - 1]
    nr = len(ring.cubes)
    extras = list(reversed(ring.cubes[nc:nr]))
    if final < start:
        start, final = final, start
        extras = list(reversed(extras))
    BlockGraphConstructor.realise_edges(graph,
        specifications = {
            (start, final): PathSpecification(
                source_cube = graph.get_zx_node(start).realising_cube,
                target_cube = graph.get_zx_node(final).realising_cube,
                extras = extras,
                pipes = pipes
            )
        }
    )

# TODO: go beyond assumption that cycle is made of one realised chain and one unrealised chain
# TODO: figure out which edges are missing if all the nodes are already placed
# TODO: after placing a ring, try placing the adjacents of the constituents of the ring
# TODO: only place those constituents if there is only one position for them to be in (i.e. positions determined)
def breakdown_cycle(graph: VolumetricZxGraph, cycle: list[NodeId]) -> tuple[NodeId, NodeId, list[NodeId]]:
    nc = len(cycle)

    transition_ur = next(
        idx for idx in range(nc)
        if not graph.is_zx_node_realised(cycle[(idx - 1) % nc]) and graph.is_zx_node_realised(cycle[idx])
    )

    transition_ru = next(
        idx for idx in range(nc)
        if graph.is_zx_node_realised(cycle[idx]) and not graph.is_zx_node_realised(cycle[(idx + 1) % nc])
    )

    realised = sum(1 for idx in range(nc) if graph.is_zx_node_realised(cycle[idx]))

    intermediates: list[NodeId] = [
        cycle[(transition_ru + 1 + idx) % nc] for idx in range(nc - realised)
    ]

    if cycle[transition_ur] < cycle[transition_ru]:
        transition_ur, transition_ru = transition_ru, transition_ur
        intermediates = list(reversed(intermediates))

    return cycle[transition_ru], cycle[transition_ur], intermediates

def find_completion(
        graph: VolumetricZxGraph, cycle: list[NodeId],
        maximal_overhead: int = 10,
        reservations: dict[Coordinates, CubeId] | None = None
):
    reserved = reservations if reservations else dict()

    nc = len(cycle)
    start, final, extras = breakdown_cycle(graph, cycle)

    console.info(f"Breakdown of {cycle} : {start} - {extras} - {final}")

    nodes1 = list(map(lambda nd : graph.get_zx_node(nd).type, extras))
    edges1 = [(cycle[i], cycle[(i + 1) % len(cycle)]) for i in range(1, len(extras) + 1)]
    pipes1 = list(map(lambda ed : graph.get_zx_edge(*ed).type, edges1))

    # # Breakdown cycle1
    # TODO: deal with case where multiple cubes realise the start of the final
    start_cube_id = graph.get_zx_node(start).realising_cube
    final_cube_id = graph.get_zx_node(final).realising_cube
    start_cube = (graph.get_bg_cube(start_cube_id).kind, graph.get_bg_cube(start_cube_id).position)
    final_cube = (graph.get_bg_cube(final_cube_id).kind, graph.get_bg_cube(final_cube_id).position)
    console.info(f"Searching completion from {start}#{start_cube_id} [{start_cube}] to {final}#{final_cube_id} [{final_cube}]")
    console.info(f"> Nodes : {nodes1}")
    console.info(f"> Pipes : {pipes1}")
    minimal_overhead, rings = PathFinderDFS.find_minimal_paths(
        start = start_cube, final = final_cube,
        node_types = nodes1,
        edge_types = pipes1,
        occupied_positions = graph.occupied,
        reserved_positions = reserved,
        maximal_overhead = maximal_overhead
    )

    console.info(f"Found {len(rings)} realisations for cycle.")

    if len(rings) == 0:
        return False

    ring = rings[0]
    nr = len(ring.cubes)
    console.info(f"Realisation 1 : {ring.cubes}")

    BlockGraphConstructor.realise_nodes(graph, {
        extras[idx] : ring.cubes[idx+1] for idx in range(len(extras))
    })

    terminal_cube_id = extras[-1]
    source, target = final, terminal_cube_id
    extra_cubes: list[tuple[CubeKind, Coordinates]]
    if final > terminal_cube_id:
        source, target = target, source
        extra_cubes = ring.cubes[len(extras)+1:nr - 1]
    else:
        extra_cubes = list(reversed(ring.cubes[len(extras)+1:nr - 1]))

    BlockGraphConstructor.realise_edges(graph, {
        (source, target): PathSpecification(
            source_cube = graph.get_zx_node(source).realising_cube,
            target_cube = graph.get_zx_node(target).realising_cube,
            extras = extra_cubes,
            pipes = [ pipes1[-1] if i == 0 else EdgeType.IDENTITY for i in range(nr)]
        )
    })

    return True

def extend_unrealised(graph: VolumetricZxGraph, edge_specifications: dict[EdgeId, PathSpecification | None] | None = None):
    schedule: dict[NodeId, list[NodeId]] = defaultdict(list)
    for node in filter(lambda nd : graph.is_zx_node_realised(nd), graph.nodes):
        for neighbor in filter(lambda nd : not graph.is_zx_node_realised(nd), graph.neighbors(node)):
            schedule[node].append( neighbor )

    for node, neighbors in schedule.items():
        node_kind = graph.get_bg_cube(graph.get_zx_node(node).realising_cube).kind
        cube = graph.get_zx_node(node).realising_cube
        cube_position = graph.get_bg_cube(cube).position
        cube_reach = graph.get_bg_cube(cube).kind.get_reach()
        for neighbor in neighbors:
            available = filter(
                lambda pos: pos not in graph.occupied,
                Spacetime.get_constellation(cube_position, cube_reach)
            )
            edge_type = graph.get_zx_edge(node, neighbor).type
            neighbor_position = next(available)
            step_taken = cube_position - neighbor_position
            neighbor_kinds = [
                kind for kind in CubeKind.suitable_kinds(graph.get_zx_node(neighbor).type)
                if Spacetime.contains(kind.get_reach(), step_taken) and Spacetime.contains(cube_reach, step_taken) and
                   edge_type in BlockGraphHelper.infer_pipe_type(node_kind, kind)
            ]
            neighbor_kind = neighbor_kinds[0]
            graph.realise_zx_node(neighbor, neighbor_kind, neighbor_position)

    BlockGraphConstructor.realise_edges(graph, edge_specifications or dict())