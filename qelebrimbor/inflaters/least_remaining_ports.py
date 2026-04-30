from functools import total_ordering
from queue import PriorityQueue

from recordclass import RecordClass

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.components import ZxNode, BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.pathfinders.depth_first_search import PathfinderDFS
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger("qelebrimbor.main")

@total_ordering
class VertexNode(RecordClass):
    node: ZxNode
    required_ports: int
    available_ports: set[Coordinates]

    @property
    def remaining_ports(self):
        return len(self.available_ports) - self.required_ports

    def __lt__(self, other):
        return self.remaining_ports <= other.remaining_ports

    def __str__(self):
        return f"{self.node} [{self.required_ports}/{len(self.available_ports)}]"

class ZxGraphInflaterPorts:
    def __init__(self, graph: VolumetricZxGraph):
        self.__graph = graph
        self.__node_realisations = 0
        self.__edge_realisations = 0

        self.__vertices: dict[ZxNode, VertexNode] = {}
        for node in graph.get_zx_nodes():
            self.__vertices[node] = VertexNode(node = node, required_ports = graph.get_zx_degree(node.id), available_ports = set())

        self.__reservations: dict[Coordinates, ZxNode] = dict()

    def __occlude_ports(self, position: Coordinates):
        if position in self.__reservations:
            holder = self.__reservations[position]
            vertex = self.__vertices[holder]
            vertex.available_ports.remove(position)
            self.__reservations.pop(position)
            if vertex.remaining_ports == 0:
                console.warning(f"O> Time to prioritize holder {holder} [{vertex.required_ports}/{len(vertex.available_ports)}]")
            elif vertex.remaining_ports < 0:
                console.error(f"O> TOO LATE to prioritize holder {holder} [{vertex.required_ports}/{len(vertex.available_ports)}]")

    def __reserve_ports(self, node: ZxNode):
        cube = node.realising_cube
        vertex = self.__vertices[node]
        constellation = SpacetimeHelper.get_constellation(cube.position, cube.kind.get_reach())
        for position in constellation:
            if position in self.__reservations:
                console.warning(f"Position {position} already reserved by {self.__reservations[position]} [requester={cube}]")
                continue

            if position not in self.__graph.occupied:
                self.__reservations[position] = node
                vertex.available_ports.add(position)

        if vertex.remaining_ports == 0:
            console.warning(f"R> Time to prioritize node {node} [{vertex.required_ports}/{len(vertex.available_ports)}]")
        elif vertex.remaining_ports < 0:
            console.error(f"R> TOO LATE to prioritize node {node} [{vertex.required_ports}/{len(vertex.available_ports)}]")

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

        queue: PriorityQueue[VertexNode] = PriorityQueue[VertexNode]()
        queue.put( self.__vertices[root] )
        self.__reserve_ports(root)

        # TODO: Realise cross edges in order of decreasing Manhattan Distance between the endpoint cubes ?

        while not queue.empty():
            current: VertexNode = queue.get()
            source = current.node
            console.info(f"Processing vertex {source} [{current}]")
            # TODO: this will fail to reach cross-edges
            target = None
            try:
                target = next(filter(lambda nb: not nb.is_realised(), graph.get_zx_neighbors(source)))
            except StopIteration:
                console.info(f"> No unrealised neighbor found [{source}].")

            if target is None:
                try:
                    target = next(filter(lambda nb: not graph.get_zx_edge(source.id, nb.id).is_realised(), graph.get_zx_neighbors(source)))
                except StopIteration:
                    console.info(f"> No unrealised edge found [{source}].")
                    continue

            console.info(f"Processing edge {source} - {target}")

            zx_edge = graph.get_zx_edge(source.id, target.id)

            if zx_edge.is_realised():
                console.warning(f"> Edge is already realised : {zx_edge}")
                continue

            if not source.is_realised():
                console.error(f"> Vertex has unrealised node ... {source}")

            if not target.is_realised():
                success = self.__attempt_node_realisation(source, target)

                if not success:
                    console.error(f"> FAILURE to realise FP edge : {zx_edge} [cause:pathfinder]")
                    continue

                self.__vertices[source].required_ports -= 1
                self.__vertices[target].required_ports -= 1

                self.__node_realisations += 1

                if current.required_ports > 0:
                    queue.put(current)

                if self.__vertices[target].required_ports > 0:
                    queue.put( self.__vertices[target] )
            else: # target.is_realised():
                console.error(f"> FAILURE to realise SP edge : {zx_edge} [cause:not-implemented]")

        console.info(f"Number of node-realisations: {self.__node_realisations}")
        console.info(f"Number of edge-realisations: {self.__edge_realisations}")
        console.info(f"Number of unreachable nodes: {sum(1 for v in self.__vertices.values() if v.remaining_ports < 0)}")

        for edge in graph.get_zx_edges():
            if not edge.is_realised():
                if edge.source.is_realised() and edge.target.is_realised():
                    console.warning(f"> Unrealised edge : {edge} [cause:not-implemented]")

    def __attempt_node_realisation(self, source: ZxNode, target: ZxNode) -> bool:
        # Place a cube of a kind suitable for the type of the unrealised endpoint node can be placed.
        console.info(f"> Searching for node-realisation : {source} - {target}")
        source_vertex = self.__vertices[source]
        console.info(f">> Source ports : {source_vertex.required_ports}/{len(source_vertex.available_ports)}")
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

        self.__reserve_ports(target)

        # Remove the reserved positions of ports from those available ones
        for position in path.extras:
            self.__occlude_ports(position)
        self.__occlude_ports(target.realising_cube.position)

        return True

    def __attempt_edge_realisation(self, source: ZxNode, target: ZxNode) -> bool:
        # Place a sequence of cubes connected by pipes in between the source and target realising cubes.
        console.info(f"> Searching for edge-realisation : {source} - {target}")
        source_vertex = self.__vertices[source]
        target_vertex = self.__vertices[target]
        console.info(f">> Source ports : {source_vertex.required_ports}/{len(target_vertex.available_ports)}")
        console.info(f">> Target ports : {target_vertex.required_ports}/{len(target_vertex.available_ports)}")

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
            self.__occlude_ports(position)

        return True