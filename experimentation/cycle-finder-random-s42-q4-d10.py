import random
import pyzx

import qelebrimbor
from qelebrimbor.common.components_zx import EdgeType, NodeType
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.utilities.cycle_analyser import CycleAnalyser

SEED = 42
QUBITS = 4
LAYERS = 10

import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)
logging.getLogger('qelebrimbor.volumetric_zx_graph').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.pathfinders.pathfinder_dfs').setLevel(logging.CRITICAL)
logging.getLogger('qelebrimbor.ringfinders.ringfinder_bfs').setLevel(logging.CRITICAL)

random.seed(SEED)
if __name__ == "__main__":
    circuit = f"random-s{SEED}-q{QUBITS}-d{LAYERS}-full-reduced"
    zx = pyzx.generate.cnots(qubits = QUBITS, depth = LAYERS)
    pyzx.full_reduce(zx)
    # pyzx.draw(zx, labels = True)

    with open(f"../assets/pyzx/{circuit}.json", 'w') as file:
        file.write(zx.to_json())

    vzx = VolumetricZxGraph.from_pyzx_graph(zx)

    CycleAnalyser.analyse(vzx)

    cycles = CycleAnalyser.decompose(vzx)
    cycle0 = cycles[0]
    edges0 = [ (cycle0[i], cycle0[(i+1) % len(cycle0)]) for i in range(len(cycle0)) ]
    n0 = len(cycle0)

    nodes0 = list(map(lambda nd : vzx.get_node_type(nd), cycle0))
    pipes0 = list(map(lambda ed : vzx.get_edge_type(*ed), edges0))
    console.info(f"Nodes 0 : {" ".join(map(lambda nd: str(nd) + ':' + str(vzx.get_node_type(nd)), cycle0))}")
    console.info(f"Edges 0 : {" ".join(map(lambda ed: str(vzx.get_edge_type(*ed))[0] + str(ed).replace(' ',''), edges0))}")

    cycle1 = cycles[1]
    n1 = len(cycle1)
    nodes1 = list(map(lambda nd: vzx.get_node_type(nd), cycle1))
    console.info(f"Nodes 1 : {" ".join(map(lambda nd: str(nd) + ':' + str(vzx.get_node_type(nd)), cycle1))}")

    rings0 = RingFinderBFS.find_minimal_rings(nodes0, pipes0, number_sought = -1, maximal_overhead = 6)
    console.info(f"Found {len(rings0)} realisations for ring {cycle0}")
    min_volume_found = 30
    for ring0 in rings0:
        console.info(f"> Realisation [{len(ring0.cubes)}] : {ring0}")
        solution = VolumetricZxGraph.from_pyzx_graph(zx)
        BlockGraphConstructor.realise_nodes(solution, {cycle0[nd]: ring0.cubes[nd] for nd in range(n0)})

        cycle0 = cycles[0]
        start = cycle0[0]
        final = cycle0[n0 - 1]
        c0 = len(ring0.cubes)
        BlockGraphConstructor.realise_edges(solution,
            specifications = {
                (start, final): PathSpecification(
                    source_cube = min(solution.get_realising_cubes(start)),
                    target_cube = min(solution.get_realising_cubes(final)),
                    extras = list(reversed(ring0.cubes[n0:c0])),
                    pipes = [ EdgeType.IDENTITY if i != c0-1 else EdgeType.HADAMARD for i in range(c0) ]
                )
            }
        )

        # Breakdown cycle1
        start = min(solution.get_realising_cubes(4))
        final = min(solution.get_realising_cubes(9))
        start_cube = (solution.get_cube_kind(start), solution.get_cube_position(start))
        final_cube = (solution.get_cube_kind(final), solution.get_cube_position(final))
        minimal_overhead, paths1 = PathFinderDFS.find_minimal_paths(
            start = start_cube, final = final_cube,
            node_types = [ NodeType.Z, NodeType.Z ],
            edge_types = [ EdgeType.HADAMARD, EdgeType.HADAMARD, EdgeType.HADAMARD ],
            occupied_positions = solution.occupied,
            maximal_overhead = 6
        )
        console.info(f">> Completion volume {len(paths1[0].cubes) - 2} from 4 #{start} [{start_cube}] to 9 #{final} [{final_cube}]")
        new_volume = len(ring0.cubes) + len(paths1[0].cubes) - 2
        if new_volume < min_volume_found:
            min_volume_found = new_volume

    console.info(f"Minimal volume found : {min_volume_found}")

    # ring0 = rings0[0]
    # c0 = len(ring0.cubes)
    # console.info(f"> Cycle 0 [{c0}]: {ring0.cubes}")
    #
    # BlockGraphConstructor.realise_nodes(vzx, {cycle0[nd]: ring0.cubes[nd] for nd in range(n0)})
    #
    # start = cycle0[0]
    # final = cycle0[n0 - 1]
    # BlockGraphConstructor.realise_edges(vzx,
    #     specifications = {
    #         (start, final): PathSpecification(
    #             source_cube = min(vzx.get_realising_cubes(start)),
    #             target_cube = min(vzx.get_realising_cubes(final)),
    #             extras = list(reversed(ring0.cubes[n0:c0])),
    #             pipes = [ EdgeType.IDENTITY if i != c0-1 else EdgeType.HADAMARD for i in range(c0) ]
    #         )
    #     }
    # )
    #
    # cycle1 = cycles[1]
    # n1 = len(cycle1)
    # nodes1 = list(map(lambda nd : vzx.get_node_type(nd), cycle1))
    # console.info(f"Nodes 1 : {" ".join(map(lambda nd: str(nd) + ':' + str(vzx.get_node_type(nd)), cycle1))}")
    #
    # # Breakdown cycle1
    # start = min(vzx.get_realising_cubes(4))
    # final = min(vzx.get_realising_cubes(9))
    # start_cube = (vzx.get_cube_kind(start), vzx.get_cube_position(start))
    # final_cube = (vzx.get_cube_kind(final), vzx.get_cube_position(final))
    # console.info(f"Searching completion from 4 #{start} [{start_cube}] to 9 #{final} [{final_cube}]")
    # minimal_overhead, rings1 = PathFinderDFS.find_minimal_paths(
    #     start = start_cube, final = final_cube,
    #     node_types = [ NodeType.Z, NodeType.Z ],
    #     edge_types = [ EdgeType.HADAMARD, EdgeType.HADAMARD, EdgeType.HADAMARD ],
    #     occupied_positions = vzx.occupied,
    #     maximal_overhead = 6
    # )
    #
    # ring1 = rings1[0]
    # c1 = len(ring1.cubes)
    # console.info(f"> Cycle 1 [+{minimal_overhead}] : {ring1}")
    #
    # BlockGraphConstructor.realise_nodes(vzx, {
    #     8 : ring1.cubes[1],
    #     5 : ring1.cubes[2]
    # })
    #
    # BlockGraphConstructor.realise_edges(vzx, {
    #     (5, 9): PathSpecification(
    #         source_cube = min(vzx.get_realising_cubes(5)),
    #         target_cube = min(vzx.get_realising_cubes(9)),
    #         extras = ring1.cubes[3:c1-1],
    #         pipes = [EdgeType.HADAMARD if i == 0 else EdgeType.IDENTITY for i in range(n1)]
    #     )
    # })
    #
    # console.info(f"TOTAL VOLUME : {vzx.number_of_cubes()}")
    #
    # viewer = VolumetricZxGraphViewer(vzx, label = circuit)
    # viewer.display()