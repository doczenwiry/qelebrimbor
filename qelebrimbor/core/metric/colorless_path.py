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

from qelebrimbor.core.attributes_bg import CubeKind
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.metric.color_shufflings import ColorShuffling
from qelebrimbor.helpers.spacetime import SpacetimeHelper


class ColorlessPath:
    def __init__(self):
        self.__moves: list[Coordinates] = []
        self.__visited_positions: set[Coordinates] = set(SpacetimeHelper.ORIGIN)
        self.__shuffling: ColorShuffling = ColorShuffling.identity()

    def visits(self, position: Coordinates) -> bool:
        return position in self.__visited_positions

    def extend(self, step: Coordinates) -> ColorlessPath:
        if SpacetimeHelper.ORIGIN.get_manhattan_distance(step) != 1:
            raise ValueError(f"ColorlessPath requires unit steps in Spacetime.")

        position = self.__moves[-1] + step
        if position in self.__visited_positions:
            raise ValueError(f"ColorlessPath already visited {position}.")

        cp = ColorlessPath()
        cp.__moves.extend(self.__moves)
        cp.__visited_positions.update(self.__visited_positions)
        cp.__moves.append(step)
        cp.__visited_positions.add(position)
        cp.__shuffling = self.__shuffling.extend(ColorShuffling.convert(step))

        return cp

    def compatible(self, source_kind: CubeKind, target_kind: CubeKind) -> bool:
        return self.__shuffling.compatible(source_kind, target_kind)