#   Copyright 2026 Seweryn Dynerowicz
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from logging import getLogger

from qelebrimbor.common.components import BgCube

console = getLogger(__name__)

from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS

class VolumeFinder:
    @staticmethod
    def get_path_overhead(source: BgCube, target: BgCube):
        discovered_paths = PathFinderDFS.find_minimal_paths(start = source, final = target, maximal_overhead= 12)
        manhattan_distance = SpacetimeHelper.ORIGIN.get_manhattan_distance(target.position)
        differential = discovered_paths[0].manhattan_length() - manhattan_distance

        return differential