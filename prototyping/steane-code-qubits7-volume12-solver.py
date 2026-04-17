import json

import pyzx as zx
import numpy as np

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.components_zx import NodeId, NodeType, EdgeType
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
logging.getLogger("qelebrimbor.pathfinders").setLevel(logging.INFO)
logging.getLogger("qelebrimbor.augmented_zx_graph").setLevel(logging.DEBUG)


def prepare_layout() -> ManualLayout:
    placements: dict[NodeId, tuple[float, float]] = {}

    rho = 2.0
    phi = 0.0
    step = np.pi / 3.0
    placements[2]  = (0.0,  0.75)
    placements[9]  = (0.75,  0.5)
    placements[5]  = (0.0, -0.75)
    placements[12] = (-0.75, -0.5)
    for nd in [1,4,0,7,3,6]:
        x = rho * np.cos(phi)
        y = rho * np.sin(phi)
        placements[nd] = (x,y)
        neighbouring_boundaries = list(filter(lambda bd: vzx.has_edge(nd, bd), vzx.get_nodes(node_type=NodeType.O)))
        if len(neighbouring_boundaries) > 0:
            boundary = min(neighbouring_boundaries)
            bx = 1.4 * rho * np.cos(phi)
            by = 1.4 * rho * np.sin(phi)
            placements[boundary] = (bx, by)
        phi += step

    return ManualLayout(placements)

if __name__ == "__main__":
    pyzx_graph = zx.Graph()
    filename = "steane-code-qubits7-volume12.json"
    with open("../assets/pyzx/" + filename, 'r') as file:
        pyzx_graph = pyzx_graph.from_json(json.load(file))

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_graph)

    CycleBasisAnalyser.analyse(vzx)

    cycles = CycleBasisAnalyser.decompose(vzx)
    cycle0 = cycles[0]
    n0 = len(cycle0)

    nodes0 = list(map(lambda nd : vzx.get_node_type(nd), cycle0))
    console.info(f"Nodes 0 : {" ".join(map(lambda nd: str(nd) + ':' + str(vzx.get_node_type(nd)), cycle0))}")

    ring0 = RingFinderBFS.find_minimal_rings(nodes0)[0]
    c0 = len(ring0.cubes)
    console.info(f"> Cycle 0 [{c0}]: {ring0.cubes}")

    BlockGraphConstructor.realise_nodes(vzx, {cycle0[nd]: ring0.cubes[nd] for nd in range(n0)})

    start = cycle0[0]
    final = cycle0[n0 - 1]
    BlockGraphConstructor.realise_edges(vzx,
                                        {
            (final, start): PathSpecification(
                source_cube = vzx.get_realising_cube(final),
                target_cube = vzx.get_realising_cube(start),
                extras = ring0.cubes[n0:c0],
                pipes = [EdgeType.IDENTITY for _ in range(n0)]
            )
        }
                                        )

    cycle1 = cycles[1]
    n1 = len(cycle1)
    nodes1 = list(map(lambda nd : vzx.get_node_type(nd), cycle1))
    console.info(f"Nodes 1 : {" ".join(map(lambda nd: str(nd) + ':' + str(vzx.get_node_type(nd)), cycle1))}")

    # Breakdown cycle1
    start = vzx.get_realising_cube(7)
    final = vzx.get_realising_cube(1)
    start_cube = (vzx.get_cube_kind(start), vzx.get_cube_position(start))
    final_cube = (vzx.get_cube_kind(final), vzx.get_cube_position(final))
    console.info(f"Searching completion from 7 #{start} [{start_cube}] to 1 #{final} [{final_cube}]")
    console.info(f"> Passing through : ")
    minimal_overhead, rings1 = PathFinderDFS.find_minimal_paths(
        start = start_cube, final = final_cube,
        node_types= [NodeType.X, NodeType.Z],
        occupied_positions = vzx.occupied,
        maximal_overhead = 6
    )

    ring1 = rings1[0]
    c1 = len(ring1.cubes)
    console.info(f"> Cycle 1 [{minimal_overhead}] : {ring1}")

    BlockGraphConstructor.realise_nodes(vzx, {
        0 : ring1.cubes[1],
        4 : ring1.cubes[2]
    })

    BlockGraphConstructor.realise_edges(vzx, {
        (1, 4): PathSpecification(
            source_cube = vzx.get_realising_cube(1),
            target_cube = vzx.get_realising_cube(4),
            extras = list(reversed(ring1.cubes[3:c1-1])),
            pipes = [EdgeType.IDENTITY for _ in range(n1)]
        )
    })

    console.info(f"TOTAL VOLUME : {vzx.number_of_cubes()}")

    hexagon = prepare_layout()
    viewer = VolumetricZxGraphViewer(vzx, label = filename, layout = hexagon)
    viewer.display()