from collections import defaultdict

from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.common.components_zx import NodeId, EdgeType
from qelebrimbor.common.components_bg import CubeId, CubeKind

import logging
console = logging.getLogger(__name__)

# TODO: go beyond assumption that cycle is made of one realised chain and one unrealised chain
# TODO: figure out which edges are missing if all the nodes are already placed
# TODO: after placing a ring, try placing the adjacents of the constituents of the ring
# TODO: only place those constituents if there is only one position for them to be in (i.e. positions determined)
def breakdown_cycle(graph: VolumetricZxGraph, cycle: list[NodeId]) -> tuple[NodeId, NodeId, list[NodeId]]:
    nc = len(cycle)

    transition_ur = next(
        idx for idx in range(nc)
        if not graph.is_node_realised(cycle[(idx-1) % nc]) and graph.is_node_realised(cycle[idx])
    )

    transition_ru = next(
        idx for idx in range(nc)
        if graph.is_node_realised(cycle[idx]) and not graph.is_node_realised(cycle[(idx + 1) % nc])
    )

    realised = sum(1 for idx in range(nc) if graph.is_node_realised(cycle[idx]))

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

    nodes1 = list(map(lambda nd : graph.get_node_type(nd), extras))
    edges1 = [(cycle[i], cycle[(i + 1) % len(cycle)]) for i in range(1, len(extras) + 1)]
    pipes1 = list(map(lambda ed : graph.get_edge_type(*ed), edges1))

    # # Breakdown cycle1
    # TODO: deal with case where multiple cubes realise the start of the final
    start_cube_id = next(iter(graph.get_realising_cubes(start)))
    final_cube_id = next(iter(graph.get_realising_cubes(final)))
    start_cube = (graph.get_cube_kind(start_cube_id), graph.get_cube_position(start_cube_id))
    final_cube = (graph.get_cube_kind(final_cube_id), graph.get_cube_position(final_cube_id))
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
            source_cube = next(iter(graph.get_realising_cubes(source))),
            target_cube = next(iter(graph.get_realising_cubes(target))),
            extras = extra_cubes,
            pipes = [ pipes1[-1] if i == 0 else EdgeType.IDENTITY for i in range(nr)]
        )
    })

    return True

def extend_unrealised(graph: VolumetricZxGraph):
    schedule: dict[NodeId, list[NodeId]] = defaultdict(list)
    for node in filter(lambda nd : graph.is_node_realised(nd), graph.nodes):
        for neighbor in filter(lambda nd : not graph.is_node_realised(nd), graph.neighbors(node)):
            schedule[node].append( neighbor )

    for node, neighbors in schedule.items():
        node_kind = graph.get_cube_kind(next(iter(graph.get_realising_cubes(node))))
        cube = next(iter(graph.get_realising_cubes(node)))
        cube_position = graph.get_cube_position(cube)
        cube_reach = graph.get_cube_kind(cube).get_reach()
        for neighbor in neighbors:
            available = filter(
                lambda pos: pos not in graph.occupied,
                Spacetime.get_constellation(cube_position, cube_reach)
            )
            edge_type = graph.get_edge_type(node, neighbor)
            neighbor_position = next(available)
            step_taken = cube_position - neighbor_position
            neighbor_kinds = [
                kind for kind in CubeKind.suitable_kinds(graph.get_node_type(neighbor))
                if Spacetime.contains(kind.get_reach(), step_taken) and Spacetime.contains(cube_reach, step_taken) and
                   edge_type in BlockGraphHelper.infer_pipe_type(node_kind, kind)
            ]
            console.info(f"{node} - {neighbor} : {neighbor_kinds}")
            neighbor_kind = neighbor_kinds[0]
            graph.realise_node(neighbor, neighbor_kind, neighbor_position)

    BlockGraphConstructor.realise_edges(graph, {})