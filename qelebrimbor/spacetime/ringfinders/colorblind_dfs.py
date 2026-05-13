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
import logging

from qelebrimbor.core.bg.ring import Ring
from qelebrimbor.core.colorless.ring import ColorlessRing
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import NodeType
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.spacetime.colorblind.painter_cycle import PainterZxCycle
from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker
from qelebrimbor.spacetime.connectivity.default import DefaultConnectivityTracker
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

console = logging.getLogger(__name__)


class RingfinderColorblindDFS:
    def __init__(
        self,
        graph: VolumetricZxGraph | None = None,
        connectivity: ConnectivityTracker | None = None,
        branch_and_bound: bool = False,
        reporting: SpacetimeTracingReport | None = None,
    ):
        """
        Instantiate a RingfinderColorblindDFS to search for shortest valid Ring suitable for ZxCycle.
        :param graph: The VolumetricZxGraph serving as the context for the searches.
        :param branch_and_bound: Controls whether a Branch-and-Bound is performed to improve the first solution found.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        Proof of the possibility would be nice. Refutation thereof would be better.
        :param reporting: Controls whether to perform tracing of the searches and output as plot(s).
        """
        self.__graph = graph or VolumetricZxGraph()
        self.__connectivity: ConnectivityTracker = connectivity or DefaultConnectivityTracker()

        self.__branch_and_bound = branch_and_bound
        self.__reporting = reporting

    @staticmethod
    def heuristic(current: ColorlessRing, node_types: list[NodeType]) -> int:
        return max(len(node_types), current.distance)

    def find_optimum(self, goal: ZxCycle, maximal_excess: int | None = None) -> Ring | None:
        """
        Search for a Ring whose intermediate cubes can be used to realise the nodes of a ZxCycle.
        WARNING: if there exists no ColorlessRing in spacetime ; infinite loop.
        :param goal: The ZxCycle specifying a Ring that must be searched for.
        :param maximal_excess: The maximum number of additional cubes permitted on top of the Manhattan Distance.
        N.B. maximal_excess = None forces the RingfinderColorblindDFS to search until it finds a Ring.
        :return: A Ring or None if no ring was found.
        """
        # Prepare the parameters for the search
        nodes = list(goal.nodes)

        node_types = list(map(lambda node: node.color, nodes))

        if any(nt == NodeType.O or nt == NodeType.Y for nt in node_types):
            raise Exception("Node restrictions cannot contain NodeType.O or NodeType.Y.")

        node_type_nr = len(node_types)

        # Maximal volume of acceptable strands
        maximal_volume = goal.length + maximal_excess if maximal_excess is not None else None
        extra = f"[max volume={maximal_volume}]" if maximal_volume is not None else ""

        # Initialize a tracer if tracing has been requested
        tracer: SpacetimeTracer | None = (
            SpacetimeTracer(pruning=self.__branch_and_bound, reporting=self.__reporting) if self.__reporting else None
        )

        # Main variables of the DFS
        optimum: Ring | None = None
        unrelaxed: list[tuple[int, ColorlessRing]] = []

        initial = ColorlessRing(anchor=Coordinates(0, 0, 0))
        heapq.heappush(unrelaxed, (RingfinderColorblindDFS.heuristic(initial, node_types), initial))

        if tracer:
            tracer.add_node(initial.anchor, label=str(initial.anchor))

        console.info(f"Searching for ring for {goal} {extra}")

        while len(unrelaxed) > 0 and (self.__branch_and_bound or optimum is None):
            # Restore the heap invariant
            heapq.heapify(unrelaxed)
            remaining_distance: int
            current: ColorlessRing
            remaining_distance, current = heapq.heappop(unrelaxed)

            terminal = current.terminal

            # Discard the current_path if it is longer than what is acceptable.
            if maximal_volume and maximal_volume < current.volume:
                continue

            # Branch-and-bound
            if self.__branch_and_bound and optimum is not None:
                # Compute the project length based on the heuristic
                projected_volume = current.volume + remaining_distance
                if optimum.volume() <= projected_volume:
                    if tracer:
                        tracer.prune_node(terminal)
                    continue

            console.debug(f"{'>' * (current.volume + 1)} Current : {current}")

            # Check whether the goal has been accomplished
            if current.closed() and current.volume >= node_type_nr:
                # Ignore the incoming path if it doesn't line up with a port of the final cube.
                console.info(f"Candidate ColorlessStrand [{current.volume}] : {current}")

                if PainterZxCycle.paintable(current, goal):
                    # Tracing exploration
                    if tracer:
                        tracer.add_edge(current.terminal, current.anchor)

                    # Update the optimum only if it improves our current knowledge
                    if optimum is None or current.volume < optimum.volume():
                        optimum = PainterZxCycle.paint(current, goal)

            # Restrict the outgoing paths to lie in the reach of the CubeKind of the start.
            constellation = SpacetimeHelper.get_constellation(position=terminal)

            console.debug(f"{'>' * (current.volume + 2)} {terminal} has constellation : {constellation}")

            for adjacent in constellation:
                # Ignore neighbor if it introduces a loop
                if current.occupies(adjacent):
                    continue

                # Ignore neighbor if its position is already occupied in spacetime
                if self.__graph.spacetime.occupied(adjacent):
                    continue

                # Ignore neighbor if occluding the position breaks connectivity
                # if not self.__connectivity.preserved(current.terminal, adjacent, adjacent):
                #     continue

                # Tracing exploration
                if tracer:
                    tracer.add_node(adjacent)
                    tracer.add_edge(terminal, adjacent)

                extended = current.extend(adjacent)

                # Filtering out the neighbor from unrelaxed
                unrelaxed = [vertex for vertex in unrelaxed if vertex[1].terminal != adjacent]

                # Compute the minimal manhattan length required to connect neighbor to target (HEURISTIC).
                unrelaxed.append(
                    (
                        RingfinderColorblindDFS.heuristic(extended, node_types[extended.volume :]),
                        extended,
                    )
                )

        console.info(f"Optimum found : {optimum}")

        # Tracing exploration
        if tracer:
            tracer.report()

        return optimum
