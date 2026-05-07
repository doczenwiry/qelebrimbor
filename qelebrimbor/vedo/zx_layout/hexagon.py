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
from qelebrimbor.core.attributes_zx import NodeId, NodeType
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class HexagonLayout(ZxLayout):
    def __init__(self, graph: VolumetricZxGraph, nodes: list[NodeId], extras: dict[NodeId, tuple[float, float]]):
        self.placements: dict[ZxNode, tuple[float, float]] = {}

        step = 2.0 * np.pi / 6.0
        for node in graph.get_zx_nodes():
            if node.id in nodes:
                rho = 2.0
                theta = nodes.index(node.id) * step
            elif node.id in extras:
                rho, phi = extras[node.id]
                theta = 2.0 * np.pi * phi
            else:
                continue
            x = rho * np.cos(theta)
            y = rho * np.sin(theta)
            self.placements[node] = (x,y)
            boundaries = list(filter(
                lambda bd: graph.has_edge(node.id, bd.id), graph.get_zx_nodes(node_type = NodeType.O)
            ))
            console.debug(f"Node {node} has boundaries : {boundaries}")
            try:
                boundary = next(iter(boundaries))
                bx = (rho + 0.7) * np.cos(theta)
                by = (rho + 0.7) * np.sin(theta)
                self.placements[boundary] = (bx, by)
            except StopIteration:
                pass

    def get_node_placement(self, node: ZxNode) -> tuple[float, float]:
        return self.placements[node] if node in self.placements else (0.0, 0.0)