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
from collections import defaultdict

import networkx
import networkx as nx
import pyzx

from qelebrimbor.core.volumetric_zx_graph import LayerTransition, VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType, LayerId, NodeId, NodeType, QubitId

console = logging.getLogger(__name__)


class PYZX:
    @staticmethod
    def into_file(graph: pyzx.graph.base.BaseGraph, filepath: str, layout: dict[int, tuple[float, float]]) -> None:
        placed_graph = graph.clone()

        for node, (x, y) in layout.items():
            placed_graph.set_row(node, x)
            placed_graph.set_qubit(node, y)

        with open(filepath, "w") as file:
            file.write(placed_graph.to_json())

    @staticmethod
    def from_file(filepath: str) -> pyzx.graph.base.BaseGraph:
        with open(filepath, "r") as file:
            return pyzx.Graph().from_json(file.read())

    @staticmethod
    def get_planar_layout(
        graph: pyzx.graph.base.BaseGraph, planar_scale: float = 1.0
    ) -> dict[int, tuple[float, float]]:
        layout: dict[int, tuple[float, float]] = dict()

        nxg = PYZX.into_networkx_graph(graph)
        nx_layout = nx.spring_layout(nxg, k=0.5, iterations=200, scale=planar_scale)
        for node_id, position in nx_layout.items():
            x, y = position
            layout[node_id] = (y, x)

        return layout

    @staticmethod
    def get_circuit_layout(graph: VolumetricZxGraph, planar_scale: float = 1.0) -> dict[int, tuple[float, float]]:
        layout: dict[int, tuple[float, float]] = dict()

        layer_qubit_information_missing = len(graph.get_zx_qubits()) == 0 or len(graph.get_zx_layers()) == 0
        # A PyZX graph obtained from a circuit has edges whose endpoints EITHER have the same layer OR the same qubit
        non_circuit_pyzx_graph = any(
            edge.source.layer != edge.target.layer and edge.source.qubit != edge.target.qubit
            for edge in graph.get_zx_edges()
        )

        if (layer_qubit_information_missing or non_circuit_pyzx_graph) and nx.is_planar(graph.blockgraph):
            for cube_id, coordinates in nx.planar_layout(graph.blockgraph, scale=planar_scale).items():
                layout[cube_id] = tuple(coordinates)
        else:
            # Compute the coordinates of the layers taking into account the extra nodes added to realise edges
            layer_coordinates: dict[LayerId, float] = defaultdict(int)
            current_coordinate = -1.0
            for layer in graph.get_zx_layers():
                minimal_coordinate = current_coordinate + 1.0
                for edge in graph.get_zx_edges(layered=(layer, LayerTransition.LOWER)):
                    previous = edge.source if edge.source.layer < edge.target.layer else edge.target
                    minimal_coordinate = max(
                        minimal_coordinate,
                        layer_coordinates[previous.layer] + edge.number_of_pipes,
                    )
                    console.debug(
                        f"> {edge} [{edge.source.realising_cube}/{edge.target.realising_cube}] yields {minimal_coordinate}"  # noqa: E501
                    )
                current_coordinate = minimal_coordinate
                layer_coordinates[layer] = current_coordinate
                console.debug(f"Layer {layer} : {current_coordinate}")

            # Compute the coordinates of the qubits taking into account the extra nodes added to realise edges
            qubit_coordinates: dict[QubitId, float] = defaultdict(int)
            current_coordinate = -1.0
            for qubit in graph.get_zx_qubits():
                minimal_coordinate = current_coordinate + 1.0
                for node in graph.get_zx_nodes(qubit=qubit):
                    for neighbor in graph.get_zx_neighbors(node, transition=LayerTransition.INTRA):
                        edge = graph.get_zx_edge(node.id, neighbor.id)
                        previous = node if node.qubit < neighbor.qubit else neighbor
                        minimal_coordinate = max(
                            minimal_coordinate,
                            qubit_coordinates[previous.qubit] + edge.number_of_pipes,
                        )
                current_coordinate = minimal_coordinate
                qubit_coordinates[qubit] = current_coordinate
                console.debug(f"Qubit {qubit} : {current_coordinate}")

            # Compute the placement of the nodes of the input ZX-graph
            for node in filter(lambda nd: nd.is_realised(), graph.get_zx_nodes()):
                layout[node.realising_cube.id] = (
                    layer_coordinates[node.layer],
                    qubit_coordinates[node.qubit],
                )
                console.debug(f"Layout {node.realising_cube} : {layout[node.realising_cube.id]}")

            # Compute the placement of the extra nodes added to realise the edges of the input ZX-graph
            for edge in filter(lambda ed: ed.is_realised(), graph.get_zx_edges()):
                if edge.source.layer == edge.target.layer:
                    start_qubit: QubitId = min(edge.source.qubit, edge.target.qubit)
                    final_qubit: QubitId = max(edge.source.qubit, edge.target.qubit)
                    offset = qubit_coordinates[start_qubit]
                    step = abs(qubit_coordinates[final_qubit] - qubit_coordinates[start_qubit]) / float(
                        edge.number_of_pipes
                    )
                    excess_cubes = (
                        edge.excess_cubes if edge.source.qubit < edge.target.qubit else reversed(edge.excess_cubes)
                    )
                else:  # edge.source.qubit == edge.target.qubit
                    start_layer: LayerId = min(edge.source.layer, edge.target.layer)
                    final_layer: LayerId = max(edge.source.layer, edge.target.layer)
                    offset = layer_coordinates[start_layer]
                    step = abs(layer_coordinates[final_layer] - layer_coordinates[start_layer]) / float(
                        edge.number_of_pipes
                    )
                    excess_cubes = (
                        edge.excess_cubes if edge.source.layer > edge.target.layer else reversed(edge.excess_cubes)
                    )

                for cube in excess_cubes:
                    offset += step
                    if edge.source.layer == edge.target.layer:
                        layout[cube.id] = layer_coordinates[edge.source.layer], offset
                    else:  # edge.source.qubit == edge.target.qubit
                        layout[cube.id] = offset, qubit_coordinates[edge.source.qubit]
                    console.debug(f"Layout [E] {cube} : {layout[cube]}")

        return layout

    @staticmethod
    def into_pyzx_graph(graph: VolumetricZxGraph) -> pyzx.graph.base.BaseGraph:
        pyzx_graph = pyzx.Graph()

        for cube in graph.get_bg_cubes():
            pyzx_graph.add_vertex(
                index=cube.id if cube.realised_node is None else cube.realised_node.id,
                ty=NodeType.convert_into_pyzx(cube.kind.get_type()),
            )

        for pipe in graph.get_bg_pipes():
            source = pipe.source.id if pipe.source.realised_node is None else pipe.source.realised_node.id
            target = pipe.target.id if pipe.target.realised_node is None else pipe.target.realised_node.id
            pyzx_graph.add_edge((source, target), EdgeType.convert_into_pyzx(pipe.type))

        return pyzx_graph

    @staticmethod
    def from_pyzx_graph(zx_graph: pyzx.graph.base.BaseGraph) -> VolumetricZxGraph:
        nodes: list[tuple[NodeId, NodeType]] = []
        qubits: dict[NodeId, QubitId] = dict()
        layers: dict[NodeId, LayerId] = dict()
        for node_id in zx_graph.vertices():
            node_qubit = int(zx_graph.qubit(node_id))
            if node_qubit != -1:
                qubits[node_id] = node_qubit

            node_layer = int(zx_graph.row(node_id))
            if node_layer != -1:
                layers[node_id] = node_layer

            nodes.append((node_id, NodeType.convert_from_pyzx(zx_graph.type(node_id))))

        edges: list[tuple[NodeId, NodeId, EdgeType]] = []
        for edge in zx_graph.edges():
            source = edge[0]
            target = edge[1]
            if source > target:
                source, target = target, source
            edges.append((source, target, EdgeType.convert_from_pyzx(zx_graph.edge_type(edge))))

        return VolumetricZxGraph(nodes, edges, qubits, layers)

    @staticmethod
    def into_networkx_graph(zxg: pyzx.graph.base.BaseGraph) -> networkx.Graph:
        nxg: networkx.Graph = networkx.Graph()

        for vertex in zxg.vertices():
            nxg.add_node(vertex, type=zxg.type(vertex), qubit=zxg.qubit(vertex), row=zxg.row(vertex))

        for edge in zxg.edges():
            nxg.add_edge(zxg.edge_s(edge), zxg.edge_t(edge), type=zxg.edge_type(edge))

        return nxg
