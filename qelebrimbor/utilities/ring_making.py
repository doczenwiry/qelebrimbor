from collections import defaultdict

from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.common.components_zx import NodeId, EdgeId, EdgeType
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

def identify_unrealised_edges(graph: VolumetricZxGraph, cycle: list[NodeId]) -> list[EdgeId]:
    nc = len(cycle)
    chains: list[EdgeId] = []

    for idx in range(nc):
        source = cycle[idx]
        target = cycle[(idx + 1) % nc]
        if not graph.is_edge_realised(source, target):
            chains.append( (source,target) )

    return chains

# TODO: sort the mess that multiple realising_cubes introduce here
def place_determined(graph: VolumetricZxGraph):
    for node in graph.nodes:
        if graph.is_node_realised(node):
            unrealised_neighbors = list(filter(lambda nb: not graph.is_edge_realised(node, nb), graph.neighbors(node)))
            if len(unrealised_neighbors) != 1:
                continue

            open_ports: dict[CubeId, list[Coordinates]] = defaultdict(list)
            for cube in graph.get_realising_cubes(node):
                cube_reach = graph.get_cube_kind(cube).get_reach()
                cube_position = graph.get_cube_position(cube)
                for port in Spacetime.get_constellation(cube_position, cube_reach):
                    if port not in graph.occupied:
                        open_ports[cube].append(port)

            if sum(len(pts) for pts in open_ports.values()) == 1:
                neighbor = unrealised_neighbors[0]
                edge_type = graph.get_edge_type(node, neighbor)
                cube, ports = next(iter(open_ports.items()))
                cube_kind = graph.get_cube_kind(cube)
                cube_reach = cube_kind.get_reach()
                cube_position = graph.get_cube_position(cube)
                port_position = ports[0]
                console.info(f"Node {node} has an unrealised neighbor {neighbor} that must be placed now at {port_position}.")
                step_taken = port_position - cube_position
                console.info(f"> Step taken : {step_taken}")
                neighbor_type = graph.get_node_type(neighbor)
                neighbor_reach = next(filter(
                    lambda cr :
                        Spacetime.contains(cr, step_taken) and Spacetime.contains(cube_reach, step_taken) and
                        edge_type in BlockGraphHelper.infer_pipe_type(cube_kind, CubeKind.convert(neighbor_type, cr)),
                        [ Spacetime.XP, Spacetime.YP, Spacetime.ZP ]
                ))
                neighbor_kind = CubeKind.convert(neighbor_type, neighbor_reach)
                neighbor_cube = graph.realise_node(neighbor, neighbor_kind, port_position)
                graph.realise_edge(node, neighbor, PathSpecification(cube, neighbor_cube, extras = [], pipes = [ edge_type ]))

# TODO: sort the mess that multiple realising_cubes introduce here
def reserve_positions(graph: VolumetricZxGraph, reservations: dict[Coordinates, CubeId]):
    for node in graph.nodes:
        if graph.is_node_realised(node):
            unrealised_neighbors = list(filter(lambda nb: not graph.is_edge_realised(node, nb), graph.neighbors(node)))
            open_ports: dict[Coordinates, CubeId] = dict()
            for cube in graph.get_realising_cubes(node):
                cube_reach = graph.get_cube_kind(cube).get_reach()
                cube_position = graph.get_cube_position(cube)
                for port in Spacetime.get_constellation(cube_position, cube_reach):
                    if port not in graph.occupied:
                        if port in open_ports and port in reservations and cube != reservations[port]:
                            console.warning(f"Multiple cubes [{open_ports[port]},{cube}] realising the same node have the a port in common. Overwriting.")
                        open_ports[port] = cube

            if len(unrealised_neighbors) == len(open_ports) > 1:
                for port, cube in open_ports.items():
                    if port in reservations and cube != reservations[port]:
                        console.error(f"Port {port} is already reserved by cube #{cube}.")
                    else:
                        console.info(f"Reserving port {port} for cube #{cube} [{node}].")
                        reservations[port] = cube

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
            pipes = [ pipes1[-1] if i == 0 else EdgeType.IDENTITY for i in range(nc)]
        )
    })

    return True