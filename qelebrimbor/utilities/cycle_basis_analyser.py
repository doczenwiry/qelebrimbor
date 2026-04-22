import networkx as nx

from qelebrimbor.common.attributes_zx import NodeId, EdgeId
from qelebrimbor.common.components import ZxEdge, ZxNode
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)
console.setLevel(logging.INFO)

class CycleBasisAnalyser:
    @staticmethod
    def analyse(vzx: VolumetricZxGraph):
        console.info(f"Cycle basis :")
        cycles = CycleBasisAnalyser.decompose_nodes(vzx)
        for index in range(len(cycles)):
            console.info(f"Index {index} : {cycles[index]}")

    @staticmethod
    def decompose_nodes(vzx: VolumetricZxGraph) -> list[list[ZxNode]]:
        return list(map(
            lambda cycle: [ node for node in map(vzx.get_zx_node, cycle) ],
            sorted(nx.cycle_basis(vzx), key = lambda cycle: len(cycle), reverse = True)
        ))

    @staticmethod
    def decompose_edges(vzx: VolumetricZxGraph) -> list[list[ZxEdge]]:
        decomposition: list[list[ZxEdge]] = []
        for cycle in CycleBasisAnalyser.decompose_nodes(vzx):
            nc = len(cycle)
            current: list[ZxEdge] = []
            for index in range(len(cycle)):
                source, target = (cycle[index], cycle[(index+1) % nc])
                current.append( vzx.get_zx_edge(source.id, target.id) )
            decomposition.append(current)
        return decomposition
