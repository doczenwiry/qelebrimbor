import json

import pyzx as zx
import numpy as np

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_zx import NodeId, NodeType, EdgeType
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.cycle_analyser import CycleAnalyser
from qelebrimbor.vedo.azg_viewer import AugmentedZxGraphViewer
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
        neighbouring_boundaries = list(filter(lambda bd: azx.has_edge(nd, bd), azx.get_nodes(node_type=NodeType.O)))
        if len(neighbouring_boundaries) > 0:
            boundary = min(neighbouring_boundaries)
            bx = 1.4 * rho * np.cos(phi)
            by = 1.4 * rho * np.sin(phi)
            placements[boundary] = (bx, by)
        phi += step

    return ManualLayout(placements)

if __name__ == "__main__":
    pyzx_graph = zx.Graph()
    with open("../assets/zx/steane-code-qubits7-volume12.json", 'r') as file:
        pyzx_graph = pyzx_graph.from_json(json.load(file))

    azx = AugmentedZxGraph.from_pyzx_graph(pyzx_graph)

    CycleAnalyser.analyse(azx)

    cycles = CycleAnalyser.decompose(azx)
    cycle0 = cycles[0]
    n0 = len(cycle0)

    nodes0 = list(map(lambda nd : azx.get_node_type(nd), cycle0))
    console.info(f"Nodes 0 : {" ".join(map(lambda nd: str(nd) + ':' + str(azx.get_node_type(nd)), cycle0))}")

    ring0 = RingFinderBFS.find_minimal_rings(nodes0)[0]
    c0 = len(ring0.cubes)
    console.info(f"> Cycle 0 [{c0}]: {ring0.cubes}")

    BlockGraphConstructor.realise_nodes(azx, {cycle0[nd]: ring0.cubes[nd] for nd in range(n0)})

    start = cycle0[0]
    final = cycle0[n0 - 1]
    BlockGraphConstructor.realise_edges(azx,
        {
            (final, start): PathSpecification(
                source_cube = min(azx.get_realising_cubes(final)),
                target_cube = min(azx.get_realising_cubes(start)),
                extras = ring0.cubes[n0:c0],
                pipes = [EdgeType.IDENTITY for _ in range(n0)]
            )
        }
    )

    cycle1 = cycles[1]
    n1 = len(cycle1)
    nodes1 = list(map(lambda nd : azx.get_node_type(nd), cycle1))
    console.info(f"Nodes 1 : {" ".join(map(lambda nd: str(nd) + ':' + str(azx.get_node_type(nd)), cycle1))}")

    # Breakdown cycle1
    start = min(azx.get_realising_cubes(7))
    final = min(azx.get_realising_cubes(1))
    start_cube = (azx.get_cube_kind(start), azx.get_cube_position(start))
    final_cube = (azx.get_cube_kind(final), azx.get_cube_position(final))
    console.info(f"Searching completion from 7 #{start} [{start_cube}] to 1 #{final} [{final_cube}]")
    console.info(f"> Passing through : ")
    minimal_overhead, rings1 = PathFinderDFS.find_minimal_paths(
        final_cube, start_cube,
        type_restrictions = [ NodeType.X, NodeType.Z ],
        occupied_positions = azx.occupied,
        maximal_overhead = 6
    )

    ring1 = rings1[0]
    c1 = len(ring1.cubes)
    console.info(f"> Cycle 1 [{minimal_overhead}] : {ring1}")

    BlockGraphConstructor.realise_nodes(azx, {
        0 : ring1.cubes[1],
        4 : ring1.cubes[2]
    })

    BlockGraphConstructor.realise_edges(azx, {
        (1, 4): PathSpecification(
            source_cube = min(azx.get_realising_cubes(1)),
            target_cube = min(azx.get_realising_cubes(4)),
            extras = list(reversed(ring1.cubes[3:c1-1])),
            pipes = [EdgeType.IDENTITY for _ in range(n1)]
        )
    })

    hexagon = prepare_layout()
    viewer = AugmentedZxGraphViewer(azx, layout = hexagon)
    viewer.display()