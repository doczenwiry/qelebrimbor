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

from qelebrimbor.common.components import ZxNode
from qelebrimbor.common.attributes_zx import NodeId
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph


class ManualLayout(ZxLayout):
    def __init__(self, graph: VolumetricZxGraph, placements: dict[NodeId, tuple[float, float]]):
        self.placements: dict[ZxNode, tuple[float, float]] = dict()
        for node_id in placements:
            self.placements[graph.get_zx_node(node_id)] = placements[node_id]

    def get_node_placement(self, node: ZxNode) -> tuple[float, float]:
        return self.placements[node]