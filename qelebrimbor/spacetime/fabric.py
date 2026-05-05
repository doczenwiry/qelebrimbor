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


import logging
console = logging.getLogger(__name__)

class SpacetimeFabric:
    def __init__(self):
        self.__occupied_positions: dict[Coordinates, BgCube] = dict()
        self.__reserved_positions: dict[Coordinates, BgCube] = dict()

    def available(self, position: Coordinates) -> bool:
        return not self.is_occupied(position) and not self.is_reserved(position)

    def is_occupied(self, position: Coordinates) -> bool:
        return position in self.__occupied_positions

    def is_reserved(self, position: Coordinates) -> bool:
        return position in self.__reserved_positions

    def reserve(self, cube: BgCube, position: Coordinates) -> bool:
        if position in self.__reserved_positions or position in self.__occupied_positions:
            return False

        self.__reserved_positions[position] = cube
        return True

    def release(self, cube: BgCube, position: Coordinates) -> bool:
        if position in self.__reserved_positions and self.__reserved_positions[position] == cube:
            self.__reserved_positions.pop(position)
            return True
        else:
            console.warning(f"Cube {cube} attempted to release a position it doesn't hold.")
            return False

    def close(self, position: Coordinates):
        if position not in self.__reserved_positions:
            raise Exception(f"Attempting to close a position which is not reserved.")

        if position in self.__occupied_positions:
            raise Exception(f"Attempting to close a position already occupied by {self.occupant(position)}.")

        self.__reserved_positions.pop(position)

    def claim(self, cube: BgCube):
        if cube.position in self.__reserved_positions:
            holder = self.__reserved_positions[cube.position]
            if holder != cube:
                console.warning(f"Cube {cube} claims a position reserved by {holder}.")
            self.__reserved_positions.pop(cube.position)

        if cube.position in self.__occupied_positions:
            holder = self.__occupied_positions[cube.position]
            if holder == cube:
                console.warning(f"Cube {cube} already occupies position {cube.position}.")
            else:
                raise Exception(f"Attempting to claim a position which is already occupied by {self.occupant(cube.position)}.")

        self.__occupied_positions[cube.position] = cube

    def holder(self, position: Coordinates):
        return self.__reserved_positions[position]

    def occupant(self, position: Coordinates):
        return self.__occupied_positions[position]