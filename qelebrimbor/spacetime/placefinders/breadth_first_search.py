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

from collections import deque

from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.attributes_bg import CubeKind
from qelebrimbor.core.attributes_zx import EdgeType
from qelebrimbor.core.components import BgCube, ZxNode

from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.core.path import Path
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class PlacefinderBFS:
    def __init__(self,
        graph: VolumetricZxGraph, ports_tracker: OpenPortsTracker | None = None,
        tracing: SpacetimeTracingReport | None = None
    ):
        self.__graph = graph
        self.__spacetime = graph.spacetime
        self.__connectivity = ports_tracker if ports_tracker else OpenPortsTracker(self.__graph)
        self.__tracing = tracing

    # TODO: consider the type of Edge between source and target (IDENTITY or HADAMARD)
    def find_closest_realisation(self, source: BgCube, target: ZxNode, maximal_distance: int = None) -> Path | None:
        optimum: Path | None = None
        minimal_paths: dict[tuple[CubeKind, Coordinates], Path] = dict()
        unrelaxed: deque[Path] = deque()

        initial = Path(start = source)
        unrelaxed.append( initial )
        minimal_paths[ (source.kind, source.position) ] = initial

        number_of_ports_required = self.__graph.get_zx_degree(target.id)
        console.info(f"Searching for placement from {source} to {target} [ports required:{number_of_ports_required}]")

        target_suitable_kinds: list[CubeKind] = CubeKind.suitable_kinds(target.type)

        # Tracing exploration
        tracer: SpacetimeTracer[BgCube] | None = SpacetimeTracer(reporting = self.__tracing) if self.__tracing else None
        if tracer:
            tracer.add_node(source, label = str(source))

        while len(unrelaxed) != 0 and optimum is None:
            current_path = unrelaxed.pop()
            terminal = current_path.final

            console.debug(f"Current path : {current_path}")

            for neighbor in BlockGraphHelper.get_candidate_constellation(terminal):
                neighbor_point = (neighbor.kind, neighbor.position)
                console.debug(f"> Neighbor : {neighbor}")

                if maximal_distance and maximal_distance < current_path.manhattan_length():
                    continue

                # Ignore neighbor if it introduces a loop
                if current_path.occupies(neighbor.position):
                    console.debug(f">> Position already occupied by path : {neighbor.position}")
                    continue

                if self.__spacetime.occupied(neighbor.position):
                    occupant = self.__spacetime.occupant(neighbor.position)
                    console.debug(f">> Position {neighbor.position} already occupied in spacetime [{occupant}]")
                    continue

                if not self.__connectivity.preserved(source, target, neighbor.position):
                    continue

                extended_path = current_path.extend(cube = neighbor, pipe_type = EdgeType.IDENTITY)
                console.debug(f"> Extended Path : {extended_path}")

                # If a suitable Cube has been reached for the target, consider it further
                console.debug(f"> Neighbor has kind {neighbor.kind} in {target_suitable_kinds} ?")
                if neighbor.kind in target_suitable_kinds:
                    open_ports = list(filter(
                        lambda pos : not extended_path.occupies(pos) and not self.__spacetime.occupied(pos),
                        SpacetimeHelper.get_constellation(neighbor.position, neighbor.kind.get_reach())
                    ))
                    number_of_open_ports = len(open_ports)
                    # If the position offers enough open ports, consider it as the optimum
                    console.debug(f"> Open ports found for {neighbor} : {open_ports} [req.{number_of_ports_required}]")
                    if number_of_ports_required - 1 <= number_of_open_ports:
                        optimum = extended_path
                        continue

                # Don't attempt to extend if the neighbor is a terminal cube.
                if neighbor.kind in [ CubeKind.OOO , CubeKind.YYY ]:
                    continue

                # Update position of neighbor in unrelaxed as its distance is being updated
                if neighbor not in minimal_paths:
                    unrelaxed.append( extended_path )

                # Tracing exploration
                if tracer:
                    tracer.add_node(neighbor)
                    tracer.add_edge(terminal, neighbor)

                # Update minimal distance discovered
                minimal_paths[neighbor_point] = extended_path

        # Tracing exploration
        if tracer:
            tracer.report()

        return optimum