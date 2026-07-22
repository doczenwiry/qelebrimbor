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
import os
from collections import defaultdict
from ctypes import c_int

os.environ["EXTRA_CLING_ARGS"] = "-Wno-nonportable-include-path"

import pyzx.graph.base
from ogdf_python import cppinclude, ogdf

from qelebrimbor.formats.ogdf import OGDF
from qelebrimbor.formats.preprocessing.abstract import Preprocessor

cppinclude("ogdf/planarity/PlanRep.h")
cppinclude("ogdf/planarity/SubgraphPlanarizer.h")

console = logging.getLogger(__name__)


class NoMoreThanFourEdges(Preprocessor):
    @staticmethod
    def compute_splittings(zxg: pyzx.graph.base.BaseGraph) -> dict[int, list[list[int]]]:
        ogg, _, reverse = OGDF.from_pyzx_graph(zxg)
        sg_planarizer = ogdf.SubgraphPlanarizer()
        planarized = ogdf.PlanRep(ogg)
        sg_planarizer.call(planarized, 0, c_int(0))

        splittings: dict[int, list[list[int]]] = defaultdict(list)

        for node in planarized.nodes:
            if node.degree() <= 4:
                continue

            vertex = reverse[planarized.original(node)]
            ordered_edges = [adj.theEdge() for adj in node.adjEntries]
            degree = len(ordered_edges)
            required_spiders = ((degree + (degree % 2)) // 2) - 1
            # Connect the extras
            kept = []
            for idx, edge in enumerate(ordered_edges[:3]):
                orig = planarized.original(edge)
                kept.append(reverse[orig.target() if orig.source() == planarized.original(node) else orig.source()])
            splittings[vertex].append(kept)
            for idx in range(required_spiders - 1):
                inherited = []
                # Edge[3 + idx] will be attached to extra
                edge = planarized.original(ordered_edges[3 + idx])
                inherited.append(
                    reverse[edge.target() if edge.source() == planarized.original(node) else edge.source()]
                )
                # Edge[degree - 1 - idx] will be attached to extra
                edge = planarized.original(ordered_edges[degree - 1 - idx])
                inherited.append(
                    reverse[edge.target() if edge.source() == planarized.original(node) else edge.source()]
                )
                # Update splittings with inheritance
                splittings[vertex].append(inherited)
            # We need to attach the edge[3 + required_spiders - 1] to the last extra vertex
            if degree % 2 == 0:
                edge = planarized.original(ordered_edges[3 + required_spiders - 1])
                splittings[vertex][-1].append(
                    reverse[edge.target() if edge.source() == planarized.original(node) else edge.source()]
                )

        return splittings

    @staticmethod
    def process(graph: pyzx.graph.base.BaseGraph) -> pyzx.graph.base.BaseGraph:
        reduced = graph.clone()

        splittings = NoMoreThanFourEdges.compute_splittings(reduced)
        console.debug(f"Splittings : {splittings}")

        for vertex, groups in splittings.items():
            console.debug(f"Vertex {vertex} : {groups}")
            preceding = vertex
            for neighbours in groups[1:]:
                # Add an extra vertex connected the one we are splitting
                extra = reduced.add_vertex(
                    ty=reduced.type(vertex), qubit=reduced.qubit(vertex), row=reduced.qubit(vertex)
                )
                reduced.add_edge((preceding, extra))
                # Move the selected edges to the extra vertex
                console.debug(f"> Passing to {extra} : {neighbours}")
                for other in neighbours:
                    zx_edge_type = reduced.edge_type(reduced.edge(vertex, other))
                    reduced.remove_edge((vertex, other))
                    reduced.add_edge((extra, other), zx_edge_type)
                preceding = extra

        return reduced
