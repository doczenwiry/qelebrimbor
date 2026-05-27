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

import matplotlib.pyplot as plt
import networkx as nx

from qelebrimbor.core.components import ZxNode
from qelebrimbor.core.zx.cycle import ZxCycle


class CycleSharingGraph:
    @staticmethod
    def plot(cycles: list[ZxCycle]):
        sharing, biggest = CycleSharingGraph.cycle_sharing_graph(cycles)
        layout = nx.kamada_kawai_layout(sharing)
        center = layout[biggest]
        for node in layout:
            layout[node][0] -= center[0]
            layout[node][1] -= center[1]

        # Prepare the subplots
        fig, ax = plt.subplots(figsize=(8, 8))

        # Draw the nodes and their labels.
        node_sizes = [sharing.nodes[n]["size"] for n in sharing.nodes]
        nodes = nx.draw_networkx_nodes(
            G=sharing,
            pos=layout,
            node_size=[s * 200 for s in node_sizes],
            node_color=node_sizes,
            cmap=plt.get_cmap("Spectral_r"),
        )
        nx.draw_networkx_labels(G=sharing, pos=layout, ax=ax)

        # Draw the edges and their labels.
        edge_weights = nx.get_edge_attributes(sharing, "weight")
        nx.draw_networkx_edges(G=sharing, pos=layout, alpha=0.8)
        nx.draw_networkx_edge_labels(G=sharing, pos=layout, edge_labels=edge_weights)

        plt.title("Cycle Sharing Analysis", y=1.025)
        plt.axis("off")
        plt.xlim(-1.2, 1.2)
        plt.ylim(-1.2, 1.2)
        ax.set_aspect("equal")
        cb = plt.colorbar(nodes, ax=ax, shrink=0.8)
        cb.set_label("Cycle size [number of nodes]", labelpad=15)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def cycle_sharing_graph(cycles: list[ZxCycle]) -> tuple[nx.Graph, int]:
        basis_sets: list[set[ZxNode]] = [set(cycle.nodes) for cycle in cycles]

        sharing: nx.Graph = nx.Graph()

        biggest: int = -1
        index_b: int = -1
        for idx, cycle in enumerate(basis_sets):
            sharing.add_node(idx, size=len(cycle))
            if biggest < len(cycle):
                biggest = len(cycle)
                index_b = idx

        for idx, cycle in enumerate(basis_sets):
            for jdx in range(idx + 1, len(basis_sets)):
                other = basis_sets[jdx]
                intersection = len(cycle.intersection(other))
                if intersection > 0:
                    sharing.add_edge(idx, jdx, weight=intersection)

        return sharing, index_b
