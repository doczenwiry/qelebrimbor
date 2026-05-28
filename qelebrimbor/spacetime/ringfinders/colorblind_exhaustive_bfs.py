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
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import NodeType
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.helpers.spacetime import SpacetimeHelper, Step
from qelebrimbor.spacetime.colorblind.painter_cycle import PainterZxCycle
from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker
from qelebrimbor.spacetime.connectivity.default import DefaultConnectivityTracker
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

console = logging.getLogger(__name__)


class RingfinderColorblindExhaustiveBFS:
    def __init__(
        self,
        graph: VolumetricZxGraph | None = None,
        connectivity: ConnectivityTracker | None = None,
        reporting: SpacetimeTracingReport | None = None,
    ):
        """
        Instantiate a RingfinderColorblindBFS to search for shortest valid Ring suitable for ZxCycle.
        :param graph: The VolumetricZxGraph serving as the context for the searches.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        Proof of the possibility would be nice. Refutation thereof would be better.
        :param reporting: Controls whether to perform tracing of the searches and output as plot(s).
        """
        self.__graph = graph or VolumetricZxGraph()
        self.__connectivity: ConnectivityTracker = connectivity or DefaultConnectivityTracker()
        self.__reporting = reporting

    def find_optimum(self, goal: ZxCycle, maximal_excess: int | None = None) -> list[Ring]:
        rings = list()

        colorless_rings = self.__find_essentially_different_colorless_rings(goal, maximal_excess)

        console.info(f"Essentially different colorless rings found : {len(colorless_rings)}")
        for colorless in colorless_rings:
            console.info(f"> Ring : {colorless}")

        for colorless in colorless_rings:
            rings.extend(PainterZxCycle.all_painted(colorless, goal))

        return rings

    # TODO: prune when a partial colorless ring won't be paintable when it is closed.
    # TODO: identify essentially different colorless rings (missing symmetry: rotation about (+1,+1,+1) axis).
    def __find_essentially_different_colorless_rings(
        self, goal: ZxCycle, maximal_excess: int | None = None
    ) -> list[ColorlessRing]:
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

        node_types = list(map(lambda node: node.type, nodes))

        if any(nt == NodeType.O or nt == NodeType.Y for nt in node_types):
            raise Exception("Node restrictions cannot contain NodeType.O or NodeType.Y.")

        node_type_nr = len(node_types)

        # Maximal volume of acceptable strands
        maximal_volume = goal.length + maximal_excess if maximal_excess is not None else None
        extra = f"[max volume={maximal_volume}]" if maximal_volume is not None else ""

        # Initialize a tracer if tracing has been requested
        tracer: SpacetimeTracer | None = SpacetimeTracer(reporting=self.__reporting) if self.__reporting else None

        # Main variables of the DFS
        optima: list[ColorlessRing] = []
        unrelaxed: list[ColorlessRing] = []

        initial: ColorlessRing = ColorlessRing()
        initial.append(SpacetimeHelper.ORIGIN)
        initial.append(SpacetimeHelper.YP)
        initial.append(SpacetimeHelper.YP + SpacetimeHelper.XP)
        heapq.heappush(unrelaxed, initial)

        if tracer:
            tracer.add_node(initial.anchor, label=str(initial.anchor))
            tracer.add_node(SpacetimeHelper.YP)
            tracer.add_edge(initial.anchor, SpacetimeHelper.YP)
            tracer.add_node(SpacetimeHelper.YP + SpacetimeHelper.XP)
            tracer.add_edge(SpacetimeHelper.YP, SpacetimeHelper.YP + SpacetimeHelper.XP)

        console.info(f"Searching for ring for {goal} {extra}")

        while len(unrelaxed) > 0:
            # Restore the heap invariant
            heapq.heapify(unrelaxed)
            partial: ColorlessRing = heapq.heappop(unrelaxed)

            # Discard the current ring if it is longer than what is acceptable.
            if maximal_volume and maximal_volume < partial.volume:
                continue

            console.info(f"> Current [V:{partial.volume}] : {partial}")

            # Check whether the goal has been accomplished
            if partial.closed() and partial.volume >= node_type_nr:
                # Ignore the incoming path if it doesn't line up with a port of the final cube.
                console.debug(f"Candidate ColorlessStrand [{partial.volume}] : {partial}")
                console.debug(f"> Paintable {partial} by {goal} ? {PainterZxCycle.paintable(partial, goal)}")

                if PainterZxCycle.paintable(partial, goal):
                    # Tracing exploration
                    if tracer:
                        tracer.add_edge(partial.terminal, partial.anchor)

                    console.debug(f"Optimum found : {partial}")
                    optima.append(partial)
                    continue

            # Restrict the outgoing paths to lie in the reach of the CubeKind of the start.
            if partial.volume >= 3:
                constellation = SpacetimeHelper.get_constellation(position=partial.terminal)
            else:
                constellation = [SpacetimeHelper.XP]

            console.info(f"> {partial.terminal} has constellation : {constellation}")

            for adjacent in constellation:
                # Ignore adjacent with a step in the negative direction with no prior step in the positive direction.
                step = adjacent - partial.terminal
                if step != step.abs() and Step(step.abs()) not in partial.steps:
                    console.debug(f">> {step} vs {partial.steps}")
                    continue

                # Ignore neighbor if it introduces a loop
                if partial.occupies(adjacent):
                    console.debug(f">> partial occupies {adjacent}")
                    continue

                # Ignore neighbor if its position is already occupied in spacetime
                if self.__graph.spacetime.occupied(adjacent):
                    console.debug(f">> spacetime occupied at {adjacent}")
                    continue

                # Ignore neighbor if occluding the position breaks connectivity
                # if not self.__connectivity.preserved(current.terminal, adjacent, adjacent):
                #     continue

                # Tracing exploration
                if tracer:
                    tracer.add_node(adjacent)
                    tracer.add_edge(partial.terminal, adjacent)

                extended = partial.extend(adjacent)
                console.debug(f">> Extended : {extended}")

                # Add the extended colorless ring to the list of unrelaxed
                heapq.heappush(unrelaxed, extended)

        console.info("Optima found :")
        for optimum in optima:
            console.info(f"> {optimum.steps}")

        # Tracing exploration
        if tracer:
            tracer.report()

        # TODO: post-process to only keep essentially different rings.

        return optima
