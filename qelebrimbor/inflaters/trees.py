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

from qelebrimbor.core.components import ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker
from qelebrimbor.spacetime.placefinders.breadth_first_search import PlacefinderBFS

console = logging.getLogger(__name__)


class ZxGraphInflaterTrees:
    def __init__(self, graph: VolumetricZxGraph, iterative: bool = False):
        self.__graph = graph
        self.__connectivity = OpenPortsTracker(graph)
        self.__placefinder = PlacefinderBFS(graph, self.__connectivity)
        self.__iterative_processing = iterative

    def process(self, abort_on_failure: bool = False, abort_on_index: int = -1):
        roots: set[ZxNode] = set()
        for node in self.__graph.get_zx_nodes():
            if node.is_realised():
                if any(not node.is_realised() for node in self.__graph.get_zx_neighbors(node)):
                    roots.add(node)
        print(f">> Roots identified : {roots}")

    # def __find_root_cube(self, root_node: ZxNode) -> BgCube | None:
    #     start = SpacetimeHelper.ORIGIN
    #     required_ports = self.__graph.get_zx_degree(root_node.id)
    #
    #     queue: deque[Coordinates] = deque([start])
    #     placement: tuple[Coordinates, Coordinates] | None = None
    #
    #     visited: set[Coordinates] = set()
    #     while len(queue) > 0 and placement is None:
    #         candidate: Coordinates = queue.popleft()
    #
    #         console.debug(f"Root position candidate for {root_node} : {candidate}
    #         [avl:{self.__spacetime.available(candidate)},visited:{candidate in visited}]")
    #
    #         if candidate in visited:
    #             continue
    #         visited.add(candidate)
    #
    #         for neighbor in SpacetimeHelper.get_constellation(candidate):
    #             queue.append(neighbor)
    #
    #         if not self.__graph.spacetime.available(candidate):
    #             continue
    #
    #         # if candidate position offers a reach with enough open ports, assign it to placement
    #         for reach in SpacetimeHelper.PLANES:
    #             count_available_ports: int = sum(
    #                 1 for pos in SpacetimeHelper.get_constellation(candidate, reach)
    #                 if self.__graph.spacetime.available(pos)
    #             )
    #             if count_available_ports >= required_ports:
    #                 placement = candidate, reach
    #                 break
    #
    #
    #     if placement:
    #         root_position, root_reach = placement
    #         return BgCube(kind = CubeKind.convert(root_node.type, root_reach), position = root_position)
    #     else:
    #         console.error(f"> Failed to find placement for root {root_node}")
    #         return None

    # def __process_component(self, root_node: ZxNode) -> bool:
    #     console.info(f"Starting inflation from root {root_node} [{root_node.realising_cube}]")
    #
    #     unrealised: list[tuple[int, ZxNode]] = [
    #         (self.__connectivity.remaining(root_node.realising_cube), root_node)
    #     ]
    #
    #     while len(unrealised) > 0:
    #         heapq.heapify(unrealised)
    #         remaining, source = heapq.heappop(unrealised)
    #
    #         if not source.is_realised():
    #             console.info(f"> FAILURE to find placement from {source} to any target [cause:unrealised-source]")
    #             return False
    #
    #         for target in self.__graph.get_zx_neighbors(source):
    #             if target.is_realised():
    #                 continue
    #
    #             cause = None
    #             if self.__connectivity.reachable(source.realising_cube):
    #                 if not self.__attempt_node_realisation(source, target):
    #                     cause = "pathfinder-none"
    #             else:
    #                 cause = "insufficient-ports"
    #
    #             if cause is not None:
    #                 console.info(f"> FAILURE to find placement from {source} to {target} [cause:{cause}]")
    #                 return False
    #
    #             if self.__connectivity.required(target.realising_cube) > 0:
    #                 unrealised.append((self.__connectivity.remaining(target.realising_cube), target))
    #
    #     return True
    #
    # def __attempt_node_realisation(self, realised: ZxNode, unrealised: ZxNode) -> bool:
    #     # Place a cube of a kind suitable for the type of the unrealised endpoint node can be placed.
    #     console.info(f"> Searching for node placement from {realised} for {unrealised}")
    #     console.debug(f">> Source ports : {self.__connectivity.report(realised.realising_cube)}")
    #
    #     placement: Path | None = self.__placefinder.find_closest_realisation(realised.realising_cube, unrealised)
    #     if placement is None:
    #         return False
    #     console.info(f">> Optimal placement found : {placement}")
    #
    #     # Realise the target cube and the path connecting it to the source cube
    #     self.__graph.realise_zx_node(unrealised, placement.final)
    #     self.__graph.realise_zx_edge(realised.id, unrealised.id, proposal = placement)
    #
    #     self.__connectivity.reserve_ports(placement.final)
    #
    #     # Remove the reserved positions of ports from those available ones
    #     for position in placement.extra_cubes:
    #         self.__connectivity.occlude_ports(position)
    #     self.__connectivity.occlude_ports(placement.final.position)
    #
    #     self.__connectivity.connect_ports(
    #         source = (realised.realising_cube, placement.start_port),
    #         target = (placement.final, placement.final_port)
    #     )
    #     self.__connectivity.verify_ports()
    #
    #     return True
