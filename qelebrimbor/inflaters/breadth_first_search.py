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

from collections import defaultdict
from typing import cast

import networkx as nx

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.components import ZxNode, BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.spacetime.placefinders.breadth_first_search import PlacementFinderBFS
from qelebrimbor.spacetime.pathfinders.depth_first_search import PathfinderDFS
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger("qelebrimbor.main")

class ZxGraphInflaterBFS:
    def __init__(self, graph: VolumetricZxGraph):
        self.__graph = graph
        self.__node_realisations = 0
        self.__edge_realisations = 0

        self.__reservations: dict[Coordinates, ZxNode] = dict()
        self.__available_ports: dict[ZxNode, list[Coordinates]] = defaultdict(list)

        self.__required_ports: dict[ZxNode, int] = dict()
        for node in graph.get_zx_nodes():
            self.__required_ports[node] = graph.get_zx_degree(node.id)

    def __occlude_positions(self, position: Coordinates):
        if position in self.__reservations:
            holder = self.__reservations[position]
            self.__available_ports[holder].remove(position)
            self.__reservations.pop(position)
            if self.__required_ports[holder] == len(self.__available_ports[holder]):
                console.warning(f"> Time to prioritize holder {holder} [{self.__required_ports[holder]}/{self.__available_ports[holder]}]")

    def __reserve_positions(self, node: ZxNode):
        cube = node.realising_cube
        for position in SpacetimeHelper.get_constellation(cube.position, cube.kind.get_reach()):
            if position in self.__reservations:
                console.warning(f"Position {position} already reserved by {self.__reservations[position]} [requester={cube}]")
                continue
            if position not in self.__graph.occupied:
                self.__reservations[position] = node
                self.__available_ports[node].append(position)
            if self.__required_ports[node] == len(self.__available_ports[node]):
                console.warning(f"> Time to prioritize node {node} [{self.__required_ports[node]}/{self.__available_ports[node]}]")

    # TODO: detects whether the source and/or target are unreachable in the BlockGraph.
    # TODO: > represent the spacetime available and pathfind to the border of the blockgraph ?
    # TODO: > reserve needed positions for connection ?

    def process(self, root: tuple[ZxNode, CubeKind] | None = None):
        console.info(f"Starting inflation from root {root}")

        if root:
            root_node, root_kind = root
        else:
            root_node = max(self.__graph.get_zx_nodes(), key=lambda zxn: self.__graph.get_zx_degree(zxn.id))
            root_kind = CubeKind.suitable_kinds(root_node.type)[0]

        # Realise the root of the construction.
        root_cube = BgCube(
            kind = root_kind,
            position = SpacetimeHelper.ORIGIN
        )
        self.__graph.realise_zx_node(root_node, root_cube)
        self.__reserve_positions(root_node)

        # Form the backbone with the bfs_edges
        # > Reserve needed positions based on remaining missing neighbors
        # Then complete with the unrealised edges from edge_bfs
        # > Perform realisations in order of decreasing Manhattan Distance between the endpoint cubes

        # Perform a pass of node-realisations (a.k.a. first-pass edges)
        for edge in nx.bfs_edges(cast(nx.Graph, self.__graph), root_node.id):
            zx_edge = self.__graph.get_zx_edge(*edge)

            if zx_edge.is_realised():
                console.warning(f"> Second attempt to realise edge : {edge}")
                continue

            source, target = (zx_edge.source, zx_edge.target) if zx_edge.source.is_realised() else (zx_edge.target, zx_edge.source)

            if source.is_realised() or target.is_realised():
                if len(self.__available_ports[source]) < self.__required_ports[source]:
                    raise Exception(f"> FAILURE to realise SP edge : {edge} [cause:insufficient-ports]")

                success = self.__attempt_node_realisation(source, target)

                if not success:
                    raise Exception(f"> FAILURE to realise FP edge : {edge} [cause:pathfinder]")

                self.__required_ports[source] -= 1
                self.__required_ports[target] -= 1

                self.__node_realisations += 1

            else:
                raise Exception(f"> FAILURE to realise FP edge : {edge} [cause:unrealised-endpoints]")

        # Perform a pass of edge-realisations (a.k.a. cross edges)
        unrealised_edges = filter(
            lambda edge: not self.__graph.get_zx_edge(*edge).is_realised(),
            nx.edge_bfs(self.__graph, root.id)
        )

        for edge in unrealised_edges:
            zx_edge = self.__graph.get_zx_edge(*edge)

            if zx_edge.is_realised():
                console.warning(f"> Second attempt to realise edge : {edge}")
                continue

            source, target = (zx_edge.source, zx_edge.target) if zx_edge.source.is_realised() else (zx_edge.target, zx_edge.source)

            if source.is_realised() and target.is_realised():
                if len(self.__available_ports[source]) < self.__required_ports[source] and len(self.__available_ports[target]) < self.__required_ports[target]:
                    raise Exception(f"> FAILURE to realise SP edge : {edge} [cause:insufficient-ports]")

                success = self.__attempt_edge_realisation(source, target)
                if not success:
                    raise Exception(f"> FAILURE to realise SP edge : {edge} [cause:pathfinder]")

                self.__required_ports[source] -= 1
                self.__required_ports[target] -= 1

                self.__node_realisations += 1

            else:
                raise Exception(f"> FAILURE to realise SP edge : {edge} [cause:unrealised-endpoints]")

        console.info(f"Number of node-realisations: {self.__node_realisations}")
        console.info(f"Number of edge-realisations: {self.__edge_realisations}")

        for edge in self.__graph.get_zx_edges():
            if not edge.is_realised():
                console.warning(f"> Unrealised edge : {edge}")

    def __attempt_node_realisation(self, source: ZxNode, target: ZxNode) -> bool:
        # Place a cube of a kind suitable for the type of the unrealised endpoint node can be placed.
        console.info(f"> Searching for node-realisation : {source} - {target}")
        console.info(f">> Source ports : {self.__required_ports[source]}/{len(self.__available_ports[source])}")
        path = PlacementFinderBFS.find_closest_realisation(self.__graph, source.realising_cube, target, reservations = self.__reservations)

        if path is None:
            console.error(f"Failed to find any path for node-realisation {source} - {target}")
            return False

        console.info(f"> Optimal path found : {path}")

        # Realise the target cube and the path connecting it to the source cube
        self.__graph.realise_zx_node(target, path.final)
        # TODO: use Path.to_specification(..)
        self.__graph.realise_zx_edge(source.id, target.id, proposal = path)

        self.__reserve_positions(target)

        # Remove the reserved positions of ports from those available ones
        for position in path.extra_cubes:
            self.__occlude_positions(position)
        self.__occlude_positions(target.realising_cube.position)

        return True

    def __attempt_edge_realisation(self, source: ZxNode, target: ZxNode) -> bool:
        # Place a sequence of cubes connected by pipes in between the source and target realising cubes.
        console.info(f"> Searching for edge-realisation : {source} - {target}")
        console.info(f">> Source ports : {self.__required_ports[source]}/{len(self.__available_ports[source])}")
        console.info(f">> Target ports : {self.__required_ports[target]}/{len(self.__available_ports[target])}")

        path = PathfinderDFS.find_optimal_paths(source.realising_cube, target.realising_cube, graph = self.__graph)

        if path is None:
            console.error(f"Failed to find any path for edge-realisation {source} - {target}")
            return False

        console.info(f"> Optimal path found : {path}")

        self.__graph.realise_zx_edge(source.id, target.id, proposal = path)

        # Remove the reserved positions of ports from those available ones
        for position in path.extra_cubes:
            self.__occlude_positions(position)

        return True