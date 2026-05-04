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

from qelebrimbor.common.components import ZxNode, BgCube
from qelebrimbor.common.coordinates import Coordinates


class SpacetimeFabric:
    def __init__(self):
        self.__occupied: dict[Coordinates, BgCube] = dict()
        self.__reservations: dict[Coordinates, BgCube] = dict()

    def available(self, position: Coordinates) -> bool:
        return position not in self.__occupied

    def claim(self, cube: BgCube):
        self.__occupied[cube.position] = cube

    def occupant(self, position: Coordinates):
        return self.__occupied[position]