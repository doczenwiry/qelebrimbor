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

import logging

from qelebrimbor.common.components import ZxNode
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.utilities.cycle_basis_analyser import CycleBasisAnalyser
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

console = logging.getLogger(__name__)

class ZxGraphInflaterRings:
    def __init__(self, graph: VolumetricZxGraph):
        self.__graph = graph
        self.__node_realisations = 0
        self.__edge_realisations = 0

    def process(self):
        cycles = CycleBasisAnalyser.decompose_edges(self.__graph)

        console.info(f"Found {len(cycles)} cycles")
        for cycle in cycles:
            console.info(f"> Cycle : {cycle}")