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

type Port = Coordinates

class Vertex(RecordClass):
    cube: BgCube
    required: int
    available: set[Port]

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
        if cube in self.__open_ports:
            return str(self.__open_ports[cube])
        else:
            return "<not-tracked>"

    def required(self, cube: BgCube):
        return self.__open_ports[cube].required if cube in self.__open_ports else 0

    def available(self, cube: BgCube):
        return len(self.__open_ports[cube].available)

    def reachable(self, cube: BgCube):
        return self.__open_ports[cube].reachable

    def remaining(self, cube: BgCube):
        return self.__open_ports[cube].remaining

    def is_critical(self, holder: BgCube, position: Coordinates):
        return self.__open_ports[holder].remaining <= 1

    def connect_ports(self, source: tuple[BgCube, Port], target: tuple[BgCube, Port]):
        source_cube, source_port = source
        target_cube, target_port = target
        if source_port in self.__open_ports[source_cube].available:
            if self.__open_ports[source_cube].required > 1:
                self.__open_ports[source_cube].required -= 1
                self.__open_ports[source_cube].available.remove(source_port)
            else:
                for position in self.__open_ports[source_cube].available:
                    self.__spacetime.release(source_cube, position)
                self.__open_ports.pop(source_cube)
        else:
            console.error(f"Attempting to connect a port {source_port} not available to source {source_cube}")

        if target_port in self.__open_ports[target_cube].available:
            if self.__open_ports[target_cube].required > 1:
                self.__open_ports[target_cube].required -= 1
            else:
                for position in self.__open_ports[target_cube].available:
                    self.__spacetime.release(target_cube, position)
                self.__open_ports.pop(target_cube)
        else:
            console.error(f"Attempting to connect a port {target_port} not available to target {target_cube}")

    def reserve_ports(self, cube: BgCube):
        vertex = Vertex(cube = cube, required = self.__graph.get_zx_degree(cube.realised_node.id), available = set())
        constellation = SpacetimeHelper.get_constellation(cube.position, cube.kind.get_reach())
        for position in constellation:
            if self.__spacetime.reserve(cube, position):
                vertex.available.add(position)
            else:
                holder = self.__spacetime.holder(position) if self.__spacetime.is_reserved(position) else None
                occupant = self.__spacetime.occupant(position) if self.__spacetime.is_occupied(position) else None
                console.warning(f"Position {position} is not available in spacetime [requester={cube}, holder={holder}, occupant={occupant}]")

        self.__open_ports[cube] = vertex
        console.info(f"Reserved ports for {vertex}")

    def occlude_ports(self, position: Port):
        if self.__spacetime.is_reserved(position):
            holder = self.__spacetime.holder(position)
            self.__open_ports[holder].available.remove(position)
            self.__spacetime.close(position)

    def verify_ports(self):
        prioritized = 0
        unreachable = 0
        for vertex in self.__open_ports.values():
            console.debug(f"Verifying {vertex}")
            if vertex.remaining == 0:
                console.warning(f"Time to prioritize {vertex}")
                prioritized += 1
            elif vertex.remaining < 0:
                console.error(f"TOO LATE FOR {vertex}")
                unreachable += 1
        if prioritized == 0 == unreachable:
            console.info(f"All tracked cubes have enough ports.")