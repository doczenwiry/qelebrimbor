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

import networkx as nx
import pyzx

from qelebrimbor.core.components import BgCube
from qelebrimbor.core.volumetric_zx_graph import LayerTransition, VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType, LayerId, NodeId, NodeType, QubitId
from qelebrimbor.formats.preprocessing.abstract import Preprocessor

console = logging.getLogger(__name__)


class PYZX:
    @staticmethod
    def into_file(graph: VolumetricZxGraph, filepath: str, planar_scale: int = 1) -> None:
        with open(filepath, "w") as file:
            file.write(PYZX.into_pyzx_graph(graph, planar_scale).to_json())

    @staticmethod
    def from_file(filepath: str, preprocessor: Preprocessor | None = None) -> VolumetricZxGraph:
        with open(filepath, "r") as file:
            pyzx_input = pyzx.Graph().from_json(file.read())
            if preprocessor is not None:
                preprocessor.process(pyzx_input)
            return PYZX.from_pyzx_graph(pyzx_input)

    @staticmethod
    def into_pyzx_graph(graph: VolumetricZxGraph, planar_scale: int = 1) -> pyzx.graph.base.BaseGraph:
        pyzx_graph = pyzx.Graph()
        layout: dict[BgCube, tuple[float, float]] = dict()

        layer_qubit_information_missing = len(graph.get_zx_qubits()) == 0 or len(graph.get_zx_layers()) == 0
        # A PyZX graph obtained from a circuit has edges whose endpoints EITHER have the same layer OR the same qubit
        non_circuit_pyzx_graph = any(
            edge.source.layer != edge.target.layer and edge.source.qubit != edge.target.qubit
            for edge in graph.get_zx_edges()
        )

        if layer_qubit_information_missing or non_circuit_pyzx_graph:
            for cube_id, coordinates in nx.planar_layout(graph.blockgraph, scale=planar_scale).items():
                layout[graph.get_bg_cube(cube_id)] = tuple(coordinates)
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
                layout[node.realising_cube] = (
                    layer_coordinates[node.layer],
                    qubit_coordinates[node.qubit],
                )
                console.debug(f"Layout {node.realising_cube} : {layout[node.realising_cube]}")

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
                        layout[cube] = layer_coordinates[edge.source.layer], offset
                    else:  # edge.source.qubit == edge.target.qubit
                        layout[cube] = offset, qubit_coordinates[edge.source.qubit]
                    console.debug(f"Layout [E] {cube} : {layout[cube]}")

        for cube in graph.get_bg_cubes():
            x, y = layout[cube] if cube in layout else (-1, -1)
            pyzx_graph.add_vertex(
                index=cube.id if cube.realised_node is None else cube.realised_node.id,
                ty=NodeType.convert_into_pyzx(cube.kind.get_type()),
                row=x,
                qubit=y,
            )

        for pipe in graph.get_bg_pipes():
            source = pipe.source.id if pipe.source.realised_node is None else pipe.source.realised_node.id
            target = pipe.target.id if pipe.target.realised_node is None else pipe.target.realised_node.id
            pyzx_graph.add_edge((source, target), EdgeType.convert_into_pyzx(pipe.type))

        return pyzx_graph

    @staticmethod
    def from_pyzx_graph(zx_graph: pyzx.graph.base.BaseGraph) -> VolumetricZxGraph:
        converted_node_ids: dict[NodeId, NodeId] = dict()
        nodes: list[tuple[NodeId, NodeType]] = []
        for original_id in zx_graph.vertices():
            node_id = len(converted_node_ids)
            converted_node_ids[original_id] = node_id
            nodes.append((node_id, NodeType.convert_from_pyzx(zx_graph.type(original_id))))

        edges: list[tuple[NodeId, NodeId, EdgeType]] = []
        for edge in zx_graph.edges():
            source = converted_node_ids[min(edge)]
            target = converted_node_ids[max(edge)]
            edges.append((source, target, EdgeType.convert_from_pyzx(zx_graph.edge_type(edge))))

        qubits: dict[NodeId, QubitId] = dict()
        layers: dict[NodeId, LayerId] = dict()
        # Add qubit and layer information
        for original_id, node_id in converted_node_ids.items():
            node_qubit = int(zx_graph.qubit(original_id))
            node_layer = int(zx_graph.row(original_id))

            if node_qubit != -1:
                qubits[node_id] = node_qubit

            if node_layer != -1:
                layers[node_id] = node_layer

        return VolumetricZxGraph(nodes, edges, qubits, layers)
