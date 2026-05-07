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

import numpy as np

from qelebrimbor.core.components import ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout, Placement


class CycleLayout(ZxLayout):
    def __init__(self, ring: VolumetricZxGraph):
        self.placements: dict[ZxNode, Placement] = {}

        rho = 2.0
        step = (2.0 * np.pi) / ring.number_of_nodes()
        phi = np.pi - step / 2.0
        for node in ring.get_zx_nodes():
            x = rho * np.cos(phi)
            y = rho * np.sin(phi)
            self.placements[node] = (x, y)
            phi -= step

    def get_node_placement(self, node: ZxNode) -> Placement:
        return self.placements[node]