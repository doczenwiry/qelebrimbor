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

from qelebrimbor.common.path import Path, Length
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.components import BgCube, ZxNode, ZxEdge

from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.calculator import ManhattanCalculator
from qelebrimbor.spacetime.fabric import SpacetimeFabric
from qelebrimbor.spacetime.tracer import SpacetimeTracer

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class ChainfinderDFS:
    def __init__(self, graph: VolumetricZxGraph = None, branch_and_bound: bool = False, tracing: bool = False):
        """
        Create a PathfinderDFS to search for optimal paths between cubes in spacetime.
        :param graph: The VolumetricZxGraph serving as the context for the search.
        :param branch_and_bound: Controls whether a Branch-and-Bound is performed to improve the first path found.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        Proof of the possibility would be nice. Refutation thereof would be better.
        :param tracing:
        """
        self.__graph = graph if graph else VolumetricZxGraph()
        self.__spacetime = graph.spacetime if graph else SpacetimeFabric()
        self.__branch_and_bound = branch_and_bound
        self.__tracing = tracing

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
        ChainfinderDFS.__remove_from_unrelaxed(current, min_distance, unrelaxed)
        return current

    def find_optimum(self,
            source: BgCube, target: BgCube,
            zx_nodes: list[ZxNode] | None = None, zx_edges: list[ZxEdge] | None = None,
            maximal_excess: int = None
    ) -> Path | None:
        node_type_restrictions: list[NodeType] = list(map(lambda zxn: zxn.type, zx_nodes)) if zx_nodes else []
        edge_type_restrictions: list[EdgeType] = list(map(lambda zxe: zxe.type, zx_edges)) if zx_edges else []

        if any(tr in {NodeType.O, NodeType.Y} for tr in node_type_restrictions):
            raise Exception(f"Restrictions cannot contain cubes of NodeType.O or NodeType.Y.")

        nt = len(node_type_restrictions)
        et = len(edge_type_restrictions)

        optimum: Path | None = None

        minimal_length_achieved: int | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()
        unrelaxed: dict[Length, list[BgCube]] = defaultdict(list)
        ChainfinderDFS.__add_into_unrelaxed(source, 0, unrelaxed)
        minimal_paths[ (source.kind, source.position) ] = Path(start = source)

        manhattan_distance = source.position.get_manhattan_distance(target.position)

        maximal_distance = manhattan_distance + maximal_excess if maximal_excess else None

        tracer: SpacetimeTracer | None = SpacetimeTracer() if self.__tracing else None
        if tracer:
            tracer.add_node(source)

        console.info(f"Searching for paths from {source} to {target} [restrictions:{zx_nodes}].")

        while len(unrelaxed) > 0 and optimum is None:
            current: BgCube = ChainfinderDFS.__extract_closest_point(unrelaxed)
            current_point = (current.kind, current.position)
            current_path = minimal_paths[current_point]
            terminal = current_path.final

            minimal_length_possible: int = ManhattanCalculator.minimal_manhattan_length(terminal, target)
            manhattan_length_projected: int = current_path.manhattan_length() + minimal_length_possible

            # Branch-and-bound
            if minimal_length_achieved and minimal_length_achieved <= manhattan_length_projected:
                continue

            length = current_path.manhattan_length()
            remaining_distance = current.position.get_manhattan_distance(target.position)
            console.debug(f"Current [{length}/{remaining_distance}]: {current} [mlp-rest:{minimal_length_possible},mlp-total:{manhattan_length_projected},path:{current_path}]")

            if BlockGraphHelper.connectable(current, target, EdgeType.IDENTITY) and len(current_path.extra_cubes) >= nt and not self.__graph.has_bg_pipe(current.id, target.id):
                console.debug(f"> Connectable to {target}")
                completed_path = current_path.extend(cube = target, pipe_type = EdgeType.IDENTITY)

                console.debug(f"> Completed path [{minimal_length_achieved}]: {completed_path}")

                # Tracing exploration
                if tracer:
                    tracer.add_node(target)
                    tracer.add_edge(terminal, target)

                if not minimal_length_achieved or completed_path.manhattan_length() < minimal_length_achieved:
                    minimal_length_achieved = completed_path.manhattan_length()
                    optimum = completed_path

            node_type_required = { node_type_restrictions[length] } if length < nt else { NodeType.X, NodeType.Z }
            pipe_type_required =   edge_type_restrictions[length]   if length < et else EdgeType.IDENTITY
            console.debug(f"> Types required : {node_type_required}")
            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal, node_types = node_type_required, pipe_type = pipe_type_required):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")

                if maximal_distance and maximal_distance < source.position.get_manhattan_distance(neighbor.position):
                    continue

                # Ignore neighbor if it introduces a loop
                if neighbor.position in current_path.occupied:
                    continue

                # Ignore neighbor if the position is already occupied in spacetime
                if self.__spacetime.is_occupied(neighbor.position):
                    continue

                # Tracing exploration
                if tracer:
                    tracer.add_node(neighbor)
                    tracer.add_edge(terminal, neighbor)

                extended_path = current_path.extend(cube = neighbor, pipe_type = EdgeType.IDENTITY)
                extended_distance = extended_path.manhattan_length()

                if neighbor_point not in minimal_paths or extended_distance < minimal_paths[neighbor_point].manhattan_length():
                    # Update position of neighbor in unrelaxed as its distance is being updated
                    if neighbor in minimal_paths:
                        ChainfinderDFS.__remove_from_unrelaxed(
                            neighbor, minimal_paths[neighbor_point].manhattan_length(), unrelaxed
                        )
                    ChainfinderDFS.__add_into_unrelaxed(neighbor, ManhattanCalculator.minimal_manhattan_length(neighbor, target), unrelaxed)

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

        # Tracing exploration
        if tracer:
            tracer.report(cubes_to_label= [source, target])

        return optimum