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
from qelebrimbor.core.colorless.frenet import FrenetRing
from qelebrimbor.core.components import ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport

console = logging.getLogger(__name__)


class RingfinderColorblindFrenetDFS:
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
    def __make_specification(goal: ZxCycle) -> tuple[list[ZxNode], list[EdgeType], list[bool]]:
        """
        Construct a specification of plane flips that will be needed along the Ring in accordance with the ZxCycle.
        :param goal: The ZxCycle specifying (partially) a Ring to be searched for.
        :return:
        """
        # Split every node along the cycle into as many nodes of the same type connected by identity as needed.
        # > Turn node of degree d into (d // 2) + (d % 2) nodes.
        nodes: list[ZxNode] = []
        edges: list[EdgeType] = []
        for node, edge in zip(goal.nodes, goal.edges):
            outer_legs: int = node.degree - 2
            nodes.append(node)

            # Calculate the number of extra nodes required to accommodate all the legs of the current node.
            extras: int = (outer_legs // 2) + (outer_legs % 2) - 1
            for _ in range(extras):
                nodes.append(ZxNode(id=-1, type=node.type))
                edges.append(EdgeType.IDENTITY)

            edges.append(edge.type)

        if len(nodes) == 4:
            for index in [0, 3]:
                nodes.insert(index, ZxNode(id=-1, type=nodes[0].type))
                edges.insert(index, EdgeType.IDENTITY)

        twists: list[bool] = list()
        expanded_length = len(nodes)
        specification: str = ""
        for index in range(expanded_length):
            is_hadamard = edges[index] == EdgeType.HADAMARD
            same_colors = nodes[index] == nodes[(index + 1) % expanded_length]
            twist = is_hadamard == same_colors
            twists.append(twist)
            specification += "T" if twist else "S"

        console.info(f"> Expanded goal into : {nodes} {edges} [specification:{specification}]")

        return nodes, edges, twists

    # TODO: prune when a partial colorless ring won't be paintable when it is closed.
    # TODO: identify essentially different colorless rings (missing symmetry: rotation about (+1,+1,+1) axis).
    def find_optimum(self, goal: ZxCycle, maximal_excess: int | None = None) -> Ring | None:
        """
        Search for a Ring whose intermediate cubes can be used to realise the nodes of a ZxCycle.
        WARNING: if there exists no ColorlessRing in spacetime ; infinite loop.
        :param goal: The ZxCycle specifying a Ring that must be searched for.
        :param maximal_excess: The maximum number of additional cubes permitted on top of the Manhattan Distance.
        N.B. maximal_excess = None forces the RingfinderColorblindFrenetDFS to search until it finds a Ring.
        :return: A Ring or None if no ring was found within maximal_excess.
        """
        console.info(f"Searching Ring for {goal}")
        nodes, edges, twists = RingfinderColorblindFrenetDFS.__make_specification(goal)

        # Initialize a tracer if tracing has been requested
        # tracer: SpacetimeTracer | None = SpacetimeTracer(reporting=self.__reporting) if self.__reporting else None

        optimum: Ring | None = None
        unrelaxed: list[FrenetRing] = list()

        heapq.heappush(unrelaxed, FrenetRing())

        while len(unrelaxed) > 0:
            heapq.heapify(unrelaxed)
            current = heapq.heappop(unrelaxed)

            if twists[current.length]:
                # Introduce a twist
                pass
            else:
                # Introduce a straight
                pass

        return optimum
