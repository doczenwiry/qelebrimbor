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

from qelebrimbor.core.bg.ring import Ring
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.spacetime.connectivity.abstract import ConnectivityTracker
from qelebrimbor.spacetime.connectivity.default import DefaultConnectivityTracker
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport


class RingMakerDFS:
    def __init__(
        self,
        graph: VolumetricZxGraph,
        connectivity: ConnectivityTracker | None = None,
        reporting: SpacetimeTracingReport | None = None,
    ):
        self.__graph = graph or VolumetricZxGraph()
        self.__connectivity = connectivity or DefaultConnectivityTracker()
        self.__reporting: SpacetimeTracingReport | None = reporting

    def find_optimum(self, goal: ZxCycle) -> Ring | None:
        if not goal.is_alternating():
            raise Exception(f"RingMakerDFS does not work with non-alternating cycles [goal:{goal}].")

        optimum: Ring | None = None

        return optimum
