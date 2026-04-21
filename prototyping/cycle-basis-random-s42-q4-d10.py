import random
from collections import defaultdict

import pyzx

from qelebrimbor.common.attributes_bg import CubeId, CubeKind
from qelebrimbor.common.attributes_zx import EdgeId
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.utilities.ring_making import find_realisation, find_completion
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser

SEED = 42
QUBITS = 4
LAYERS = 10

import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)
logging.getLogger('qelebrimbor.pathfinders.pathfinder_dfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.ringfinders.ringfinder_bfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.utilities.blockgraph_constructor').setLevel(logging.CRITICAL)

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
                neighbor_cube = BgCube(CubeKind.convert(neighbor_type, neighbor_reach), port_position)
                neighbor_cube_id = graph.realise_zx_node(neighbor, neighbor_cube)
                graph.realise_zx_edge(node, neighbor, PathSpecification(cube, neighbor_cube_id, extras = [], pipes = [edge_type]))

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

    index = 0
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_realisation(vzx, cycle, maximal_overhead = 2)

    for index in range(1, 4):
        cycle = cycles[index]
        console.info(f"Cycle {index} : {cycle}")
        find_completion(vzx, cycle, maximal_overhead = 10)

    excess_volume: dict[EdgeId, int] = dict()
    for edge in vzx.edges:
        if vzx.is_zx_edge_realised(*edge):
            count = len(vzx.get_zx_edge(*edge).realisation) - 1
            if count > 0:
                excess_volume[edge] = count

    console.info(f"Excess volume : +{sum(excess_volume.values())}")
    for edge in excess_volume:
        console.info(f"> {edge} : +{excess_volume[edge]}")

    console.info(f"Total volume : {vzx.number_of_cubes()}")
    viewer = VolumetricZxGraphViewer(vzx, label = circuit)
    viewer.display()