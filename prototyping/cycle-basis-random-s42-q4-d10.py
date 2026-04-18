import random
from collections import defaultdict

import pyzx

from qelebrimbor.common.attributes_bg import CubeId, CubeKind
from qelebrimbor.common.attributes_zx import NodeId, EdgeId, EdgeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser

SEED = 42
QUBITS = 4
LAYERS = 10

import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders.pathfinder_dfs').setLevel(logging.DEBUG)
logging.getLogger('qelebrimbor.ringfinders.ringfinder_bfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.utilities.blockgraph_constructor').setLevel(logging.CRITICAL)

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

# TODO: sort the mess that multiple realising_cubes introduce here
def place_determined(graph: VolumetricZxGraph):
    for node in graph.nodes:
        if graph.is_zx_node_realised(node):
            unrealised_neighbors = list(filter(lambda nb: not graph.is_zx_edge_realised(node, nb), graph.neighbors(node)))
            if len(unrealised_neighbors) != 1:
                continue

            open_ports: dict[CubeId, list[Coordinates]] = defaultdict(list)
            cube = graph.get_zx_node(node).realising_cube
            if cube != -1:
                cube_reach = graph.get_bg_cube(cube).kind.get_reach()
                cube_position = graph.get_bg_cube(cube).position
                for port in Spacetime.get_constellation(cube_position, cube_reach):
                    if port not in graph.occupied:
                        open_ports[cube].append(port)

            if sum(len(pts) for pts in open_ports.values()) == 1:
                neighbor = unrealised_neighbors[0]
                edge_type = graph.get_zx_edge(node, neighbor).type
                cube, ports = next(iter(open_ports.items()))
                cube_kind = graph.get_bg_cube(cube).kind
                cube_reach = cube_kind.get_reach()
                cube_position = graph.get_bg_cube(cube).position
                port_position = ports[0]
                console.info(f"Node {node} has an unrealised neighbor {neighbor} that must be placed now at {port_position}.")
                step_taken = port_position - cube_position
                console.info(f"> Step taken : {step_taken}")
                neighbor_type = graph.get_zx_node(neighbor).type
                neighbor_reach = next(filter(
                    lambda cr :
                        Spacetime.contains(cr, step_taken) and Spacetime.contains(cube_reach, step_taken) and
                        edge_type in BlockGraphHelper.infer_pipe_type(cube_kind, CubeKind.convert(neighbor_type, cr)),
                        [ Spacetime.XP, Spacetime.YP, Spacetime.ZP ]
                ))
                neighbor_kind = CubeKind.convert(neighbor_type, neighbor_reach)
                neighbor_cube = graph.realise_zx_node(neighbor, neighbor_kind, port_position)
                graph.realise_zx_edge(node, neighbor, PathSpecification(cube, neighbor_cube, extras = [], pipes = [edge_type]))

# TODO: sort the mess that multiple realising_cubes introduce here
def reserve_positions(graph: VolumetricZxGraph, reservations: dict[Coordinates, CubeId]):
    for node in graph.nodes:
        if graph.is_zx_node_realised(node):
            unrealised_neighbors = list(filter(lambda nb: not graph.is_zx_edge_realised(node, nb), graph.neighbors(node)))
            open_ports: dict[Coordinates, CubeId] = dict()
            cube = graph.get_zx_node(node).realising_cube
            if cube != -1:
                cube_reach = graph.get_bg_cube(cube).kind.get_reach()
                cube_position = graph.get_bg_cube(cube).position
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

def find_completion_edges(
        graph: VolumetricZxGraph, cycle: list[NodeId],
        maximal_overhead: int = 10,
        reservations: dict[Coordinates, CubeId] | None = None
):
    reserved = reservations if reservations else dict()

    nc = len(cycle)
    start, final, extras = breakdown_cycle(graph, cycle)

    console.info(f"Breakdown of {cycle} : {start} - {extras} - {final}")

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
            pipes = [ pipes1[-1] if i == 0 else EdgeType.IDENTITY for i in range(nc)]
        )
    })

    return True

