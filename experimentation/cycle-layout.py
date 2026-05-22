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

from time import time
from typing import cast

import igraph as ig
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from vedo import get_color

import qelebrimbor.core.zx.attributes
from qelebrimbor.analysis.cycle_sharing import CycleSharingGraph
from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.core.components import ZxEdge, ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType, NodeType
from qelebrimbor.formats.preprocessing.full_reduce import FullReduce
from qelebrimbor.formats.pyzx import PYZX
from qelebrimbor.vedo.zx_palette import ZxPalette


def node_color(node: ZxNode) -> tuple[float, float, float]:
    r, g, b = ZxPalette.MAJOR_COLORS[node.type]
    return r / 255.0, g / 255.0, b / 255.0


def edge_color(edge: ZxEdge):
    if edge.type == EdgeType.HADAMARD:
        return tuple(c for c in get_color(rgb="yellow4"))
    else:
        return tuple(c for c in get_color(rgb="gray6"))


def alternating_cycle_plot(graph: VolumetricZxGraph, label: str):
    all_cycles = CycleAnalyser.decompose(graph, minimal=False)

    nxg = cast(nx.Graph, graph)

    # 2. Generate the layout coordinates using Kamada-Kawai
    # We add higher weights to internal cycle edges to keep the rings clean and tightly grouped
    H = nxg.copy()
    for u, v in H.edges():
        H[u][v]["weight"] = 1.0
    for cycle in all_cycles:
        for edge in cycle.edges:
            H[edge.source.id][edge.target.id]["weight"] = 2.0

    pos = nx.kamada_kawai_layout(H, weight="weight")

    # Find geometric center of the central core
    # core_nodes = set().union(*all_cycles)
    core_nodes = set()
    for cycle in all_cycles:
        core_nodes.update({node.id for node in cycle.nodes})
    center_x = np.mean([pos[n][0] for n in core_nodes])
    center_y = np.mean([pos[n][1] for n in core_nodes])
    center = np.array([center_x, center_y])

    # Adjust coordinates radially outward for non-core nodes
    for node in nxg.nodes():
        if node not in core_nodes:
            # Calculate vector from center to the node
            vector = pos[node] - center
            distance = np.linalg.norm(vector)

            if distance > 0:
                # Check the degree; give lower degree endpoint nodes a bigger push
                if nxg.degree(node) == 1:
                    scale_factor = 1.8  # Aggressive push for tips (e.g. 34, 32, 0)
                else:
                    scale_factor = 1.25  # Moderate push for intermediate branch nodes

                # Update position along the same angular trajectory
                pos[node] = center + vector * scale_factor

    plt.figure(figsize=(12, 12))
    plt.title(f"Cycle Tiling [{label}]", fontsize=14, pad=20)

    node_colors = [node_color(node) for node in graph.get_zx_nodes()]
    node_sizes = [1600 if node.type != NodeType.O else 800 for node in graph.get_zx_nodes()]
    edge_colors = [edge_color(edge) for edge in graph.get_zx_edges()]

    # Draw the actual thin black structural graph edges
    nx.draw_networkx_edges(G=nxg, pos=pos, edge_color="black", width=16.0)
    # Draw the actual thin black structural graph edges
    nx.draw_networkx_edges(G=nxg, pos=pos, edge_color=edge_colors, width=8.0)

    # Draw white nodes with clean black borders
    nx.draw_networkx_nodes(nxg, pos, node_color=node_colors, node_size=node_sizes, edgecolors="black", linewidths=4)

    # Add node index labels inside the circles
    nx.draw_networkx_labels(nxg, pos, font_size=16, font_weight="bold", font_color="white")

    plt.axis("off")
    plt.tight_layout()
    plt.show()


qelebrimbor.core.zx.attributes.ZX_COLORING = True

if __name__ == "__main__":
    pyzx_input = PYZX.from_file("../benchmarking/datasets/small/random-cnots-q8-d16-s106106234.pyzx.json")
    # pyzx_input = PYZX.from_file("../assets/pyzx/random-s42-q4-d10.json")
    FullReduce.process(pyzx_input)

    PYZX.into_file(pyzx_input, filepath="../assets/pyzx/random-cnots-q8-d16-s106106234-reduced.pyzx.json")
    vzx = PYZX.from_pyzx_graph(pyzx_input)

    print(f"vzx : {len(vzx)}")

    nxg = cast(nx.Graph, vzx)
    print(nx.check_planarity(nxg))
    G_2core = nx.k_core(nxg, k=2)
    print(f"G_2core : {len(G_2core)}")

    start = time()
    converted = ig.Graph.from_networkx(nxg)
    converted_ig = []
    for mcb in converted.minimum_cycle_basis():
        converted_ig.append(list(sorted(mcb)))
    converted_ig = sorted(converted_ig)
    print(f"Runtime [IG:{len(converted_ig)}] : {time() - start}s ")

    start = time()
    converted_nx = []
    for mcb in nx.minimum_cycle_basis(nxg):
        converted_nx.append(list(sorted(mcb)))
    converted_nx = sorted(converted_nx)
    print(f"Runtime [NX:{len(converted_nx)}] : {time() - start}s")

    for index in range(len(converted_ig)):
        print(f"{converted_ig[index]} =? {converted_nx[index]}")

    print(f"Agree ? {converted_ig == converted_nx}")

    cycles = CycleAnalyser.decompose(vzx)
    for cycle in cycles:
        print(f"Cycle [{cycle.length}] : {cycle}")

    CycleSharingGraph.plot(cycles)

    alternating_cycle_plot(vzx, label="big")

    cycle0 = [node.id for node in cycles[0].nodes]
    others = [node.id for node in vzx.get_zx_nodes() if node.id not in cycle0]

    positions = nx.shell_layout(nxg, [cycle0, others])
    nx.draw(nxg, pos=positions, with_labels=True)
    plt.show()
    # dataset_filepaths = benchmark.get_dataset_filenames()
    # longest_file_name = max(map(len, dataset_filepaths))
    #
    # for input_path in dataset_filepaths:
    #     vzx = PYZX.from_file(benchmark.DATASET_DIRECTORY + "/" + input_path, preprocessor=AlternatingCycles())
    #
    #     if CycleAnalyser.has_cycles(vzx):
    #         alternating_cycle_plot(vzx, label = input_path)
