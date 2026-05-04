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

from typing import Iterator

from recordclass import RecordClass

from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph


import logging
console = logging.getLogger(__name__)

class Vertex(RecordClass):
    cube: BgCube
    required: int
    available: set[Coordinates]

    @property
    def reachable(self):
        return self.remaining >= 0

    @property
    def remaining(self):
        return len(self.available) - self.required

    def __str__(self):
        return f"{self.cube} [rq:{self.required},av:{len(self.available)}]"

    def __repr__(self):
        return str(self)

class OpenPortsTracker:
    def __init__(self, graph: VolumetricZxGraph):
        self.__graph = graph
        self.__spacetime = graph.spacetime
        self.__open_ports: dict[BgCube, Vertex] = dict()

    def tracked_cubes(self) -> Iterator[BgCube]:
        return iter(self.__open_ports.keys())

    def report(self, cube: BgCube):
        return str(self.__open_ports[cube])

    def required(self, cube: BgCube):
        return self.__open_ports[cube].required

    def available(self, cube: BgCube):
        return len(self.__open_ports[cube].available)

    def reachable(self, cube: BgCube):
        return self.__open_ports[cube].reachable

    def remaining(self, cube: BgCube):
        return self.__open_ports[cube].remaining

    def close_ports(self, cube: BgCube, amount: int):
        self.__open_ports[cube].required -= amount

    def reserve_ports(self, cube: BgCube):
        vertex = Vertex(cube = cube, required = self.__graph.get_zx_degree(cube.realised_node.id), available = set())
        constellation = SpacetimeHelper.get_constellation(cube.position, cube.kind.get_reach())
        for position in constellation:
            if self.__spacetime.reserve(cube, position):
                vertex.available.add(position)
            else:
                console.warning(f"Position {position} is not available in spacetime [requester={cube}]")

        self.__open_ports[cube] = vertex

    def occlude_ports(self, position: Coordinates):
        if self.__spacetime.is_reserved(position):
            holder = self.__spacetime.holder(position)
            self.__open_ports[holder].available.remove(position)
            self.__spacetime.close(position)

    def verify_ports(self):
        for vertex in self.__open_ports.values():
            if vertex.remaining == 0:
                console.warning(f"Time to prioritize {vertex}")
            elif vertex.remaining < 0:
                console.error(f"TOO LATE FOR {vertex}")