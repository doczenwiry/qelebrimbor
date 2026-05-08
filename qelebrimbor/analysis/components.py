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
from typing import cast
from time import time
import networkx as nx

import pandas
import seaborn
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph


class ConnectedComponentsAnalyser:
    @staticmethod
    def analyse(graph: VolumetricZxGraph, plot: bool = False) -> tuple[int, set]:
        start = time()
        components = list(nx.connected_components(cast(nx.Graph, graph)))
        runtime = round(time() - start, 2)

        if plot:
            ax = seaborn.histplot(data = pandas.Series(map(len, components), dtype = int))
            ax.yaxis.set_major_locator(MaxNLocator(integer = True))
            plt.title(f"Connected components [computed in {str(runtime).rjust(2, ' ')}]")
            plt.xlabel("Number of nodes")
            plt.ylabel("Number of components")
            plt.show()
        else:
            histogram: dict[int, int] = defaultdict(int)
            for index in range(len(components)):
                component = components[index]
                histogram[len(component)] += 1
            size = sorted(histogram.keys(), reverse = True)[0]
            print(f"> Largest connected component has size {size} [count={histogram[size]}]")

        return len(components), components[0]