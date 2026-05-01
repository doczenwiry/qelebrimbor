from collections import defaultdict, deque
import matplotlib.pyplot as plt
import networkx as nx

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeId, NodeType, EdgeType
from qelebrimbor.common.components import BgCube, ZxNode

from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.common.path import Length, Path

import logging

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

console = logging.getLogger(__name__)

class PathfinderDFS:
    @staticmethod
    def __retrieve_closest_unrelaxed(
            unrelaxed: dict[Length, list[BgCube]]
    ) -> tuple[BgCube, Length]:
        pass

    @staticmethod
    def __add_into_unrelaxed(cube: BgCube, distance: Length, unrelaxed: dict[Length, list[BgCube]]):
        if distance not in unrelaxed:
            unrelaxed[distance] = []
        unrelaxed[distance].append(cube)

    @staticmethod
    def __remove_from_unrelaxed(cube: BgCube, distance: Length, unrelaxed: dict[Length, list[BgCube]]):
        unrelaxed[distance].remove(cube)
        if len(unrelaxed[distance]) == 0:
            unrelaxed.pop(distance)

    @staticmethod
    def __extract_closest_point(unrelaxed: dict[Length, list[BgCube]]) -> BgCube:
        min_distance = min(unrelaxed.keys())
        current: BgCube = unrelaxed[min_distance][0]
        PathfinderDFS.__remove_from_unrelaxed(current, min_distance, unrelaxed)
        return current

    # TODO: consider the type of Edge between source and target (IDENTITY or HADAMARD)
    @staticmethod
    def find_closest_realisation(
            graph: VolumetricZxGraph, source: BgCube, target: ZxNode,
            reservations: dict[Coordinates, ZxNode],
            maximal_distance: int = None,
            tracing: bool = False
    ) -> Path | None:
        optimum: Path | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()
        unrelaxed: deque[Path] = deque()
        initial = Path(start = source)
        unrelaxed.append( initial )
        minimal_paths[ (source.kind, source.position) ] = initial

        number_of_ports_required = graph.get_zx_degree(target.id)
        console.info(f"Searching for placement from {source} to {target}. [ports required:{number_of_ports_required}]")

        target_suitable_kinds: list[CubeKind] = CubeKind.suitable_kinds(target.type)

        pruning_performed = 0
        points_discovered = 0
        points_considered = 0

        # Tracing exploration
        nodes : dict[BgCube, NodeId] = dict()
        labels: dict[NodeId, str] = dict()
        trace: nx.Graph = nx.Graph()
        if tracing:
            trace.add_node( 0 )
            labels[len(nodes)] = str(source)
            nodes[source] = 0

        while len(unrelaxed) != 0 and optimum is None:
            current_path = unrelaxed.pop()
            terminal = current_path.final

            console.debug(f"Current : {current_path}")

            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")

                if maximal_distance and maximal_distance < source.position.get_manhattan_distance(neighbor.position):
                    continue

                # Ignore neighbor if it introduces a loop
                if neighbor.position in current_path.occupied or neighbor.position in graph.occupied:
                    console.debug(f">> Position occupied : {neighbor.position}")
                    continue

                # if neighbor.position in reservations:
                #     # Allow taking the reservations if it is not critical to the holder.
                #     holder = reservations[neighbor.position]
                #     if holder.id != source.realised_node.id:
                #         reserved_ports_positions = sum(1 for kv in reservations.items() if kv[1] == holder)
                #         # number_of_ports_required = 0
                #         # number_of_ports_required = sum(
                #         #     1 for nb in graph.get_zx_neighbors(holder) if graph.get_zx_edge(holder.id, nb.id).is_realised()
                #         # )
                #         # critical = number_of_ports_required <= reserved_ports_positions
                #         # console.warning(f"> Position reserved : {neighbor.position} by {holder} [rq:{number_of_ports_required},rv:{reserved_ports_positions},critical:{critical}]")
                #
                # #     if holder.id != source.realised_node.id:
                # #         console.debug(f">> Position {neighbor.position} reserved by {holder} [critical:{critical}]")
                # #         continue

                extended_path = current_path.extend(cube = neighbor, pipe_type = EdgeType.IDENTITY)
                console.debug(f"> Extended Path : {extended_path}")

                # If a suitable Cube has been reached for the target, consider it further
                console.debug(f"> Neighbor has kind {neighbor.kind} in {target_suitable_kinds} ?")
                if neighbor.kind in target_suitable_kinds:
                    open_ports = list(filter(
                        lambda pos : pos not in extended_path.occupied and pos not in graph.occupied and pos not in reservations,
                        SpacetimeHelper.get_constellation(neighbor.position, neighbor.kind.get_reach())
                    ))
                    number_of_open_ports = len(open_ports)
                    # If the position offers enough open ports, consider it as the optimum
                    console.debug(f"> Open ports found for {neighbor} : {open_ports} [req.{number_of_ports_required}]")
                    if number_of_ports_required <= number_of_open_ports:
                        optimum = extended_path
                        continue

                # Don't attempt to extend if the neighbor is a terminal cube.
                if neighbor.kind in [ CubeKind.OOO , CubeKind.YYY ]:
                    continue

                # Update position of neighbor in unrelaxed as its distance is being updated
                if neighbor not in minimal_paths:
                    unrelaxed.append( extended_path )

                # Tracing exploration
                if tracing:
                    # labels[len(nodes)] = str(neighbor)
                    nodes[neighbor] = len(nodes)
                    trace.add_node( nodes[neighbor] )
                    trace.add_edge( nodes[terminal], nodes[neighbor] )

                points_discovered += 1

                # Update minimal distance discovered
                minimal_paths[neighbor_point] = extended_path

            points_considered += 1

        console.debug(f"> Number of points considered : {points_considered}")
        console.debug(f"> Number of pruning performed : {pruning_performed}")
        console.debug(f"> Number of points discovered : {points_discovered}")

        if tracing:
            layout = nx.drawing.layout.bfs_layout(trace, start = 0)
            nx.draw(trace, layout, node_size = 1)
            nx.draw_networkx_labels(trace, layout, labels)
            console.debug(f"> Number of nodes : {len(trace.nodes)}")
            plt.show()

        return optimum

    @staticmethod
    def find_optimal_paths(
            graph: VolumetricZxGraph, source: BgCube, target: BgCube,
            maximal_excess: int = 10,
            bnb: bool = False,
            tracing: bool = False
    ) -> Path | None:
        """
        Perform path-finding using a Depth-First Search approach.
        :param graph: The VolumetricZxGraph that represents the context within which the path finding is performed
        :param source: The cube from which to start.
        :param target: The cube towards which to go.
        :param maximal_excess: The maximum number of additional cubes permitted on top of the Manhattan Length.
        :param bnb: Controls whether a Branch-and-Bound refinement ought to be performed after finding the first path.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        Proof of the possibility would be nice. Refutation thereof would be better.
        :param tracing: Controls whether to keep track of the order of relaxations performed by the pathfinder. Performance metric.
        :return:
        """
        optimum: Path | None = None

        minimal_length_achieved: int | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()
        unrelaxed: dict[Length, list[BgCube]] = defaultdict(list)
        PathfinderDFS.__add_into_unrelaxed(source, 0, unrelaxed)
        minimal_paths[ (source.kind, source.position) ] = Path(start = source)

        manhattan_distance = source.position.get_manhattan_distance(target.position)
        console.info(f"Searching for path from {source} to {target} [distance={manhattan_distance}].")

        maximal_distance = manhattan_distance + maximal_excess

        interconnect = { NodeType.X, NodeType.Z }

        pruning_performed = 0
        points_discovered = 0
        points_considered = 0

        # Tracing exploration
        nodes : dict[BgCube, NodeId] = dict()
        labels: dict[NodeId, str] = dict()
        trace: nx.Graph = nx.Graph()
        if tracing:
            trace.add_node( 0 )
            labels[len(nodes)] = str(source)
            nodes[source] = 0

        while len(unrelaxed) != 0 and (bnb or optimum is None):
            current: BgCube = PathfinderDFS.__extract_closest_point(unrelaxed)
            current_point = (current.kind, current.position)
            current_path = minimal_paths[current_point]
            terminal = current_path.final

            minimal_length_possible: int = Path.minimal_length_possible(terminal, target)
            manhattan_length_projected: int = current_path.manhattan_length() + minimal_length_possible

            # Branch-and-bound
            if minimal_length_achieved and minimal_length_achieved <= manhattan_length_projected:
                pruning_performed += 1
                continue

            console.debug(f"Current : {current} [mlp-rest:{minimal_length_possible},mlp-total:{manhattan_length_projected},path:{current_path}]")

            if BlockGraphHelper.connectable(current, target, EdgeType.IDENTITY):
                console.debug(f"> Connectable to {target} : {BlockGraphHelper.connectable(current, target, EdgeType.IDENTITY)}")
                completed_path = current_path.extend(cube = target, pipe_type = EdgeType.IDENTITY)
                if not minimal_length_achieved or completed_path.manhattan_length() < minimal_length_achieved:
                    minimal_length_achieved = completed_path.manhattan_length()
                    optimum = completed_path

            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal, node_types = interconnect):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")

                if maximal_distance < source.position.get_manhattan_distance(neighbor.position):
                    continue

                # Ignore neighbor if it introduces a loop
                if neighbor.position in current_path.occupied or neighbor.position in graph.occupied:
                    continue

                extended_path = current_path.extend(cube = neighbor, pipe_type = EdgeType.IDENTITY)
                extended_distance = extended_path.manhattan_length()

                if neighbor not in minimal_paths or extended_distance < minimal_paths[neighbor_point].manhattan_length():
                    # Update position of neighbor in unrelaxed as its distance is being updated
                    if neighbor in minimal_paths:
                        PathfinderDFS.__remove_from_unrelaxed(
                            neighbor, minimal_paths[neighbor_point].manhattan_length(), unrelaxed
                        )
                    PathfinderDFS.__add_into_unrelaxed(neighbor, Path.minimal_length_possible(neighbor, target), unrelaxed)

                    # Tracing exploration
                    if tracing:
                        # labels[len(nodes)] = str(neighbor)
                        nodes[neighbor] = len(nodes)
                        trace.add_node( nodes[neighbor] )
                        trace.add_edge( nodes[current], nodes[neighbor] )

                    points_discovered += 1

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

            points_considered += 1

        points_octahedron = int(manhattan_distance * (2 * manhattan_distance**2 + 1) / 3)
        console.debug(f"> Number of octahedron points : {points_octahedron}")
        console.debug(f"> Number of points considered : {points_considered}")
        console.debug(f"> Number of pruning performed : {pruning_performed}")
        console.debug(f"> Number of points discovered : {points_discovered}")

        if tracing:
            layout = nx.drawing.layout.bfs_layout(trace, start = 0)
            nx.draw(trace, layout, node_size = 1)
            nx.draw_networkx_labels(trace, layout, labels)
            console.debug(f"> Number of nodes : {len(trace.nodes)}")
            plt.show()

        return optimum