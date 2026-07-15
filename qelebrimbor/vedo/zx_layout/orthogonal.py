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

import os

# Suppress warnings regarding case-insensitive filesystem on macOS
os.environ["EXTRA_CLING_ARGS"] = "-Wno-nonportable-include-path"

from ogdf_python import cppinclude, ogdf

from qelebrimbor.core.components import ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout

cppinclude("ogdf/basic/Graph.h")
cppinclude("ogdf/basic/GraphAttributes.h")
cppinclude("ogdf/planarity/PlanarizationLayout.h")
cppinclude("ogdf/orthogonal/OrthoLayout.h")


class OrthogonalLayout(ZxLayout):
    def __init__(self, graph: VolumetricZxGraph, scale: float = 1.0):
        # Convert graph from VZX to OGDF for running layout algorithm
        og = ogdf.Graph()
        mapping = {}
        for node in graph.get_zx_nodes():
            mapping[node] = og.newNode()
        for edge in graph.get_zx_edges():
            og.newEdge(mapping[edge.source], mapping[edge.target])
        attributes = ogdf.GraphAttributes(og, ogdf.GraphAttributes.all)
        for node, o_node in mapping.items():
            attributes.width[o_node] = 1.0
            attributes.height[o_node] = 1.0
            attributes.label[o_node] = f"{node.type.name}{node.id}"

        # Prepare algorithm to compute coordinates of ZX-nodes
        algorithm = ogdf.PlanarizationLayout()
        layout = ogdf.OrthoLayout()
        layout.separation(1.0)
        layout.cOverhang(0.0)
        layout.__python_owns__ = False  # Needed to avoid C++ segmentation fault when object is destroyed
        algorithm.setPlanarLayouter(layout)

        algorithm.call(attributes)

        # Snap to unit coordinates on a Manhattan Grid
        coordinates_x = {raw: raw for idx, raw in enumerate(set(map(lambda o: attributes.x[o], mapping.values())))}
        coordinates_y = {raw: raw for idx, raw in enumerate(set(map(lambda o: attributes.y[o], mapping.values())))}

        # Scale down the positions and populate placements dictionary
        self.placements: dict[ZxNode, tuple[float, float]] = dict()
        for node, o_node in mapping.items():
            coordinate_x = scale * coordinates_x[attributes.x[o_node]]
            coordinate_y = scale * coordinates_y[attributes.y[o_node]]
            # print(f"Node {node} @ ({coordinate_x},{coordinate_y})")
            self.placements[node] = (coordinate_x, coordinate_y)

    def get_node_placement(self, node: ZxNode) -> tuple[float, float]:
        return self.placements[node]
