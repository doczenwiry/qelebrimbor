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

from qelebrimbor.core.components import ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.vedo.zx_layout.abstract import ZxLayout


class CircuitLayout(ZxLayout):
    def __init__(self, vzx: VolumetricZxGraph, vertical: bool = True):
        self.placements = dict()

        for node in vzx.get_zx_nodes():
            qubit = node.qubit
            layer = node.layer

            self.placements[node] = (qubit, layer) if vertical else (layer, qubit)

    def get_node_placement(self, node: ZxNode) -> tuple[float, float]:
        return self.placements[node]