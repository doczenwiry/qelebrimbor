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

from qelebrimbor.core.common import ZxCycle
from qelebrimbor.core.attributes_zx import NodeType, EdgeType
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.analysis.components import ConnectedComponentsAnalyser


class VolumetricZxGraphAnalyser:
    @staticmethod
    def analyse(graph: VolumetricZxGraph, plot: bool = False) -> tuple[list[ZxCycle], int]:
        print(f"Analysis of the input ZX graph")

        node_counts: dict[NodeType, int] = {
            nodetype : len(list(graph.get_zx_nodes(node_type = nodetype)))
            for nodetype in NodeType
        }
        breakdown = ",".join(str(nodetype) + ':' + str(count) for nodetype, count in node_counts.items())
        print(f"> Number of ZX nodes : {graph.number_of_nodes()} [{breakdown}]")

        edge_counts = {
            edgetype : len(list(graph.get_zx_edges(edge_type = edgetype)))
            for edgetype in EdgeType
        }
        breakdown = ",".join(str(edgetype) + ':' + str(count) for edgetype, count in edge_counts.items())
        print(f"> Number of ZX edges : {graph.number_of_edges()} [{breakdown}]")

        print(f"> Number of qubits : {len(graph.get_zx_qubits())}")
        print(f"> Number of layers : {len(graph.get_zx_layers())}")

        zx_cycles = CycleAnalyser.analyse(graph = graph, minimal = False, plot = plot)
        component_count, largest_component = ConnectedComponentsAnalyser.analyse(graph = graph, plot = plot)

        if component_count > 1:
            print("WARNING: The input ZX-graph has more than one connected component.")

        return zx_cycles, component_count