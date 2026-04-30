from collections import defaultdict
from queue import PriorityQueue

import networkx as nx

from qelebrimbor.common.attributes_bg import CubeId, CubeKind
from qelebrimbor.common.attributes_zx import NodeId, EdgeType
from qelebrimbor.common.components import ZxNode, BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.pathfinders.depth_first_search import PathfinderDFS
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

    def process(self, graph: VolumetricZxGraph, root: ZxNode, root_kind: CubeKind | None = None):
        console.info(f"Starting inflation from root {root}")

        # Realise the root of the construction.
        root_cube = BgCube(
            kind = root_kind if root_kind else CubeKind.suitable_kinds(root.type)[0],
            position = SpacetimeHelper.ORIGIN
        )
        graph.realise_zx_node(root, root_cube)

        self.__reserve_positions(root)

        # Form the backbone with the bfs_edges
        # > Reserve needed positions based on remaining missing neighbors
        # Then complete with the unrealised edges from edge_bfs
        # > Perform realisations in order of decreasing Manhattan Distance between the endpoint cubes

        # Perform a pass of node-realisations (a.k.a. first-pass edges)
        for edge in nx.bfs_edges(graph, root.id):
            zx_edge = graph.get_zx_edge(*edge)

            if zx_edge.is_realised():
                console.warning(f"> Second attempt to realise edge : {edge}")
                continue

            source, target = (zx_edge.source, zx_edge.target) if zx_edge.source.is_realised() else (zx_edge.target, zx_edge.source)

            if source.is_realised() or target.is_realised():
                if any(position in graph.occupied for position in self.__available_ports[source]):
                    console.error(f"> DETECTION FAILURE: {source} [{self.__available_ports[source]}]")
                    console.error(f">>> {list(filter(lambda position : position in graph.occupied, self.__available_ports[source]))}")
                    console.error(f">>> {self.__required_ports[source]}")

                if len(self.__available_ports[source]) < self.__required_ports[source]:
                    console.error(f"> FAILURE to realise SP edge : {edge} [insufficient number of ports at {source.realising_cube}]")
                    continue

                success = self.__attempt_node_realisation(source, target)

                if not success:
                    console.error(f"> FAILURE to realise FP edge : {edge}")

                self.__required_ports[source] -= 1
                self.__required_ports[target] -= 1

                self.__node_realisations += 1

            else:
                console.error(f"> UNREALISABLE FP edge : {edge} [need one realised endpoint]")

        # Perform a pass of edge-realisations (a.k.a. cross edges)
        unrealised_edges = filter(
            lambda edge: not graph.get_zx_edge(*edge).is_realised(),
            nx.edge_bfs(graph, root.id)
        )

        for edge in unrealised_edges:
            zx_edge = graph.get_zx_edge(*edge)

            if zx_edge.is_realised():
                console.warning(f"> Second attempt to realise edge : {edge}")
                continue

            # if tuple(sorted(edge)) in [(24, 29), (58, 59), (60, 61), (71, 79), (70, 73)]:
            #     console.warning(f">> HARDCODED IGNORING OF EDGE FROM EXAMPLE [{edge}].")
            #     continue

            source, target = (zx_edge.source, zx_edge.target) if zx_edge.source.is_realised() else (zx_edge.target, zx_edge.source)

            if source.is_realised() and target.is_realised():
                if len(self.__available_ports[source]) < self.__required_ports[source] and len(self.__available_ports[target]) < self.__required_ports[target]:
                    console.error(f"> FAILURE to realise SP edge : {edge} [insufficient number of ports at {source.realising_cube}]")
                    continue

                success = self.__attempt_edge_realisation(source, target)
                if not success:
                    console.error(f"> FAILURE to realise SP edge : {edge} [no path found by pathfinder]")

                self.__required_ports[source] -= 1
                self.__required_ports[target] -= 1

                self.__node_realisations += 1

            else:
                console.error(f"> Unrealisable SP edge : {edge} [need two realised endpoints]")

        console.info(f"Number of node-realisations: {self.__node_realisations}")
        console.info(f"Number of edge-realisations: {self.__edge_realisations}")

        for edge in graph.get_zx_edges():
            if not edge.is_realised():
                console.warning(f"> Unrealised edge : {edge}")

    def __attempt_node_realisation(self, source: ZxNode, target: ZxNode) -> bool:
        # Place a cube of a kind suitable for the type of the unrealised endpoint node can be placed.
        console.info(f"> Searching for node-realisation : {source} - {target}")
        console.info(f">> Source ports : {self.__required_ports[source]}/{len(self.__available_ports[source])}")
        path = PathfinderDFS.find_closest_realisation(self.__graph, source.realising_cube, target)

        if path is None:
            console.error(f"Failed to find any path for node-realisation {source} - {target}")
            return False

        console.info(f"> Optimal path found : {path}")

        # Realise the target cube and the path connecting it to the source cube
        self.__graph.realise_zx_node(target, path.target)
        # TODO: use Path.to_specification(..)
        self.__graph.realise_zx_edge(source.id, target.id,
            proposal = PathSpecification(
                source.realising_cube, target.realising_cube,
                extras = path.extras, pipes = [ EdgeType.IDENTITY for _ in range(path.manhattan_length()) ]
            )
        )

        self.__reserve_positions(target)

        # Remove the reserved positions of ports from those available ones
        for position in path.extras:
            self.__occlude_positions(position)
        self.__occlude_positions(target.realising_cube.position)

        return True

    def __attempt_edge_realisation(self, source: ZxNode, target: ZxNode) -> bool:
        # Place a sequence of cubes connected by pipes in between the source and target realising cubes.
        console.info(f"> Searching for edge-realisation : {source} - {target}")
        console.info(f">> Source ports : {self.__required_ports[source]}/{len(self.__available_ports[source])}")
        console.info(f">> Target ports : {self.__required_ports[target]}/{len(self.__available_ports[target])}")

        path = PathfinderDFS.find_optimal_paths(self.__graph, source.realising_cube, target.realising_cube)

        if path is None:
            console.error(f"Failed to find any path for edge-realisation {source} - {target}")
            return False

        console.info(f"> Optimal path found : {path}")

        self.__graph.realise_zx_edge(source.id, target.id, proposal = PathSpecification(
            source.realising_cube, target.realising_cube,
            extras = path.extras, pipes = [ EdgeType.IDENTITY for _ in range(path.manhattan_length()) ]
        ))

        # Remove the reserved positions of ports from those available ones
        for position in path.extras:
            self.__occlude_positions(position)

        return True