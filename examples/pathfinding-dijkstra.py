from time import time

import qelebrimbor
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.components import BgCube
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.pathfinders.dijkstra import PathfinderDijkstra

import logging
console = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)

if __name__ == "__main__":
    source = BgCube(CubeKind.XZZ, SpacetimeHelper.ORIGIN)

    for distance in range(1, 10):
        target = BgCube(CubeKind.XZZ, distance * SpacetimeHelper.XP)
        console.info(f"Searching for path between {source} and {target} [distance={distance}].")
        start = time()
        paths = PathfinderDijkstra.find_optimal_paths(source, target)
        final = time()

        console.info(f"Found {len(paths)} paths in {round(final - start)} seconds.")