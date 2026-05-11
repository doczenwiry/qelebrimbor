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

import heapq

from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.zx.attributes import NodeType, EdgeType
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.bg.path import Path, Length

from qelebrimbor.helpers.blockgraph import BlockGraphHelper

from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class PathfinderDijkstra:
    def __init__(self, graph: VolumetricZxGraph = None, tracing: SpacetimeTracingReport | None = None):
        self.__graph = graph
        self.__tracing = tracing

    def find_optimum(
            self, source: BgCube, target: BgCube, edge_type: EdgeType, maximal_excess: int | None = None
    ) -> Path | None:
        optimum: Path | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()

        # TODO: switch to a more efficient data-structure instead of heapq (i.e. fibo-heap)
        unrelaxed: list[tuple[Length, Path]] = []

        initial = Path(start = source)
        minimal_paths[ (source.kind, source.position) ] = initial

        vertex: tuple[Length, Path] = (initial.length, initial)
        heapq.heappush(unrelaxed, vertex)

        manhattan_distance = source.position.get_manhattan_distance(target.position)
        console.info(f"Searching for path from {source} to {target} [distance={manhattan_distance}].")

        interconnect = { NodeType.X, NodeType.Z }

        # Tracing exploration
        tracer: SpacetimeTracer[BgCube] | None = SpacetimeTracer(reporting = self.__tracing) if self.__tracing else None
        if tracer:
            tracer.add_node(source, label = str(source))

        while len(unrelaxed) != 0 and optimum is None:
            heapq.heapify(unrelaxed)
            vertex: tuple[Length, Path] = heapq.heappop(unrelaxed)
            manhattan_length, current_path = vertex
            terminal = current_path.final

            console.debug(f"Current [{terminal}] : {current_path}")

            if BlockGraphHelper.connectable(terminal, target, EdgeType.IDENTITY):
                console.info(f">> Terminal {terminal} be connected to target {target} [{current_path}]")
                completed_path = current_path.extend(target, pipe_type = EdgeType.IDENTITY)

                # Tracing exploration
                if tracer:
                    tracer.add_node( target , label = str(target) )
                    tracer.add_edge( terminal, target )

                optimum = completed_path

            # Relaxation step on every neighbor
            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal, node_types = interconnect):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")

                # Ignore neighbor if it introduces a loop or its position is already occupied

                if neighbor.position in current_path.occupied:
                    continue

                if self.__graph and not self.__graph.spacetime.available(neighbor.position):
                    continue

                # Tracing exploration
                if tracer:
                    tracer.add_node(neighbor)
                    tracer.add_edge(terminal, neighbor)

                extended_path = current_path.extend(neighbor, pipe_type = EdgeType.IDENTITY)
                extended_distance = extended_path.length
                console.debug(f">> {current_path}   =Relax=   {extended_path}")

                if neighbor_point not in minimal_paths or extended_distance < minimal_paths[neighbor_point].length:
                    # Filtering out the neighbor from unrelaxed
                    unrelaxed = [ vertex for vertex in unrelaxed if vertex[1].final != neighbor ]
                    unrelaxed.append((extended_path.length, extended_path))

                    # Update minimal distance discovered
                    minimal_paths[neighbor_point] = extended_path

        # Tracing exploration
        if tracer:
            tracer.report()

        return optimum