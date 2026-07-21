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

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import NodeType

# Suppress warnings regarding case-insensitive filesystem on macOS
os.environ["EXTRA_CLING_ARGS"] = "-Wno-nonportable-include-path"

from ogdf_python import cppinclude, ogdf

cppinclude("ogdf/basic/Graph.h")
cppinclude("ogdf/basic/GraphAttributes.h")
cppinclude("ogdf/basic/graphics.h")


class OGDF:
    __VERTEX_COLORS = {
        pyzx.VertexType.X: ogdf.Color(255, 0, 0, 255),
        pyzx.VertexType.Z: ogdf.Color(0, 0, 255, 255),
        pyzx.VertexType.BOUNDARY: ogdf.Color(64, 64, 64, 255),
    }

    @staticmethod
    def from_pyzx_graph(zxg: pyzx.graph.base.BaseGraph) -> tuple[ogdf.Graph, ogdf.GraphAttributes, dict]:
        # Convert the PyZX graph to an OGDF graph
        ogg = ogdf.Graph()
        mapping = {}
        reverse = {}
        for vertex in zxg.vertices():
            node = ogg.newNode()
            mapping[vertex] = node
            reverse[node] = vertex
        for source, target in zxg.edges():
            ogg.newEdge(mapping[source], mapping[target])

        attributes = ogdf.GraphAttributes(ogg, ogdf.GraphAttributes.all)

        for vertex, node in mapping.items():
            # Only style the nodes that correspond to a vertex in the original graph
            vertex_type = zxg.type(vertex)
            attributes.fillColor[node] = OGDF.__VERTEX_COLORS.get(vertex_type, ogdf.Color(255, 255, 255, 255))

            attributes.label[node] = str(vertex)
            attributes.width[node] = 0.75 if vertex_type == pyzx.VertexType.BOUNDARY else 1.0
            attributes.height[node] = 0.75 if vertex_type == pyzx.VertexType.BOUNDARY else 1.0
            attributes.shape[node] = ogdf.Shape.Ellipse

        undirected = getattr(ogdf.EdgeArrow, "None")
        for edge in ogg.edges:
            attributes.arrowType[edge] = undirected

        return ogg, attributes, reverse

    @staticmethod
    def from_vzx_graph(vzx: VolumetricZxGraph) -> tuple[ogdf.Graph, ogdf.GraphAttributes, dict]:
        # Convert the VZX graph to an OGDF graph
        ogg = ogdf.Graph()
        mapping = {}
        reverse = {}
        for vertex in vzx.get_zx_nodes():
            node = ogg.newNode()
            mapping[vertex] = node
            reverse[node] = vertex
        for edge in vzx.get_zx_edges():
            ogg.newEdge(mapping[edge.source], mapping[edge.target])

        attributes = ogdf.GraphAttributes(ogg, ogdf.GraphAttributes.all)

        for vertex, node in mapping.items():
            # Only style the nodes that correspond to a vertex in the original graph
            attributes.fillColor[node] = OGDF.__VERTEX_COLORS.get(vertex.type, ogdf.Color(255, 255, 255, 255))

            attributes.label[node] = str(vertex)
            attributes.width[node] = 0.75 if vertex.type == NodeType.O else 1.0
            attributes.height[node] = 0.75 if vertex.type == NodeType.O else 1.0
            attributes.shape[node] = ogdf.Shape.Ellipse

        undirected = getattr(ogdf.EdgeArrow, "None")
        for edge in ogg.edges:
            attributes.arrowType[edge] = undirected

        return ogg, attributes, reverse
