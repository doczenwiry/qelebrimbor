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

from qelebrimbor.formats.ogdf import OGDF

# Suppress warnings regarding case-insensitive filesystem on macOS
os.environ["EXTRA_CLING_ARGS"] = "-Wno-nonportable-include-path"

from ogdf_python import cppinclude, ogdf

from qelebrimbor.core.components import ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.zx_layout.abstract import ZxLayout

cppinclude("ogdf/orthogonal/OrthoLayout.h")
cppinclude("ogdf/planarity/PlanarizationLayout.h")
cppinclude("ogdf/planarity/EmbedderMinDepthMaxFaceLayers.h")


class OrthogonalLayout(ZxLayout):
    def __init__(self, graph: VolumetricZxGraph, scale: float = 1.0):
        # Convert graph from VZX to OGDF for running layout algorithm
        ogg, attributes, reverse = OGDF.from_vzx_graph(graph)

        # Prepare algorithm to compute coordinates of ZX-nodes
        algorithm = ogdf.PlanarizationLayout()

        layout = ogdf.OrthoLayout()
        layout.separation(scale)
        layout.__python_owns__ = False  # Needed to avoid C++ segmentation fault when object is destroyed
        algorithm.setPlanarLayouter(layout)

        embedder = ogdf.EmbedderMinDepthMaxFaceLayers()
        embedder.__python_owns__ = False  # Needed to avoid C++ segmentation fault when object is destroyed
        algorithm.setEmbedder(embedder)

        algorithm.call(attributes)

        # Scale down the positions and populate placements dictionary
        self.placements: dict[ZxNode, tuple[float, float]] = dict()
        for ogg_node, vzx_node in reverse.items():
            self.placements[vzx_node] = (scale * attributes.x[ogg_node], scale * attributes.y[ogg_node])

    def get_node_placement(self, node: ZxNode) -> tuple[float, float]:
        return self.placements[node]
