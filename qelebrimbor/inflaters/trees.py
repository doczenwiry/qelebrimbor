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

from qelebrimbor.core.bg.attributes import CubeId
from qelebrimbor.core.bg.path import Path
from qelebrimbor.core.common import Port
from qelebrimbor.core.components import BgCube, ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import NodeType
from qelebrimbor.core.zx.tree import ZxTree
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker
from qelebrimbor.spacetime.placefinders.breadth_first_search import PlacefinderBFS

console = logging.getLogger(__name__)


class ZxGraphInflaterTrees:
    def __init__(self, graph: VolumetricZxGraph, verbose: bool = False):
        self.__graph = graph
        self.__connectivity = OpenPortsTracker(graph)
        self.__placefinder = PlacefinderBFS(graph, self.__connectivity)
        self.__verbose = verbose

    def process(self, abort_on_index: int = -1):
        roots: set[ZxNode] = set()
        for node in self.__graph.get_zx_nodes():
            if node.is_realised():
                if any(not neighbor.is_realised() for neighbor in self.__graph.get_zx_neighbors(node)):
                    roots.add(node)
        console.debug(f">> Roots identified : {roots}")
        trees: list[ZxTree] = list(map(lambda rt: ZxTree.extract(self.__graph, rt), roots))
        maximal_height: int = max(tree.height for tree in trees)

        console.debug(f">> Trees identified : {len(trees)}")
        for tree in trees:
            console.debug(f">>> Tree [h={tree.height}] : {tree}")

        processed = 0
        for level in range(maximal_height):
            if level == abort_on_index:
                break

            if not self.__attempt_levels_realisation(trees, level):
                break

            processed += 1

        if self.__verbose:
            print(f">> Levels realised : {processed}/{maximal_height}")

    def __count_cluster_required_ports(self, cube: BgCube) -> int:
        return sum(
            self.__connectivity.ports_required(equivalent) for equivalent in self.__graph.get_equivalent_bg_cubes(cube)
        )

    def __count_cluster_available_ports(self, cube: BgCube) -> int:
        return sum(
            self.__connectivity.ports_available(equivalent) for equivalent in self.__graph.get_equivalent_bg_cubes(cube)
        )

    def __count_required_ports(self, node: ZxNode) -> int:
        return sum(
            1
            for neighbor in self.__graph.get_zx_neighbors(node)
            if not self.__graph.get_zx_edge(node.id, neighbor.id).is_realised()
        )

    def __count_available_ports(self, node: ZxNode) -> int:
        count: int = 0
        for equivalent in self.__graph.get_equivalent_bg_cubes(node.realising_cube):
            count += sum(
                1
                for port in SpacetimeHelper.get_constellation(equivalent.position, equivalent.kind.get_reach())
                if not self.__graph.spacetime.occupied(port)
            )
        return count

    def __obtain_available_port(self, current: ZxNode) -> tuple[BgCube, Port] | None:
        cube = current.realising_cube
        console.debug(f">> Equivalents : {self.__graph.get_equivalent_bg_cubes(cube)}")
        for equivalent in self.__graph.get_equivalent_bg_cubes(cube):
            for port in SpacetimeHelper.get_constellation(equivalent.position, equivalent.kind.get_reach()):
                console.debug(f">>> Port {port} ? [{self.__graph.spacetime.occupied(port)}]")
                if not self.__graph.spacetime.occupied(port):
                    if not self.__connectivity.is_reserved(port) or self.__connectivity.holder(port) == equivalent:
                        console.debug(f">>> Port found : {equivalent}-{port}.")
                        return equivalent, port
                    else:
                        holder = self.__connectivity.holder(port)
                        if holder is not None:
                            ports_available = self.__count_cluster_available_ports(holder)
                            ports_required = self.__count_cluster_required_ports(holder)
                            if ports_available > ports_required:
                                return equivalent, port
                elif self.__graph.spacetime.occupied(port):
                    console.debug(f">>> Occupant : {self.__graph.spacetime.occupant(port)}.")
                elif self.__connectivity.is_reserved(port):
                    console.debug(f">>> Holder : {self.__connectivity.holder(port)}.")
        console.debug(">>> No port found.")
        return None

    def __attempt_levels_realisation(self, trees: list[ZxTree], level: int) -> bool:
        console.debug(f">> Attempting realisation of level [L={level}]")
        cube_id: CubeId
        available_port: tuple[BgCube, Port] | None
        # TODO: remove non-determinism by specifying the order of realisation in each level
        # - Spiders before boundaries ?
        # - Pure BFS or Mixed DFS ?
        level_nodes: list[tuple[ZxNode, ZxTree]] = list()
        for tree in trees:
            for current in tree.level(level):
                level_nodes.append((current, tree))
        level_nodes.sort(key=lambda entry: entry[0].type in {NodeType.X, NodeType.Z}, reverse=True)

        console.info(f">> Current [L:{level}] : {level_nodes}")
        if self.__verbose:
            only_nodes: list[ZxNode] = list(map(lambda entry: entry[0], level_nodes))
            print(f">> Attempting realisation of level {level} : {only_nodes}")

        for current, tree in level_nodes:
            if not current.is_realised():
                # Realise node based on preceding node's color and edge type to infer its CubeKind.
                preceding_node = tree.preceding(current)
                console.debug(f">> Current : {current} [preceding={preceding_node}]")
                if not preceding_node.is_realised():
                    continue

                edge = self.__graph.get_zx_edge(preceding_node.id, current.id)
                available_port = self.__obtain_available_port(preceding_node)
                console.debug(f">>> Available port : {available_port}")
                if available_port is not None:
                    preceding_cube, port = available_port
                    cube = BgCube(
                        kind=BlockGraphHelper.infer_cube_kind(preceding_cube, port, edge.type, current.type),
                        position=port,
                    )
                    cube_id = self.__graph.realise_zx_node(current, cube=cube)
                    realising_cube = self.__graph.get_bg_cube(cube_id)
                    self.__graph.realise_zx_edge(
                        source=preceding_node.id,
                        target=current.id,
                        proposal=Path(start=preceding_cube).extend(cube=realising_cube, pipe_type=edge.type),
                    )
                    if current.type in {NodeType.X, NodeType.Z}:
                        self.__connectivity.reserve(cube, self.__count_required_ports(current))
                else:
                    raise Exception(f"Realising cube of {preceding_node} has no ports available [src:si].")

            # Extend if the number of required ports is above the number of available ports.
            # TODO: check that a single cube suffices at this stage of the construction.
            required = self.__count_required_ports(current)
            available = self.__count_available_ports(current)
            console.debug(f">> Checking node {current} : {required} / {available} ")
            if required > available:
                available_port = self.__obtain_available_port(current)
                console.debug(f">>> Node {current} has degree {self.__graph.get_zx_degree(current.id)}")
                if available_port is not None:
                    current_cube, port = available_port
                    cube = BgCube(kind=current_cube.kind, position=port)
                    cube_id = self.__graph.extend_zx_node(current, cube=current_cube, extension=cube)
                else:
                    raise Exception(f"Realising cube of {current} has no ports available [ext:si].")

        return True
