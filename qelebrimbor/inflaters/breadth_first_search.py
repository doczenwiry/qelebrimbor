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
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.spacetime.connectivity.sufficient_ports import OpenPortsTracker
from qelebrimbor.spacetime.placefinders.breadth_first_search import PlacefinderBFS
from qelebrimbor.spacetime.pathfinders.depth_first_search import PathfinderDFS
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger("qelebrimbor.main")

class ZxGraphInflaterBFS:
    def __init__(self, graph: VolumetricZxGraph):
        self.__graph = graph
        self.__spacetime = graph.spacetime

        self.__ports_tracker = OpenPortsTracker(graph)
        self.__placefinder = PlacefinderBFS(graph, self.__ports_tracker)
        self.__pathfinder = PathfinderDFS(graph)

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
        self.__ports_tracker.reserve_ports(root_cube)

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
                if self.__ports_tracker.reachable(source.realising_cube):
                    raise Exception(f"> FAILURE to realise FP edge : {edge} [cause:insufficient-ports]")

                success = self.__attempt_node_realisation(source, target)

                if not success:
                    raise Exception(f"> FAILURE to realise FP edge : {edge} [cause:pathfinder]")
            else:
                raise Exception(f"> FAILURE to realise FP edge : {edge} [cause:unrealised-endpoints]")

        # Perform a pass of edge-realisations (a.k.a. cross edges)
        unrealised_edges = filter(
            lambda edge: not self.__graph.get_zx_edge(*edge).is_realised(),
            nx.edge_bfs(cast(nx.Graph, self.__graph), root_node.id)
        )

        for edge in unrealised_edges:
            zx_edge = self.__graph.get_zx_edge(*edge)

            if zx_edge.is_realised():
                console.warning(f"> Second attempt to realise edge : {edge}")
                continue

            source, target = (zx_edge.source, zx_edge.target) if zx_edge.source.is_realised() else (zx_edge.target, zx_edge.source)

            if source.is_realised() and target.is_realised():
                if self.__ports_tracker.reachable(source.realising_cube) or self.__ports_tracker.reachable(target.realising_cube):
                    raise Exception(f"> FAILURE to realise SP edge : {edge} [cause:insufficient-ports]")

                success = self.__attempt_edge_realisation(source, target)
                if not success:
                    raise Exception(f"> FAILURE to realise SP edge : {edge} [cause:pathfinder]")
            else:
                raise Exception(f"> FAILURE to realise SP edge : {edge} [cause:unrealised-endpoints]")

        for edge in self.__graph.get_zx_edges():
            if not edge.is_realised():
                console.warning(f"> Unrealised edge : {edge}")

    def __attempt_node_realisation(self, source: ZxNode, target: ZxNode) -> bool:
        # Place a cube of a kind suitable for the type of the unrealised endpoint node can be placed.
        console.info(f"> Searching for node-realisation : {source} - {target}")
        console.info(f">> Source ports : {self.__ports_tracker.report(source.realising_cube)}")
        path = self.__placefinder.find_closest_realisation(source.realising_cube, target)

        if path is None:
            console.error(f"Failed to find any path for node-realisation {source} - {target}")
            return False

        console.info(f"> Optimal path found : {path}")

        # Realise the target cube and the path connecting it to the source cube
        self.__graph.realise_zx_node(target, path.final)
        # TODO: use Path.to_specification(..)
        self.__graph.realise_zx_edge(source.id, target.id, proposal = path)

        self.__ports_tracker.reserve_ports(path.final)

        # Remove the reserved positions of ports from those available ones
        for position in path.extra_cubes:
            self.__ports_tracker.occlude_ports(position)
        self.__ports_tracker.occlude_ports(path.final.position)

        self.__ports_tracker.connect_ports(
            source = (source.realising_cube, path.start_port),
            target = (target.realising_cube, path.final_port)
        )

        return True

    def __attempt_edge_realisation(self, source: ZxNode, target: ZxNode) -> bool:
        # Place a sequence of cubes connected by pipes in between the source and target realising cubes.
        console.info(f"> Searching for edge-realisation : {source} - {target}")
        console.debug(f">> Source ports : {self.__ports_tracker.report(source.realising_cube)}")
        console.debug(f">> Target ports : {self.__ports_tracker.report(target.realising_cube)}")

        path = self.__pathfinder.find_optimal_paths(source.realising_cube, target.realising_cube)

        if path is None:
            console.error(f"Failed to find any path for edge-realisation {source} - {target}")
            return False

        console.info(f"> Optimal path found : {path}")

        self.__graph.realise_zx_edge(source.id, target.id, proposal = path)

        # Remove the reserved positions of ports from those available ones
        for position in path.extra_cubes:
            self.__ports_tracker.occlude_ports(position)

        self.__ports_tracker.connect_ports(
            source = (source.realising_cube, path.start_port),
            target = (target.realising_cube, path.final_port)
        )

        return True