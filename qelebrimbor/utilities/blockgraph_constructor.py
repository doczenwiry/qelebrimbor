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

from qelebrimbor.core.bg.attributes import CubeId, CubeKind
from qelebrimbor.core.bg.path import Path
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeId, NodeId

console = logging.getLogger(__name__)


class BlockGraphConstructor:
    @staticmethod
    def realise(
        graph: VolumetricZxGraph,
        nodes_specifications: dict[NodeId, BgCube],
        edges_specifications: dict[EdgeId, Path],
    ):
        BlockGraphConstructor.realise_nodes(graph, nodes_specifications)
        BlockGraphConstructor.realise_edges(graph, edges_specifications)

    @staticmethod
    def realise_nodes(graph: VolumetricZxGraph, specifications: dict[NodeId, BgCube]) -> bool:
        for node_id, bg_cube in specifications.items():
            zx_node = graph.get_zx_node(node_id)
            if zx_node.is_realised():
                console.error(f"Node {zx_node} is already realised")
                return False

            console.debug(f"Node {zx_node} -> {bg_cube}")
            graph.realise_zx_node(zx_node, bg_cube)
        return True

    @staticmethod
    def place_cubes(
        graph: VolumetricZxGraph,
        specifications: list[tuple[CubeKind, CubeId, Coordinates]],
    ):
        for kind, cube_id, step in specifications:
            cube = graph.get_bg_cube(cube_id)
            position = cube.position + step
            graph.place_cube(BgCube(kind=kind, position=position))

    @staticmethod
    def realise_edges(graph: VolumetricZxGraph, specifications: dict[EdgeId, Path]) -> bool:
        for edge, proposal in specifications.items():
            source, target = edge

            zx_edge = graph.get_zx_edge(*edge)
            if zx_edge.is_realised():
                console.warning(f"Edge: {source} -> {target} is already realised : {zx_edge.realisation}")
                continue

            console.debug(f"Realisation of edge {zx_edge}")
            console.debug(f"> Proposal : {proposal}")
            if graph.is_path_valid(zx_edge, proposal):
                graph.realise_zx_edge(source, target, proposal)
            else:
                raise Exception(f"> Invalid path proposal for edge {edge} [{proposal}]")

        return True
