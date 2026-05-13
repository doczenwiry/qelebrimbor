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

import logging

from qelebrimbor.core.components import BgCube
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import SpacetimeHelper

console = logging.getLogger(__name__)


class SpacetimeFabric:
    def __init__(self) -> None:
        self.__occupied_positions: dict[Coordinates, BgCube] = dict()

    def available(self, position: Coordinates) -> bool:
        return not self.occupied(position)

    def occupied(self, position: Coordinates) -> bool:
        return position in self.__occupied_positions

    def ports_offered(self, position: Coordinates, reach: Coordinates) -> int:
        return sum(1 for pos in SpacetimeHelper.get_constellation(position, reach) if self.available(pos))

    def occupy(self, cube: BgCube, position: Coordinates) -> bool:
        if position not in self.__occupied_positions:
            self.__occupied_positions[position] = cube
            return True
        else:
            console.error(f"Cube {cube} attempted to acquire occupied {position}.")
            return False

    def occupant(self, position: Coordinates):
        return self.__occupied_positions[position]
