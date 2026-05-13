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

from qelebrimbor.analysis.components import ConnectedComponentsAnalyser
from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType, NodeType
from qelebrimbor.core.zx.cycle import ZxCycle


class VolumetricZxGraphAnalyser:
    @staticmethod
    def analyse(graph: VolumetricZxGraph, minimal: bool = False, plot: bool = False) -> list[ZxCycle]:
        node_counts: dict[NodeType, int] = {
            nodetype: len(list(graph.get_zx_nodes(node_type=nodetype)))
            for nodetype in NodeType
            if graph.number_of_zx_nodes(node_type=nodetype) > 0
        }
        breakdown = ",".join(str(nodetype) + ":" + str(count) for nodetype, count in node_counts.items())
        print(f"> Number of nodes : {graph.number_of_nodes()} [{breakdown}]")

        edge_counts = {
            edgetype: len(list(graph.get_zx_edges(edge_type=edgetype)))
            for edgetype in EdgeType
            if graph.number_of_zx_edges(edge_type=edgetype) > 0
        }
        breakdown = ",".join(str(edgetype) + ":" + str(count) for edgetype, count in edge_counts.items())
        print(f"> Number of edges : {graph.number_of_edges()} [{breakdown}]")

        print(f"> Number of qubits : {len(graph.get_zx_qubits())}")
        print(f"> Number of layers : {len(graph.get_zx_layers())}")

        zx_cycles = CycleAnalyser.analyse(graph=graph, minimal=minimal, plot=plot)
        _, _ = ConnectedComponentsAnalyser.analyse(graph=graph, plot=plot)

        return zx_cycles
