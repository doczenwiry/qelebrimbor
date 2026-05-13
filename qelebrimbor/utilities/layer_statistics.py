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

from qelebrimbor.core.volumetric_zx_graph import LayerTransition, VolumetricZxGraph


def get_layer_density(graph: VolumetricZxGraph, layer: int) -> tuple[int, int]:
    number_of_nodes = sum(1 for _ in graph.get_zx_nodes(layer=layer))
    number_of_edges = sum(1 for _ in graph.get_zx_edges(layered=(layer, LayerTransition.INTRA)))

    return number_of_nodes, number_of_edges
