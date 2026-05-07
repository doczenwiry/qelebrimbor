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

from qelebrimbor.core.components import BgCube
from qelebrimbor.core.attributes_zx import NodeType, EdgeType

from qelebrimbor.spacetime.fabric import SpacetimeFabric
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)


class RingfinderDFS:
    def __init__(self,
            graph: VolumetricZxGraph = None,
            ports_tracker: OpenPortsTracker | None = None,
            branch_and_bound: bool = False,
            tracing: SpacetimeTracingReport | None = None
    ):
        """
        Create a PathfinderDFS to search for optimal paths between cubes in spacetime.
        :param graph: The VolumetricZxGraph serving as the context for the search.
        :param branch_and_bound: Controls whether a Branch-and-Bound is performed to improve the first path found.
        This will incur an additional computational cost that may or may not fall into super-exponential territory.
        Proof of the possibility would be nice. Refutation thereof would be better.
        :param tracing: Controls whether a tracing/reporting of all vertices explored is performed.
        """
        self.__graph = graph if graph else VolumetricZxGraph()
        self.__ports_tracker = ports_tracker if ports_tracker else OpenPortsTracker(self.__graph)
        self.__spacetime = graph.spacetime if graph else SpacetimeFabric()
        self.__branch_and_bound = branch_and_bound
        self.__tracing = tracing

    def find_optimum(self,
            source: BgCube, target: BgCube,
            restrictions: tuple[list[NodeType], list[EdgeType]] | None = None,
            maximal_excess: int = None
    ):
        pass