import json

import pyzx as zx
import numpy as np

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeId, NodeType, EdgeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.manual import ManualLayout

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("qelebrimbor").setLevel(logging.CRITICAL)
logging.getLogger("qelebrimbor.augmented_zx_graph").setLevel(logging.DEBUG)


def prepare_layout() -> ManualLayout:
    placements: dict[NodeId, tuple[float, float]] = {}

    rho = 2.0
    phi = 0.0
    step = np.pi / 3.0
    placements[1] = (0.0, 0.0)
    placements[7] = (0.7 * np.cos(step), 0.7 * np.sin(step))
    for node in [0,2,4,5,6,3]:
        x = rho * np.cos(phi)
        y = rho * np.sin(phi)
        placements[node] = (x,y)
        boundary = min(
            map(lambda bd: bd.id,
                filter(lambda bd: vzx.has_edge(node, bd.id), vzx.get_zx_nodes(node_type=NodeType.O)))
        )
        bx = 1.4 * rho * np.cos(phi)
        by = 1.4 * rho * np.sin(phi)
        placements[boundary] = (bx, by)
        phi += step

    return ManualLayout(placements)

if __name__ == "__main__":
    pyzx_graph = zx.Graph()
    with open("../assets/pyzx/steane-code-qubits7-volume14.json", 'r') as file:
        pyzx_graph = pyzx_graph.from_json(json.load(file))

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_graph)
    vzx.log_summary()

    CycleBasisAnalyser.analyse(vzx)

    cycles = CycleBasisAnalyser.decompose(vzx)
    cycle0 = cycles[0]
    n0 = len(cycle0)

    nodes0 = list(map(lambda nd : vzx.get_zx_node(nd).type, cycle0))
    console.info(f"Nodes 0 : {" ".join(map(lambda nd: str(nd) + ':' + str(vzx.get_zx_node(nd).type), cycle0))}")

    ring0 = RingFinderBFS.find_minimal_rings(nodes0, maximal_overhead = 4)[0]
    c0 = len(ring0.cubes)
    console.info(f"> Cycle 0 [{c0}]: {ring0.cubes}")

    BlockGraphConstructor.realise_nodes(vzx, {cycle0[nd]: ring0.cubes[nd] for nd in range(n0)})

    start = cycle0[0]
    final = cycle0[n0 - 1]
    BlockGraphConstructor.realise_edges(vzx,
                                        {
            (final, start): PathSpecification(
                source_cube = vzx.get_zx_node(final).realising_cube,
                target_cube = vzx.get_zx_node(start).realising_cube,
                extras = ring0.cubes[n0:c0],
                pipes = [EdgeType.IDENTITY for _ in range(n0)]
            )
        }
                                        )

    cycle1 = cycles[1]
    n1 = len(cycle1)
    nodes1 = list(map(lambda nd : vzx.get_zx_node(nd).type, cycle1))
    console.info(f"Nodes 1 : {" ".join(map(lambda nd: str(nd) + ':' + str(vzx.get_zx_node(nd).type), cycle1))}")

    cycle2 = cycles[2]
    n2 = len(cycle2)
    nodes2 = list(map(lambda nd : vzx.get_zx_node(nd).type, cycle2))
    console.info(f"Nodes 2 : {" ".join(map(lambda nd: str(nd) + ':' + str(vzx.get_zx_node(nd).type), cycle2))}")

    BlockGraphConstructor.realise_nodes(vzx, {
        1 : (CubeKind.ZZX, Coordinates(1,2,1))
    })

    BlockGraphConstructor.realise_edges(vzx, {})

    # Breakdown cycle1
    start = vzx.get_zx_node(1).realising_cube
    final = vzx.get_zx_node(6).realising_cube
    start_cube = (vzx.get_bg_cube(start).kind, vzx.get_bg_cube(start).position)
    final_cube = (vzx.get_bg_cube(final).kind, vzx.get_bg_cube(final).position)
    console.info(f"Searching completion from 1 #{start} [{start_cube}] to 6 #{final} [{final_cube}]")
    console.info(f"> Passing through : []")
    minimal_overhead, completions1 = PathFinderDFS.find_minimal_paths(
        final = final_cube, start = start_cube,
        occupied_positions = vzx.occupied,
        maximal_overhead = 6
    )

    completion1 = completions1[0]
    c1 = len(completion1.cubes)
    console.info(f"> Completion 1 [{c1}] : {completion1}")

    BlockGraphConstructor.realise_edges(vzx, {
        (1, 6): PathSpecification(
            source_cube = vzx.get_zx_node(1).realising_cube,
            target_cube = vzx.get_zx_node(6).realising_cube,
            extras = completion1.cubes[1:c1 - 1],
            pipes = [EdgeType.IDENTITY for _ in range(n1)]
        )
    })

    # Breakdown cycle2 [all finals]
    # for final_cube_index in range(len(azx.get_realising_cubes(1))):
    #     start = min(azx.get_realising_cubes(0))
    #     final = list(azx.get_realising_cubes(1))[final_cube_index]
    #     start_cube = (azx.get_bg_cube(start).kind, azx.get_bg_cube(start).position)
    #     final_cube = (azx.get_bg_cube(final).kind, azx.get_bg_cube(final).position)
    #     console.info(f"Searching completion from 0 #{start} [{start_cube}] to 1 #{final} [{final_cube}]")
    #     minimal_overhead, completions2 = PathFinderDFS.find_minimal_paths(
    #         final_cube, start_cube,
    #         occupied_positions = azx.occupied,
    #         maximal_overhead = 6
    #     )
    #
    #     if len(completions2) > 0:
    #         completion2 = completions2[0]
    #         c2 = len(completion2.cubes)
    #         console.info(f"> Completion 2 [{c2}] : {completion2}")
    #     else:
    #         console.info(f"> Completion 2 [inf] : n/a")

    final_cube_idx = 3
    start = vzx.get_zx_node(0).realising_cube
    final = vzx.get_zx_node(1).realising_cube
    start_cube = (vzx.get_bg_cube(start).kind, vzx.get_bg_cube(start).position)
    final_cube = (vzx.get_bg_cube(final).kind, vzx.get_bg_cube(final).position)
    console.info(f"Searching completion from 0 #{start} [{start_cube}] to 1 #{final} [{final_cube}]")
    minimal_overhead, completions2 = PathFinderDFS.find_minimal_paths(
        final = final_cube, start = start_cube,
        occupied_positions = vzx.occupied,
        maximal_overhead = 6
    )

    completion2 = completions2[0]
    c2 = len(completion2.cubes)
    console.info(f"> Completion 2 [{c2}] : {completion2}")

    BlockGraphConstructor.realise_edges(vzx, {
        (0, 1): PathSpecification(
            source_cube = vzx.get_zx_node(0).realising_cube,
            target_cube = vzx.get_zx_node(1).realising_cube,
            extras = completion2.cubes[1:c2 - 1],
            pipes = [EdgeType.IDENTITY for _ in range(n2+2)]
        )
    })

    console.info(f"TOTAL VOLUME : {vzx.number_of_cubes()}")

    hexagon = prepare_layout()
    viewer = VolumetricZxGraphViewer(vzx, label ="steane-code", layout = hexagon)
    viewer.display()