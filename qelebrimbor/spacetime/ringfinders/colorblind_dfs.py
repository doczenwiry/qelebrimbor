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

from qelebrimbor.core.bg.ring import Ring
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.core.zx.attributes import NodeType
from qelebrimbor.core.colorless.ring import ColorlessRing
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker
from qelebrimbor.spacetime.connectivity.default import DefaultConnectivityTracker
from qelebrimbor.spacetime.colorblind.painter_cycle import PainterZxCycle
from qelebrimbor.spacetime.tracer import SpacetimeTracer, SpacetimeTracingReport

import logging
console = logging.getLogger(__name__)

class RingfinderColorblindDFS:
    def __init__(self,
            graph: VolumetricZxGraph = None,
            connectivity: ConnectivityTracker | None = None,
            branch_and_bound: bool = False,
            reporting: SpacetimeTracingReport | None = None
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

    def find_optimum(self, goal: ZxCycle, maximal_excess: int | None = None) -> Ring | None:
        """
        Search for a Strand connecting the source and target of a Chain with the intermediate nodes along the way.
        WARNING: if there exists no ColorlessPath in spacetime between the source and the target; infinite loop.
        :param goal: The Chain specifying a Strand that must be searched for.
        :param maximal_excess: The maximum number of additional cubes permitted on top of the Manhattan Distance.
        N.B. maximal_excess = None forces the PathfinderDFS to search until it finds a Path.
        :return: A Path or None if no path was found.
        """

        pass
