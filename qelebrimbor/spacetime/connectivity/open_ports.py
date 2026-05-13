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

from recordclass import RecordClass

from qelebrimbor.core.common import Port
from qelebrimbor.core.components import BgCube, ZxNode
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker

console = logging.getLogger(__name__)


class TrackingInformation(RecordClass):
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


class OpenPortsTracker(ConnectivityTracker):
    def __init__(self, graph: VolumetricZxGraph):
        self.__graph = graph
        self.__spacetime = graph.spacetime
        self.__reserved_ports: dict[BgCube, TrackingInformation] = dict()
        self.__ports_holders: dict[Port, BgCube] = dict()

    def preserved(self, start: BgCube, final: BgCube, position: Coordinates) -> bool:
        if position not in self.__ports_holders:
            return True

        holder = self.__ports_holders[position]
        return holder == start or holder == final or self.__reserved_ports[holder].remaining > 0

    def available(self, start: BgCube, final: BgCube) -> bool:
        if start not in self.__reserved_ports:
            console.warning(f"Impossible to infer connectability due to unknown status of {start}")

        if final not in self.__reserved_ports:
            console.warning(f"Impossible to infer connectability due to unknown status of {final}")

        return self.__reserved_ports[start].reachable and self.__reserved_ports[final].reachable

    def report(self, verbose: bool = False):
        prioritized = 0
        unreachable = 0
        if verbose:
            console.critical("Reporting on all tracked cubes.")
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

        if prioritized == 0:
            console.info("No tracked cubes requires to be prioritized.")

        if unreachable == 0:
            if verbose:
                console.critical("All tracked cubes have enough ports.")
            console.info("All tracked cubes have enough ports.")

    def reachable(self, cube: BgCube):
        raise NotImplementedError("Method reachable(..) has been deprecated. Use available(..) instead.")

    def reserve(self, cube: BgCube, required: int):
        vertex = TrackingInformation(required=required, available=set())

        for port in SpacetimeHelper.get_constellation(cube.position, cube.kind.get_reach()):
            if port not in self.__ports_holders and self.__spacetime.available(port):
                vertex.available.add(port)
                self.__ports_holders[port] = cube

        self.__reserved_ports[cube] = vertex
        console.debug(f"Reserved ports for {vertex}")

    def connect(self, source: tuple[BgCube, Port], target: tuple[BgCube, Port]):
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

    def occlude(self, *positions: Coordinates):
        for port in positions:
            if port not in self.__ports_holders:
                continue
            holder = self.__ports_holders[port]
            self.__reserved_ports[holder].available.remove(port)

    @staticmethod
    def get_nodes_with_insufficient_ports(graph: VolumetricZxGraph) -> list[ZxNode]:
        nodes_with_insufficient_ports = []
        for node in filter(ZxNode.is_realised, graph.get_zx_nodes()):
            edges_unrealised = sum(
                1
                for neighbor in graph.get_zx_neighbors(node)
                if not graph.get_zx_edge(node.id, neighbor.id).is_realised()
            )
            cube = node.realising_cube
            open_ports = sum(
                1
                for position in SpacetimeHelper.get_constellation(cube.position, cube.kind.get_reach())
                if not graph.spacetime.occupied(position)
            )
            if open_ports < edges_unrealised:
                nodes_with_insufficient_ports.append(node)
        return nodes_with_insufficient_ports
