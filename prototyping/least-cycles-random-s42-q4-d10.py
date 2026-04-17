import random
import pyzx

from qelebrimbor.common.components_bg import CubeId
from qelebrimbor.common.components_zx import EdgeType, NodeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.least_cycle_analyser import MinimalCycleBasisAnalyser
from qelebrimbor.utilities.ring_making import place_determined, reserve_positions, find_completion, identify_unrealised_edges
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

SEED = 42
QUBITS = 4
LAYERS = 10

import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.utilities.ring_making').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.utilities.blockgraph_constructor').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders.pathfinder_dfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.ringfinders.ringfinder_bfs').setLevel(logging.CRITICAL)

random.seed(SEED)
if __name__ == "__main__":
    circuit = f"random-s{SEED}-q{QUBITS}-d{LAYERS}"
    zx = pyzx.generate.cnots(qubits = QUBITS, depth = LAYERS)
    # pyzx.full_reduce(zx)
    # pyzx.draw(zx, labels = True)

    with open(f"../assets/pyzx/{circuit}.json", 'w') as file:
        file.write(zx.to_json())

    vzx = VolumetricZxGraph.from_pyzx_graph(zx)

    MinimalCycleBasisAnalyser.analyse(vzx)

    cycles = MinimalCycleBasisAnalyser.decompose(vzx)

    cycle0 = cycles[0]
    edges0 = [ (cycle0[i], cycle0[(i+1) % len(cycle0)]) for i in range(len(cycle0)) ]
    n0 = len(cycle0)

    console.info(f"Cycle 0 : {cycle0}")
    nodes0 = list(map(lambda nd : vzx.get_node_type(nd), cycle0))
    pipes0 = list(map(lambda ed : vzx.get_edge_type(*ed), edges0))
    console.debug(f"Nodes 0 : {" ".join(map(lambda nd: str(nd) + ':' + str(vzx.get_node_type(nd)), cycle0))}")
    console.debug(f"Edges 0 : {" ".join(map(lambda ed: str(vzx.get_edge_type(*ed))[0] + str(ed).replace(' ',''), edges0))}")

    realisations0 = RingFinderBFS.find_minimal_rings(nodes0, pipes0, maximal_overhead = 2)
    ring0 = realisations0[0]

    console.debug(f"Realisation 0 [{len(ring0.cubes)}] : {ring0}")

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
                source_cube = min(vzx.get_realising_cubes(start)),
                target_cube = min(vzx.get_realising_cubes(final)),
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

    edges = identify_unrealised_edges(vzx, cycle4)
    console.debug(f"Chains [{len(edges)}]")
    for edge in edges:
        console.debug(f"> {edge}")
        start, final = edge
        if start > final:
            start, final = final, start
        start_cube_id = next(iter(vzx.get_realising_cubes(start)))
        final_cube_id = next(iter(vzx.get_realising_cubes(final)))
        start_cube = (vzx.get_cube_kind(start_cube_id), vzx.get_cube_position(start_cube_id))
        final_cube = (vzx.get_cube_kind(final_cube_id), vzx.get_cube_position(final_cube_id))
        pipes4 = [ vzx.get_edge_type(start, final) ]
        console.debug(f"Searching completion from {start}#{start_cube_id} [{start_cube}] to {final}#{final_cube_id} [{final_cube}]")
        minimal_overhead, rings = PathFinderDFS.find_minimal_paths(
            start = start_cube, final = final_cube,
            edge_types = pipes4,
            occupied_positions = vzx.occupied,
            reserved_positions = reservations,
            maximal_overhead = 6
        )

        console.debug(f"Found {len(rings)} realisations for cycle.")

        if len(rings) != 0:
            ring = rings[0]
            nr = len(ring.cubes)
            console.debug(f"Realisation 1 : {ring.cubes}")

            extras = ring.cubes[1:-1]
            BlockGraphConstructor.realise_edges(vzx, {
                (start, final): PathSpecification(
                    source_cube = next(iter(vzx.get_realising_cubes(start))),
                    target_cube = next(iter(vzx.get_realising_cubes(final))),
                    extras = extras,
                    pipes = [ pipes4[-1] if i == 0 else EdgeType.IDENTITY for i in range(nr)]
                )
            })

    cycle5 = cycles[5]
    console.info(f"Cycle 5 : {cycle5}")
    find_completion(graph = vzx, cycle = cycle5, reservations = reservations)

    cycle6 = cycles[6]
    console.info(f"Cycle 6 : {cycle6}")

    edges = identify_unrealised_edges(vzx, cycle6)
    console.debug(f"Chains [{len(edges)}]")
    for edge in edges:
        console.debug(f"> {edge}")
        start, final = edge
        if start > final:
            start, final = final, start
        start_cube_id = next(iter(vzx.get_realising_cubes(start)))
        final_cube_id = next(iter(vzx.get_realising_cubes(final)))
        start_cube = (vzx.get_cube_kind(start_cube_id), vzx.get_cube_position(start_cube_id))
        final_cube = (vzx.get_cube_kind(final_cube_id), vzx.get_cube_position(final_cube_id))
        pipes6 = [ vzx.get_edge_type(start, final) ]
        console.debug(f"Searching completion from {start}#{start_cube_id} [{start_cube}] to {final}#{final_cube_id} [{final_cube}]")
        minimal_overhead, rings = PathFinderDFS.find_minimal_paths(
            start = start_cube, final = final_cube,
            edge_types = pipes6,
            occupied_positions = vzx.occupied,
            reserved_positions = reservations,
            maximal_overhead = 6
        )

        console.debug(f"Found {len(rings)} realisations for cycle.")

        if len(rings) != 0:
            ring = rings[0]
            nr = len(ring.cubes)
            console.debug(f"Realisation 1 : {ring.cubes}")

            extras = ring.cubes[1:-1]
            BlockGraphConstructor.realise_edges(vzx, {
                (start, final): PathSpecification(
                    source_cube = next(iter(vzx.get_realising_cubes(start))),
                    target_cube = next(iter(vzx.get_realising_cubes(final))),
                    extras = extras,
                    pipes = [ pipes6[-1] if i == 0 else EdgeType.IDENTITY for i in range(nr)]
                )
            })

    console.info(f"Unrealised spiders    : {list(filter(lambda nd : not vzx.is_node_realised(nd) and vzx.is_spider(nd), vzx.nodes))}")
    console.info(f"Unrealised boundaries : {list(filter(lambda nd : not vzx.is_node_realised(nd) and vzx.is_boundary(nd), vzx.nodes))}")

    console.info(f"Realised nodes : {sum(1 for node in vzx.nodes if vzx.is_node_realised(node))} of {vzx.number_of_nodes()}")
    console.info(f"Overall volume : {vzx.number_of_cubes()}")
    viewer = VolumetricZxGraphViewer(vzx, label = circuit)
    viewer.display()