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
from qelebrimbor.inflaters.equivolumetric_rings import Construction
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker
from qelebrimbor.spacetime.placefinders.breadth_first_search import PlacefinderBFS
from qelebrimbor.utilities.statistics import VolumetricZxGraphStatistics

console = logging.getLogger(__name__)


class ZxGraphInflaterEquivolumetricTrees:
    def __init__(self, graph: VolumetricZxGraph, verbose: bool = False):
        self.__graph = graph
        self.__connectivity = OpenPortsTracker(graph)
        self.__placefinder = PlacefinderBFS(graph, self.__connectivity)
        self.__verbose = verbose

    def process(self, constructions: list[Construction]):
        completed_constructions: list[Construction] = []
        for construction in constructions:
            graph, connectivity, _ = construction
            roots: set[ZxNode] = set()
            for node in graph.get_zx_nodes():
                if node.is_realised():
                    if any(not neighbor.is_realised() for neighbor in graph.get_zx_neighbors(node)):
                        roots.add(node)
            console.debug(f">> Roots identified : {roots}")
            trees: list[ZxTree] = list(map(lambda rt: ZxTree.extract(graph, rt), roots))
            maximal_height: int = max(tree.height for tree in trees)

            console.debug(f">> Trees identified : {len(trees)}")
            for tree in trees:
                console.debug(f">>> Tree [h={tree.height}] : {tree}")

            processed = 0
            for level in range(maximal_height):
                if self.__attempt_levels_realisation(graph, trees, level):
                    processed += 1

            if self.__verbose:
                console.debug(f">> Levels realised : {processed}/{maximal_height}")

            unrealised_nodes, unrealised_edges = VolumetricZxGraphStatistics.unrealised(graph)
            if unrealised_nodes == 0 or unrealised_edges == 0:
                completed_constructions.append(construction)

        return completed_constructions

    def __count_required_ports(self, graph: VolumetricZxGraph, node: ZxNode) -> int:
        return sum(
            1 for neighbor in graph.get_zx_neighbors(node) if not graph.get_zx_edge(node.id, neighbor.id).is_realised()
        )

    def __count_available_ports(self, graph: VolumetricZxGraph, node: ZxNode) -> int:
        count: int = 0
        if not node.is_realised():
            raise ValueError(f"count_available_ports : {node} is not realised.")
        console.debug(f">> count_available_ports : {node} [{node.realising_cube}]")
        for equivalent in graph.get_equivalent_bg_cubes(node.realising_cube):
            count += sum(
                1
                for port in SpacetimeHelper.get_constellation(equivalent.position, equivalent.kind.get_reach())
                if not graph.spacetime.occupied(port)
            )
        return count

    def __obtain_available_port(self, graph: VolumetricZxGraph, current: ZxNode) -> tuple[BgCube, Port] | None:
        cube = current.realising_cube
        console.debug(f">> Equivalents for node {current} : {graph.get_equivalent_bg_cubes(cube)}")
        candidates: list[tuple[BgCube, Port]] = []
        for equivalent in graph.get_equivalent_bg_cubes(cube):
            for port in SpacetimeHelper.get_constellation(equivalent.position, equivalent.kind.get_reach()):
                console.debug(f">>> Port {port} ? [{graph.spacetime.occupied(port)}]")
                if not graph.spacetime.occupied(port):
                    console.debug(f">>> Port found : {equivalent}-{port}.")
                    candidates.append((equivalent, port))
                else:
                    console.debug(f">>> Occupant : {graph.spacetime.occupant(port)}.")
        console.debug(f">>> Potential ports found : {candidates}")

        for equivalent, port in candidates:
            concerned_nodes = list(
                graph.spacetime.occupant(position).realised_node
                for position in SpacetimeHelper.get_constellation(port)
                if graph.spacetime.occupied(position)
                and graph.spacetime.occupant(position) != equivalent
                and graph.spacetime.occupant(position).kind.get_type() in [NodeType.X, NodeType.Z]
                and port in graph.spacetime.available_ports(position, graph.spacetime.occupant(position).kind.reach)
                and graph.spacetime.occupant(position).realised_node is not None
                and self.__count_required_ports(graph, graph.spacetime.occupant(position).realised_node)
                == self.__count_available_ports(graph, graph.spacetime.occupant(position).realised_node)
            )
            console.debug(f"> Concerned nodes for {equivalent}-{port} : {concerned_nodes}")
            if len(concerned_nodes) == 0:
                return equivalent, port

        return None

    def __attempt_levels_realisation(self, graph: VolumetricZxGraph, trees: list[ZxTree], level: int) -> bool:
        console.debug(f">> Attempting realisation of level [L={level}]")
        cube_id: CubeId
        available_port: tuple[BgCube, Port] | None
        nodes: list[tuple[ZxNode, ZxTree]] = list()
        for tree in trees:
            nodes.extend((node, tree) for node in tree.level(level))

        nodes = sorted(nodes, key=lambda entry: len(entry[1].following(entry[0])), reverse=True)
        console.debug(f">> Level {level} : {nodes}")

        for current_node, tree in nodes:
            console.debug(f">> Current [L:{level}] : {current_node}")
            if not current_node.is_realised():
                # Realise node based on preceding node's color and edge type to infer its CubeKind.
                preceding_node = tree.preceding(current_node)
                console.debug(f">> Current : {current_node} [preceding:{preceding_node}]")
                if not preceding_node.is_realised():
                    continue

                edge = graph.get_zx_edge(preceding_node.id, current_node.id)
                available_port = self.__obtain_available_port(graph, preceding_node)
                if available_port is not None:
                    preceding_cube, port = available_port
                    cube = BgCube(
                        kind=BlockGraphHelper.infer_cube_kind(preceding_cube, port, edge.type, current_node.type),
                        position=port,
                    )
                    cube_id = graph.realise_zx_node(current_node, cube=cube)
                    realising_cube = graph.get_bg_cube(cube_id)
                    graph.realise_zx_edge(
                        source=preceding_node.id,
                        target=current_node.id,
                        proposal=Path(start=preceding_cube).extend(cube=realising_cube, pipe_type=edge.type),
                    )
                else:
                    raise Exception(f"Realising cube of {preceding_node} has no ports available [src:si].")

            # Extend if the number of required ports is above the number of available ports.
            # TODO: check that a single cube suffices at this stage of the construction.
            required = self.__count_required_ports(graph, current_node)
            available = self.__count_available_ports(graph, current_node)
            console.debug(f">> Checking node {current_node} : {required} / {available} ")
            if required > available:
                available_port = self.__obtain_available_port(graph, current_node)
                console.debug(f">>> Node {current_node} has degree {current_node.degree}")
                if available_port is not None:
                    current_cube, port = available_port
                    cube = BgCube(kind=current_cube.kind, position=port)
                    cube_id = graph.extend_zx_node(current_node, cube=current_cube, extension=cube)
                else:
                    raise Exception(f"Realising cube of {current_node} has no ports available [ext:si].")

        return True
