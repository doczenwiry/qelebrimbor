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

import pyzx

# Suppress warnings regarding case-insensitive filesystem on macOS
os.environ["EXTRA_CLING_ARGS"] = "-Wno-nonportable-include-path"

from ogdf_python import cppinclude, ogdf

cppinclude("ogdf/basic/Graph.h")
cppinclude("ogdf/basic/GraphAttributes.h")
cppinclude("ogdf/basic/graphics.h")


class OGDF:
    @staticmethod
    def from_pyzx_graph(zxg: pyzx.graph.base.BaseGraph) -> tuple[ogdf.Graph, ogdf.GraphAttributes]:
        ogg = ogdf.Graph()
        mapping = {}
        for node in zxg.vertices():
            mapping[node] = ogg.newNode()
        for source, target in zxg.edges():
            ogg.newEdge(mapping[source], mapping[target])

        attributes = ogdf.GraphAttributes(ogg, ogdf.GraphAttributes.all)
        for vertex, node in mapping.items():
            attributes.width[node] = 20.0
            attributes.height[node] = 20.0
            attributes.shape[node] = ogdf.Shape.Ellipse
            attributes.label[node] = str(vertex)
            vertex_type = zxg.type(vertex)
            if vertex_type == pyzx.VertexType.X:
                attributes.fillColor[node] = ogdf.Color(255, 0, 0, 255)
            elif vertex_type == pyzx.VertexType.Z:
                attributes.fillColor[node] = ogdf.Color(0, 0, 255, 255)
            elif vertex_type == pyzx.VertexType.BOUNDARY:
                attributes.fillColor[node] = ogdf.Color(64, 64, 64, 255)
            else:
                attributes.fillColor[node] = ogdf.Color(255, 255, 255, 255)

        return ogg, attributes
