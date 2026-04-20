import networkx as nx

from qelebrimbor.common.attributes_zx import NodeId, EdgeId
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)
console.setLevel(logging.INFO)

class MinimalCycleBasisAnalyser:
    @staticmethod
    def analyse(vzx: VolumetricZxGraph):
        console.info(f"Minimal cycle-basis :")
        cycles = MinimalCycleBasisAnalyser.decompose_nodes(vzx)
        for index in range(len(cycles)):
            console.info(f"Index {index} : {cycles[index]}")

    @staticmethod
    def decompose_nodes(vzx: VolumetricZxGraph) -> list[list[NodeId]]:
        return sorted(nx.minimum_cycle_basis(vzx), key = lambda cycle: len(cycle), reverse = True)

    @staticmethod
    def decompose_edges(vzx: VolumetricZxGraph) -> list[list[EdgeId]]:
        decomposition: list[list[EdgeId]] = []
        for cycle in MinimalCycleBasisAnalyser.decompose_nodes(vzx):
            nc = len(cycle)
            current: list[EdgeId] = []
            for index in range(len(cycle)):
                source, target = sorted( (cycle[index], cycle[(index+1) % nc]))
                current.append( (source, target) )
            decomposition.append(current)
        return decomposition