random.seed(SEED)
if __name__ == "__main__":
    circuit = f"random-s{SEED}-q{QUBITS}-d{LAYERS}"
    zx = pyzx.generate.cnots(qubits = QUBITS, depth = LAYERS)
    # pyzx.draw(zx, labels = True)

    with open(f"../assets/pyzx/{circuit}.json", 'w') as file:
        file.write(zx.to_json())

    vzx = VolumetricZxGraph.from_pyzx_graph(zx)

    CycleBasisAnalyser.analyse(vzx)

    cycles = CycleBasisAnalyser.decompose(vzx)
    cycle0 = cycles[0]
    edges0 = [ (cycle0[i], cycle0[(i+1) % len(cycle0)]) for i in range(len(cycle0)) ]
    n0 = len(cycle0)

    console.info(f"Cycle 0 : {cycle0}")
    nodes0 = list(map(lambda nd : vzx.get_zx_node(nd).type, cycle0))
    pipes0 = list(map(lambda ed : vzx.get_zx_edge(*ed).type, edges0))
    console.info(f"Nodes 0 : {" ".join(map(lambda nd: str(nd) + ':' + str(vzx.get_zx_node(nd).type), cycle0))}")
    console.info(f"Edges 0 : {" ".join(map(lambda ed: str(vzx.get_zx_edge(*ed).type)[0] + str(ed).replace(' ',''), edges0))}")

    realisations0 = RingFinderBFS.find_minimal_rings(nodes0, pipes0, maximal_overhead = 2)
    ring0 = realisations0[0]

    console.info(f"Realisation 0 [{len(ring0.cubes)}] : {ring0}")

    BlockGraphConstructor.realise_nodes(vzx, {cycle0[nd]: ring0.cubes[nd] for nd in range(n0)})

    cycle0 = cycles[0]
    start = cycle0[0]
    final = cycle0[n0 - 1]
    if final < start:
        start, final = final, start
    c0 = len(ring0.cubes)
    BlockGraphConstructor.realise_edges(vzx,
        specifications = {
            (start, final): PathSpecification(
                source_cube = vzx.get_zx_node(start).realising_cube,
                target_cube = vzx.get_zx_node(final).realising_cube,
                extras = list(reversed(ring0.cubes[n0:c0])),
                pipes = pipes0
            )
        }
    )

    reservations: dict[Coordinates, CubeId] = dict()

    place_determined(vzx)
    reserve_positions(vzx, reservations)

    cycle1 = cycles[1]
    console.info(f"Cycle 1 : {cycle1}")
    find_completion(graph = vzx, cycle = cycle1, reservations = reservations)

    place_determined(vzx)
    reserve_positions(vzx, reservations)

    cycle2 = cycles[2]
    console.info(f"Cycle 2 : {cycle2}")
    find_completion(graph = vzx, cycle = cycle2, reservations = reservations)

    place_determined(vzx)
    reserve_positions(vzx, reservations)

    cycle3 = cycles[3]
    console.info(f"Cycle 3 : {cycle3}")
    find_completion(graph = vzx, cycle = cycle3, reservations = reservations)

    place_determined(vzx)
    reserve_positions(vzx, reservations)

    cycle4 = cycles[4]
    console.info(f"Cycle 4 : {cycle4}")
    # find_completion(vzx, cycle4)

    excess_volume: dict[EdgeId, int] = dict()
    for edge in vzx.edges:
        if vzx.is_zx_edge_realised(*edge):
            count = len(vzx.get_zx_edge(*edge).realisation) - 1
            if count > 0:
                excess_volume[edge] = count

    console.info(f"Excess volume :")
    for edge in excess_volume:
        console.info(f"> {edge} : +{excess_volume[edge]}")

    console.info(f"Total volume : {vzx.number_of_cubes()}")
    viewer = VolumetricZxGraphViewer(vzx, label = circuit)
    viewer.display()