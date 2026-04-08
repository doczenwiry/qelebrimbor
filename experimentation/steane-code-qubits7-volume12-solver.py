import json

import pyzx as zx
import numpy as np

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_zx import NodeId, NodeType, EdgeType
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.ringfinders.ringfinder_bfs import RingFinderBFS
from qelebrimbor.utilities.blockgraph_constructor import BlockGraphConstructor
from qelebrimbor.utilities.cycle_analyser import CycleAnalyser
from qelebrimbor.vedo.azg_viewer import AugmentedZxGraphViewer
from qelebrimbor.vedo.zx_layout.manual import ManualLayout

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("qelebrimbor").setLevel(logging.INFO)


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

    cycle0 = CycleAnalyser.decompose(azx)[0]
    n = len(cycle0)

    nodes0 = list(map(lambda nd : azx.get_node_type(nd), cycle0))
    ring0 = RingFinderBFS.find_minimal_rings(nodes0)[0]
    c = len(ring0.cubes)
    console.info(f"Cycle 0 [{c}]: {ring0.cubes}")
    console.info(f"> {nodes0}")

    BlockGraphConstructor.realise_nodes(azx, { cycle0[nd]: ring0.cubes[nd] for nd in range(n) })

    start = cycle0[0]
    final = cycle0[n-1]
    BlockGraphConstructor.realise_edges(azx,
        {
            (final, start): PathSpecification(
                source_cube = min(azx.get_realising_cubes(final)),
                target_cube = min(azx.get_realising_cubes(start)),
                extras = ring0.cubes[n:c],
                pipes = [ EdgeType.IDENTITY for _ in range(n) ]
            )
        }
    )

    hexagon = prepare_layout()
    viewer = AugmentedZxGraphViewer(azx, layout = hexagon)
    viewer.display()