import heapq
from collections import defaultdict
from functools import total_ordering

from recordclass import RecordClass

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.components import ZxNode, BgCube, ZxEdge
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.pathfinders.depth_first_search import PathfinderDFS
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

@total_ordering
class VertexNode(RecordClass):
    node: ZxNode
    required_ports: int
    available_ports: set[Coordinates]

    @property
    def remaining_ports(self):
        return len(self.available_ports) - self.required_ports

    def __lt__(self, other):
        return self.remaining_ports < other.remaining_ports if self.remaining_ports != other.remaining_ports else self.required_ports <= other.required_ports

    def __str__(self):
        return f"{self.node} [rq:{self.required_ports},av:{len(self.available_ports)}]"

    def __repr__(self):
        return str(self)

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
            holder = self.__vertices[self.__reservations[position]]
            holder.available_ports.remove(position)
            self.__reservations.pop(position)
            if holder.remaining_ports == 0:
                console.warning(f"O> Time to prioritize {holder}")
            elif holder.remaining_ports < 0:
                console.error(f"O> TOO LATE for {holder}")

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
            console.warning(f"R> Time to prioritize {vertex}")
        elif vertex.remaining_ports < 0:
            console.error(f"R> TOO LATE for {vertex}")

    # TODO: > represent the spacetime available and pathfind to the border of the blockgraph ?

    def process(self, graph: VolumetricZxGraph, root: ZxNode, root_kind: CubeKind | None = None):
        console.info(f"Starting inflation from root {root}")

        # Realise the root of the construction.
        root_cube = BgCube(
            kind = root_kind if root_kind else CubeKind.suitable_kinds(root.type)[0],
            position = SpacetimeHelper.ORIGIN
        )
        graph.realise_zx_node(root, root_cube)

        queue: list[VertexNode] = []
        heapq.heappush( queue, self.__vertices[root] )
        self.__reserve_ports(root)

        # TODO: Realise cross edges in order of decreasing Manhattan Distance between the endpoint cubes ?

        while len(queue) > 0:
            queue = [ vt for vt in queue if vt.required_ports > 0 ]
            heapq.heapify(queue)
            current: VertexNode = heapq.heappop(queue)
            source = current.node
            console.warning(f"Processing vertex {current}")
            console.warning(f"> Chosen among : {list(filter(lambda vt: vt.remaining_ports == current.remaining_ports, queue))}")
            # TODO: this will fail to reach cross-edges
            target: ZxNode
            candidate: ZxNode | None = None
            try:
                candidate = next(filter(lambda nb: not nb.is_realised(), graph.get_zx_neighbors(source)))
            except StopIteration:
                console.warning(f"> No unrealised neighbor found [{source}].")

            if candidate is None:
                try:
                    candidate = next(filter(lambda nb: not graph.get_zx_edge(source.id, nb.id).is_realised(), graph.get_zx_neighbors(source)))
                except StopIteration:
                    console.warning(f"> No unrealised edge found [{source}].")
                    continue

            if candidate is None:
                continue

            target = candidate

            console.debug(f"> Processing edge {source} - {target}")

            zx_edge = graph.get_zx_edge(source.id, target.id)

            if zx_edge.is_realised():
                console.warning(f"> Edge is already realised : {zx_edge}")
                continue

            if not source.is_realised():
                console.error(f"> FAILURE to realise FP edge : {zx_edge} [cause:unrealised-source]")

            if not target.is_realised():
                success = self.__attempt_node_realisation(source, target)

                if not success:
                    if self.__vertices[zx_edge.source].remaining_ports < 0 or self.__vertices[zx_edge.target].remaining_ports < 0:
                        cause = "insufficient-ports"
                    else:
                        cause = "unknown"
                    console.error(f"> FAILURE to realise FP edge : {zx_edge} [cause:{cause}]")

                self.__node_realisations += 1
            else: # target.is_realised():
                success = self.__attempt_edge_realisation(source, target)

                if not success:
                    source_vertex = self.__vertices[zx_edge.source]
                    target_vertex = self.__vertices[zx_edge.target]
                    if source_vertex.remaining_ports < 0 or target_vertex.remaining_ports < 0:
                        cause = "insufficient-ports"
                    else:
                        cause = "unknown"
                    raise Exception(f"> FAILURE to realise SP edge : {zx_edge} [cause:{cause}]")

                self.__edge_realisations += 1

            self.__vertices[source].required_ports -= 1
            self.__vertices[target].required_ports -= 1

            if current.required_ports > 0:
                heapq.heappush(queue, current)

            if self.__vertices[target].required_ports > 0:
                heapq.heappush(queue, self.__vertices[target] )

        console.info(f"Number of node-realisations: {self.__node_realisations}")
        console.info(f"Number of edge-realisations: {self.__edge_realisations}")
        console.info(f"Number of unreachable nodes: {sum(1 for v in self.__vertices.values() if v.remaining_ports < 0)}")

        report: dict[str, list[ZxEdge]] = defaultdict(list)

        for edge in graph.get_zx_edges():
            if not edge.is_realised():
                cause = None
                if edge.source.is_realised() or edge.target.is_realised():
                    if self.__vertices[edge.source].remaining_ports < 0 or self.__vertices[edge.target].remaining_ports < 0:
                        cause = "insufficient-ports"
                else:
                    cause = "disconnected-component"

                if cause is not None:
                    report[cause].append( edge )
                    console.warning(f"> Unrealised edge : {edge} [cause:{cause}]")

        return report

    def __attempt_node_realisation(self, source: ZxNode, target: ZxNode) -> bool:
        # Place a cube of a kind suitable for the type of the unrealised endpoint node can be placed.
        console.info(f"> Searching for node-realisation : {source} - {target}")
        source_vertex = self.__vertices[source]
        console.debug(f">> Source ports : {source_vertex.required_ports}/{source_vertex.available_ports}")

        if source_vertex.remaining_ports < 0:
            console.error(f"Insufficient number of ports to realise {source} - {target}")
            return False

        path = PathfinderDFS.find_closest_realisation(
            graph = self.__graph, source = source.realising_cube, target = target,
            reservations = self.__reservations
        )

        if path is None:
            console.error(f"Failed to find any path for node-realisation {source} - {target}")
            return False

        console.info(f"> Optimal path found : {path}")

        # Realise the target cube and the path connecting it to the source cube
        self.__graph.realise_zx_node(target, path.final)
        self.__graph.realise_zx_edge(source.id, target.id, path)

        self.__reserve_ports(target)

        # Remove the reserved positions of ports from those available ones
        for cube in path.extra_cubes:
            self.__occlude_ports(cube.position)
        self.__occlude_ports(target.realising_cube.position)

        return True

    def __attempt_edge_realisation(self, source: ZxNode, target: ZxNode) -> bool:
        # Place a sequence of cubes connected by pipes in between the source and target realising cubes.
        console.info(f"> Searching for edge-realisation : {source} - {target}")
        source_vertex = self.__vertices[source]
        target_vertex = self.__vertices[target]
        console.debug(f">> Source ports : {source_vertex.required_ports}/{source_vertex.available_ports}")
        console.debug(f">> Target ports : {target_vertex.required_ports}/{target_vertex.available_ports}")

        if source_vertex.remaining_ports < 0:
            console.error(f"Insufficient number of ports to realise {source} - {target}")
            return False

        if target_vertex.remaining_ports < 0:
            console.error(f"Insufficient number of ports to realise {source} - {target}")
            return False

        path = PathfinderDFS.find_optimal_paths(self.__graph, source.realising_cube, target.realising_cube)

        if path is None:
            console.error(f"Failed to find any path for edge-realisation {source} - {target}")
            return False

        console.info(f"> Optimal path found : {path}")

        self.__graph.realise_zx_edge(source.id, target.id, proposal = path)

        # Remove the reserved positions of ports from those available ones
        for cube in path.extra_cubes:
            self.__occlude_ports(cube.position)

        return True