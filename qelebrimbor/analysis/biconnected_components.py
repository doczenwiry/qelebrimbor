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

from collections import defaultdict
from time import time
from typing import cast

import matplotlib.pyplot as plt
import networkx as nx
import pandas
import seaborn
from matplotlib.ticker import MaxNLocator

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph


class BiconnectedComponentsAnalyser:
    @staticmethod
    def count(graph: VolumetricZxGraph, include_bridges: bool = False) -> int:
        return sum(
            1 for bcc in nx.biconnected_component_edges(cast(nx.Graph, graph)) if include_bridges or len(bcc) > 1
        )

    @staticmethod
    def analyse(graph: VolumetricZxGraph, include_bridges: bool = False, plot: bool = False) -> list:
        start = time()
        biconnected = [
            bcc for bcc in nx.biconnected_component_edges(cast(nx.Graph, graph)) if include_bridges or len(bcc) > 1
        ]
        runtime = round(time() - start, 2)

        if plot:
            ax = seaborn.histplot(data=pandas.Series(map(len, biconnected), dtype=int))
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            plt.title(f"Biconnected components [computed in {str(runtime).rjust(2, ' ')}]")
            plt.xlabel("Number of nodes")
            plt.ylabel("Number of components")
            plt.show()
        else:
            histogram: dict[int, int] = defaultdict(int)
            for bcc in biconnected:
                histogram[len(bcc)] += 1
            size = sorted(histogram.keys(), reverse=True)[0]
            print(f"> Total number of connected components : {len(biconnected)}")
            print(f"> Largest connected component has size {size} [count={histogram[size]}]")

        return biconnected
