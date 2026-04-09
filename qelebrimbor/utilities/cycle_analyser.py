import networkx as nx

from qelebrimbor.common.components_zx import NodeId
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)
console.setLevel(logging.INFO)

class CycleAnalyser:
    @staticmethod
    def analyse(vzx: VolumetricZxGraph):
        console.info(f"Cycle basis :")
        for cycle in CycleAnalyser.decompose(vzx):
            console.info(f"> {cycle}")

    @staticmethod
    def decompose(vzx: VolumetricZxGraph) -> list[list[NodeId]]:
        return sorted(nx.cycle_basis(vzx), key = lambda cycle: len(cycle), reverse = True)
