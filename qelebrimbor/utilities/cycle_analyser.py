import networkx as nx

from qelebrimbor.common.components_zx import NodeId
from qelebrimbor.augmented_zx_graph import AugmentedZxGraph

import logging
console = logging.getLogger(__name__)
console.setLevel(logging.INFO)

class CycleAnalyser:
    @staticmethod
    def analyse(azx: AugmentedZxGraph):
        console.info(f"Cycle basis :")
        for cycle in CycleAnalyser.decompose(azx):
            console.info(f"> {cycle}")

    @staticmethod
    def decompose(azx: AugmentedZxGraph) -> list[list[NodeId]]:
        return sorted(nx.cycle_basis(azx), key = lambda cycle: len(cycle), reverse = True)
