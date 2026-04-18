import networkx as nx

from qelebrimbor.common.attributes_zx import NodeId
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)
console.setLevel(logging.INFO)

class MinimalCycleBasisAnalyser:
    @staticmethod
    def analyse(vzx: VolumetricZxGraph):
        console.info(f"Minimal cycle-basis :")
        for cycle in MinimalCycleBasisAnalyser.decompose(vzx):
            console.info(f"> {cycle}")

    @staticmethod
    def decompose(vzx: VolumetricZxGraph) -> list[list[NodeId]]:
        return sorted(nx.minimum_cycle_basis(vzx), key = lambda cycle: len(cycle), reverse = True)
