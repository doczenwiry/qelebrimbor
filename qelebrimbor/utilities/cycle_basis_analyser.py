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

from typing import cast
import networkx as nx

from qelebrimbor.common.components import ZxEdge, ZxNode
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)

class CycleBasisAnalyser:
    @staticmethod
    def analyse(vzx: VolumetricZxGraph, minimal: bool = False):
        console.info(f"Cycle basis :")
        cycles = CycleBasisAnalyser.decompose_nodes(vzx, minimal)
        for index in range(len(cycles)):
            console.info(f"Index {index} : {cycles[index]}")

    @staticmethod
    def decompose_nodes(vzx: VolumetricZxGraph, minimal: bool = False) -> list[list[ZxNode]]:
        nxg = cast(nx.Graph, vzx)
        cycle_basis = nx.minimum_cycle_basis(nxg) if minimal else nx.cycle_basis(nxg)
        return list(map(
            lambda cycle: list(map(vzx.get_zx_node, cycle)),
            sorted(cycle_basis, key = len, reverse = True)
        ))

    @staticmethod
    def decompose_edges(vzx: VolumetricZxGraph, minimal: bool = False) -> list[list[ZxEdge]]:
        decomposition: list[list[ZxEdge]] = []
        for cycle in CycleBasisAnalyser.decompose_nodes(vzx, minimal):
            nc = len(cycle)
            current: list[ZxEdge] = []
            for index in range(len(cycle)):
                source, target = (cycle[index], cycle[(index+1) % nc])
                current.append( vzx.get_zx_edge(source.id, target.id) )
            decomposition.append(current)
        return decomposition
