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

import itertools
import logging
from time import time

import qelebrimbor.core.zx.attributes
from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.components import BgCube, ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType, NodeType
from qelebrimbor.core.zx.chain import ZxChain
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.spacetime.strandfinders.breadth_first_search import StrandfinderBFS
from qelebrimbor.spacetime.strandfinders.colorblind_dfs import StrandfinderColorblindDFS
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("qelebrimbor.spacetime.strandfinders").setLevel(logging.INFO)

qelebrimbor.core.zx.attributes.ZX_COLORING = True

if __name__ == "__main__":
    nodes = list(zip(itertools.count(0, 1), [NodeType.X, NodeType.Z, NodeType.X, NodeType.Z]))
    edges = [(index, index + 1, EdgeType.IDENTITY) for index in range(len(nodes) - 1)]
    qubits = {node_id: 0 for node_id, _ in nodes}
    layers = {node_id: node_id for node_id, _ in nodes}

    for md in [1, 5, 10, 25, 100]:
        vzx = VolumetricZxGraph(nodes, edges, qubits, layers)

        source = vzx.get_zx_node(0)
        target = vzx.get_zx_node(len(nodes) - 1)

        vzx.realise_zx_node(node=source, cube=BgCube(CubeKind.XZZ, SpacetimeHelper.ORIGIN))
        vzx.realise_zx_node(node=target, cube=BgCube(CubeKind.ZXX, md * SpacetimeHelper.XM))

        # strandfinder = StrandfinderBFS(vzx,tracing = SpacetimeTracingReport.FINAL)
        # strandfinder = StrandfinderDFS(vzx, branch_and_bound = True, tracing = SpacetimeTracingReport.FINAL)
        strandfinder = StrandfinderColorblindDFS(vzx, branch_and_bound=False, tracing=SpacetimeTracingReport.FINAL)

        if strandfinder.__class__ == StrandfinderBFS and md > 5:
            print(f"StrandfinderBFS is too slow with md > 5. Not even trying {md}.")
            continue

        preceding: ZxNode = vzx.get_zx_node(0)
        chain = ZxChain(source=vzx.get_zx_node(0))
        for index in range(1, len(nodes)):
            following = vzx.get_zx_node(index)
            chain.append(
                vzx.get_zx_node(following.id),
                vzx.get_zx_edge(preceding.id, following.id),
            )
            preceding = following

        print(f"Chain : {chain}")

        start = time()
        strand = strandfinder.find_optimum(chain, maximal_excess=6)
        final = time()
        runtime = round(final - start, 2)

        label = f"{strandfinder.__class__.__name__} : time = {runtime}s"
        if strand is not None:
            print(f"Strand : {strand}")

            vzx.realise_zx_chain(chain, strand)

            label += f", volume = {strand.length}, excess = +{strand.length - max(chain.length, md)}"
        else:
            label += ", volume = n/a, excess = n/a"
            print("> Failed to find optimal chain.")

        viewer = VolumetricZxGraphViewer(graph=vzx, label=label)
        viewer.display()
