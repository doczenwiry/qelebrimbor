from time import time

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.pathfinders.dijkstra import PathfinderDijkstra
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.pathfinders.depth_first_search import PathfinderDFS

from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.planar import PlanarLayout

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)
logging.getLogger("qelebrimbor.volumetric_zx_graph").setLevel(logging.CRITICAL)
logging.getLogger("qelebrimbor.helpers.blockgraph").setLevel(logging.CRITICAL)
logging.getLogger("qelebrimbor.pathfinders.depth_first_search").setLevel(logging.INFO)
logging.getLogger("qelebrimbor.vedo").setLevel(logging.CRITICAL)

PATHFINDER_UNDER_TEST = PathfinderDFS
DISTANCES = {
    PathfinderDFS : [1, 5, 10, 25, 50, 100, 200],
    PathfinderDijkstra : [1, ..., 6],
}

VISUALISATION = False

if __name__ == "__main__":
    pathfinder = PATHFINDER_UNDER_TEST
    distances = DISTANCES[pathfinder]

    for distance in distances:
        # Prepare input VZX graph
        vzx = VolumetricZxGraph(
            nodes = [ (0, NodeType.X) , (1, NodeType.X) ],
            edges = [ (0, 1, EdgeType.IDENTITY) ]
        )
        source = vzx.get_zx_node(0)
        target = vzx.get_zx_node(1)
        source_cube = vzx.get_bg_cube(vzx.realise_zx_node(source, BgCube(CubeKind.XZZ, SpacetimeHelper.ORIGIN)))
        target_cube = vzx.get_bg_cube(vzx.realise_zx_node(target, BgCube(CubeKind.XZZ, distance * SpacetimeHelper.XP)))

        console.info(f"Searching for path between {source} and {target} [distance={distance}].")
        start = time()
        path = pathfinder.find_optimal_paths(source_cube, target_cube)
        final = time()

        if path is None:
            console.error(f"Failed to find a path [runtime={round(final - start)}s].\n")
            continue

        console.info(f"Found a locally-optimal path [runtime={round(final - start)}s].")
        console.info(f"> {path} [length={path.manhattan_length()}]\n")

        proposal = PathSpecification(
            source_cube, target_cube,
            extras = path.extras, pipes = [ EdgeType.IDENTITY for _ in range(path.manhattan_length()) ]
        )
        vzx.realise_zx_edge(0, 1, proposal)

        if VISUALISATION:
            viewer = VolumetricZxGraphViewer(vzx, label = f"distance={distance}", layout = PlanarLayout(vzx, scale = 1))
            viewer.display()