import random
from collections import defaultdict

import pyzx

from qelebrimbor.common.attributes_bg import CubeId, CubeKind
from qelebrimbor.common.attributes_zx import EdgeId
from qelebrimbor.common.components import BgCube, ZxEdge
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.utilities.ring_making import find_realisation, find_completion
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser

SEED = 42
QUBITS = 4
LAYERS = 10

import logging
logging.basicConfig(level=logging.CRITICAL)
console = logging.getLogger(__name__)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.INFO)

# TODO: sort the mess that multiple realising_cubes introduce here
def place_determined(graph: VolumetricZxGraph):
    for node in graph.get_zx_nodes():
        if node.is_realised():
            unrealised_neighbors = list(
                filter(lambda nb: not graph.get_zx_edge(node.id, nb).is_realised(), graph.neighbors(node.id))
            )
            if len(unrealised_neighbors) != 1:
                continue

            open_ports: dict[BgCube, list[Coordinates]] = defaultdict(list)
            cube = node.realising_cube
            if cube is not None:
                cube_reach = cube.kind.get_reach()
                for port in SpacetimeHelper.get_constellation(cube.position, cube_reach):
                    if port not in graph.occupied:
                        open_ports[cube].append(port)

            if sum(len(pts) for pts in open_ports.values()) == 1:
                neighbor = unrealised_neighbors[0]
                edge_type = graph.get_zx_edge(node.id, neighbor).type
                cube, ports = next(iter(open_ports.items()))
                cube_reach = cube.kind.get_reach()
                port_position = ports[0]
                console.info(f"Node {node} has an unrealised neighbor {neighbor} that must be placed now at {port_position}.")
                step_taken = port_position - cube.position
                console.info(f"> Step taken : {step_taken}")
                neighbor_type = graph.get_zx_node(neighbor).type
                neighbor_reach = next(filter(
                    lambda cr :
                    SpacetimeHelper.contains(cr, step_taken) and SpacetimeHelper.contains(cube_reach, step_taken) and
                    edge_type in BlockGraphHelper.infer_pipe_type(cube.kind, CubeKind.convert(neighbor_type, cr)),
                        [SpacetimeHelper.XP, SpacetimeHelper.YP, SpacetimeHelper.ZP]
                ))
                neighbor_cube = BgCube(CubeKind.convert(neighbor_type, neighbor_reach), port_position)
                neighbor_cube_id = graph.realise_zx_node(neighbor, neighbor_cube)
                graph.realise_zx_edge(node, neighbor, PathSpecification(cube, neighbor_cube, extras = [], pipes = [edge_type]))

# TODO: sort the mess that multiple realising_cubes introduce here
def reserve_positions(graph: VolumetricZxGraph, reservations: dict[Coordinates, BgCube]):
    for node in graph.get_zx_nodes():
        if node.is_realised():
            unrealised_neighbors = list(
                filter(lambda nb: not graph.get_zx_edge(node.id, nb).is_realised(), graph.neighbors(node.id))
            )
            open_ports: dict[Coordinates, BgCube] = dict()
            cube = graph.get_zx_node(node).realising_cube
            if cube is not None:
                cube_reach = cube.kind.get_reach()
                for port in SpacetimeHelper.get_constellation(cube.position, cube_reach):
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

    cycles = CycleBasisAnalyser.decompose_nodes(vzx)

    index = 0
    cycle = cycles[index]
    console.info(f"Cycle {index} : {cycle}")
    find_realisation(vzx, cycle, maximal_overhead = 2)

    for index in range(1, 4):
        cycle = cycles[index]
        console.info(f"Cycle {index} : {cycle}")
        find_completion(vzx, cycle, maximal_overhead = 10)

    vzx.log_report()

    viewer = VolumetricZxGraphViewer(vzx, label = circuit)
    viewer.display()