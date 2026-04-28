import qelebrimbor
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.components import BgCube
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.pathfinders.dijkstra import PathfinderDijkstra

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level = logging.DEBUG)

if __name__ == "__main__":
    source = BgCube(CubeKind.XZZ, SpacetimeHelper.ORIGIN)
    target = BgCube(CubeKind.XZZ, SpacetimeHelper.XP)
    paths = PathfinderDijkstra.find_optimal_paths(source, target)

    console.info(f"Found {len(paths)} paths.")
    for path in paths:
        console.info(f"> {path}")