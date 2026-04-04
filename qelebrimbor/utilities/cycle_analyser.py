import networkx as nx

from qelebrimbor.augmented_zx_graph import AugmentedZxGraph

import logging
console = logging.getLogger(__name__)

class CycleAnalyser:
    @staticmethod
    def analyse(azx: AugmentedZxGraph):
        cycles = [sorted(cycle) for cycle in nx.cycle_basis(azx)]
        cycles = sorted(cycles, key=len, reverse=True)
        content = ""
        for cycle in cycles:
            content += f"{cycle} "
        console.info(f"Cycle basis : {content}")
