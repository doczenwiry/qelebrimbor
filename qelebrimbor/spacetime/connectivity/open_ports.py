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

from typing import Iterator, Iterable
from recordclass import RecordClass

from qelebrimbor.core.common import Port
from qelebrimbor.core.components import BgCube, ZxNode
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph


import logging
console = logging.getLogger(__name__)

class Vertex(RecordClass):
    required: int
    available: set[Port]

    @property
    def reachable(self):
        return self.remaining >= 0

    @property
    def remaining(self):
        return len(self.available) - self.required

    def __str__(self):
        return f"req:{self.required}, avl:{self.available}"

    def __repr__(self):
        return str(self)

class OpenPortsTracker:
    def __init__(self, graph: VolumetricZxGraph):
        self.__graph = graph
        self.__spacetime = graph.spacetime
        self.__reserved_ports: dict[BgCube, Vertex] = dict()
        self.__ports_holders: dict[Port, BgCube] = dict()

    def tracked_nodes(self) -> Iterator[BgCube]:
        return iter(self.__reserved_ports.keys())

    def report(self, cube: BgCube):
        if cube in self.__reserved_ports:
            return f"{cube} [{self.__reserved_ports[cube]}]"
        else:
            return "<not-tracked>"

    def required(self, cube: BgCube):
        return self.__reserved_ports[cube].required if cube in self.__reserved_ports else 0

    def reserved(self, cube: BgCube) -> Iterable[Port]:
        return iter(self.__reserved_ports[cube].available)

    def available(self, cube: BgCube):
        return len(self.__reserved_ports[cube].available)

    def reachable(self, cube: BgCube):
        return self.__reserved_ports[cube].reachable

    def remaining(self, cube: BgCube):
        return self.__reserved_ports[cube].remaining

    def is_reserved(self, port: Port) -> bool:
        return port in self.__ports_holders

    def holder(self, port: Port) -> BgCube:
        pass

    def is_critical(self, holder: BgCube, port: Port):
        return self.__reserved_ports[holder].remaining == 0

    def connect_ports(self, source: tuple[BgCube, Port], target: tuple[BgCube, Port]):
        source_cube, source_port = source
        target_cube, target_port = target
        if source_port in self.__reserved_ports[source_cube].available:
            if self.__reserved_ports[source_cube].required > 1:
                self.__reserved_ports[source_cube].required -= 1
                self.__reserved_ports[source_cube].available.remove(source_port)
            else:
                for port in self.__reserved_ports[source_cube].available:
                    self.__ports_holders.pop(port)
                self.__reserved_ports.pop(source_cube)
        else:
            console.warning(f"Attempting to connect a port {source_port} not available to source {source_cube}")

        if target_port in self.__reserved_ports[target_cube].available:
            if self.__reserved_ports[target_cube].required > 1:
                self.__reserved_ports[target_cube].required -= 1
            else:
                for port in self.__reserved_ports[target_cube].available:
                    self.__ports_holders.pop(port)
                self.__reserved_ports.pop(target_cube)
        else:
            console.warning(f"Attempting to connect a port {target_port} not available to target {target_cube}")

    def reserve_ports(self, cube: BgCube, required_ports: int):
        vertex = Vertex(required = required_ports, available = set())

        for position in SpacetimeHelper.get_constellation(cube.position, cube.kind.get_reach()):
            if position not in self.__ports_holders and self.__spacetime.available(position):
                vertex.available.add(position)

        self.__reserved_ports[cube] = vertex
        console.debug(f"Reserved ports for {vertex}")

    def occlude_ports(self, *ports: Coordinates):
        for holder, vertex in self.__reserved_ports.items():
            for port in ports:
                if port in vertex.available:
                   vertex.available.remove(port)

    def verify_ports(self, verbose: bool = False):
        prioritized = 0
        unreachable = 0
        if verbose:
            console.critical(f"Verifying all ports.")
        for holder, vertex in self.__reserved_ports.items():
            console.debug(f"Verifying {holder} [{vertex}]")
            if verbose:
                console.critical(f"Node {holder} [{vertex}]")
            if vertex.remaining == 0:
                console.debug(f"Time to prioritize {holder} [{vertex}]")
                prioritized += 1
            elif vertex.remaining < 0:
                console.error(f"TOO LATE FOR {holder} [{vertex}]")
                unreachable += 1
        if prioritized == 0 == unreachable:
            console.info(f"All tracked cubes have enough ports.")

    @staticmethod
    def get_nodes_with_insufficient_ports(graph: VolumetricZxGraph) -> list[ZxNode]:
        nodes_with_insufficient_ports = []
        for node in filter(ZxNode.is_realised, graph.get_zx_nodes()):
            edges_unrealised = sum(
                1 for neighbor in graph.get_zx_neighbors(node) if
                not graph.get_zx_edge(node.id, neighbor.id).is_realised()
            )
            cube = node.realising_cube
            open_ports = sum(
                1 for position in SpacetimeHelper.get_constellation(cube.position, cube.kind.get_reach())
                if not graph.spacetime.occupied(position)
            )
            if open_ports < edges_unrealised:
                nodes_with_insufficient_ports.append(node)
        return nodes_with_insufficient_ports