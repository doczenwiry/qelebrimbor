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
import itertools
import logging

from qelebrimbor.core.colorless.frenet import FrenetRing, FrenetTwisting
from qelebrimbor.core.components import ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport

console = logging.getLogger(__name__)


class RingfinderColorblindFrenetBFS:
    def __init__(self, graph: VolumetricZxGraph | None = None, reporting: SpacetimeTracingReport | None = None):
        """
        Instantiate a RingfinderColorblindFrenetDFS to search for a Ring of minimal volume suitable for a ZxCycle.
        This approach is based on using Discrete Frenet Frames to only explore essentially different rings
        by keeping track of the twists along the way (cfr. https://arxiv.org/abs/1102.5658).
        :param graph: The VolumetricZxGraph serving as the context for the searches.
        :param reporting: Controls whether to perform tracing of the searches and output as plot(s).
        """
        self.__graph = graph or VolumetricZxGraph()
        self.__reporting = reporting

    @staticmethod
    def __make_specification(goal: ZxCycle) -> list[tuple[ZxNode, EdgeType, int]]:
        """
        Construct a specification of plane flips that will be needed along the Ring in accordance with the ZxCycle.
        :param goal: The ZxCycle specifying (partially) a Ring to be searched for.
        :return:
        """
        # Split every node along the cycle into as many nodes of the same type connected by identity as needed.
        # > Turn node with degree d into (d + d%2) nodes.
        specification: list[tuple[ZxNode, EdgeType, int]] = list()
        for node, edge in zip(goal.nodes, goal.edges):
            # Calculate the number of extra cubes required to accommodate all the legs for the current node.
            cubes_required: int = 1 if node.degree <= 4 else ((node.degree + node.degree % 2) // 2) - 1
            extras: int = cubes_required - 1
            specification.append((node, edge, extras))

        # TODO: deal with padding all the cases with less than 6 cubes.
        cubes_required = sum(extras + 1 for _, _, extras in specification)
        if cubes_required == 4:
            for index in [0, 2]:
                node, edge_type, extras = specification[index]
                specification[index] = (node, edge_type, extras + 1)

        console.info(f"> Expanded goal into : {specification}")

        return specification

    # TODO: prune when a partial colorless ring won't be paintable when it is closed.
    # TODO: identify essentially different colorless rings (missing symmetry: rotation about (+1,+1,+1) axis).
    def find_optimum(self, goal: ZxCycle, maximal_excess: int | None = None) -> FrenetRing | None:
        """
        Search for a Ring whose intermediate cubes can be used to realise the nodes of a ZxCycle.
        WARNING: if there exists no ColorlessRing in spacetime ; infinite loop.
        :param goal: The ZxCycle specifying a Ring that must be searched for.
        :param maximal_excess: The maximum number of additional cubes permitted on top of the Manhattan Distance.
        N.B. maximal_excess = None forces the RingfinderColorblindFrenetDFS to search until it finds a Ring.
        :return: A Ring or None if no ring was found within maximal_excess.
        """
        console.info(f"Searching Ring for {goal}")
        specification = RingfinderColorblindFrenetBFS.__make_specification(goal)

        # Initialize a tracer if tracing has been requested
        # tracer: SpacetimeTracer | None = SpacetimeTracer(reporting=self.__reporting) if self.__reporting else None

        optimum: FrenetRing | None = None
        unrelaxed: list[tuple[int, FrenetRing]] = list()

        heapq.heappush(unrelaxed, (0, FrenetRing()))

        while len(unrelaxed) > 0 and optimum is None:
            heapq.heapify(unrelaxed)
            sections, current = heapq.heappop(unrelaxed)

            console.debug(f"Current : {current}")

            if sections == len(specification):
                if current.closed():
                    optimum = current
                continue

            following_node, following_edge, following_extras = specification[sections]

            # TODO: design a work-around for this exponential growth ...
            if following_extras > 4:
                console.critical(f"Exponential growth of number of flat layouts: {3**following_extras}")

            flats = itertools.product(
                [FrenetTwisting.NONE, FrenetTwisting.ZERO, FrenetTwisting.FULL], repeat=following_extras
            )
            for layout in flats:
                try:
                    extended = current.extend(*layout)
                    heapq.heappush(unrelaxed, (sections + 1, extended.extend(FrenetTwisting.QT_M)))
                    heapq.heappush(unrelaxed, (sections + 1, extended.extend(FrenetTwisting.QT_P)))
                except ValueError:
                    # extension intersects with occupied positions
                    continue

            # TODO: reduce the unrelaxed rings by mirroring
            reduced: list[tuple[int, FrenetRing]] = []
            for sections, ring in unrelaxed:
                if any(other.mirrors(ring) for _, other in reduced):
                    continue
                reduced.append((sections, ring))
            unrelaxed.clear()
            unrelaxed.extend(reduced)

        return optimum
