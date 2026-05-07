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
from time import time
from typing import Iterable

from qelebrimbor.core import attributes_zx
from qelebrimbor.core.attributes_zx import NodeId, NodeType, EdgeType

from qelebrimbor.spacetime.ringfinders.breadth_first_search import RingfinderBFS
from qelebrimbor.spacetime.ringfinders.depth_first_search import RingfinderDFS
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport

from qelebrimbor.utilities.cycle_analyser import CycleAnalyser

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.vedo.zx_layout.cycle import CycleLayout
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
logging.basicConfig(level=logging.INFO)

def __benchmark_ring(restrictions: Iterable[tuple[NodeType, EdgeType]]):
    node_type_restrictions, edge_type_restrictions = zip(*restrictions)
    print(f"NodeType restrictions : {node_type_restrictions}")
    print(f"EdgeType restrictions : {edge_type_restrictions}")

    ring_size = len(node_type_restrictions)
    nodes: list[tuple[NodeId, NodeType]] = [
        (node_id, node_type_restrictions[node_id]) for node_id in range(ring_size)
    ]

    edges: list[tuple[NodeId, NodeId, EdgeType]] = [
        (node_id, (node_id+1) % ring_size, edge_type_restrictions[node_id]) for node_id in range(ring_size)
    ]

    vzx = VolumetricZxGraph(nodes, edges)

    zx_cycle = CycleAnalyser.decompose(vzx, minimal = True)[0]
    print(f"Cycle : {CycleAnalyser.string(zx_cycle)}")

    # ringfinder = RingfinderBFS(graph = vzx, tracing = SpacetimeTracingReport.FINAL)
    ringfinder = RingfinderDFS(graph = vzx, tracing = SpacetimeTracingReport.FINAL)

    start = time()
    ring = ringfinder.find_optimum(zx_cycle, maximal_excess = 6)
    final = time()
    runtime = round(final - start, 2)

    if ring is None:
        print(f"> Failed to find optimal ring.")
        return -1
    print(f"Found a ring with volume : {ring.volume()}")
    print(f"> {ring}")

    vzx.realise_zx_cycle(zx_cycle, ring)

    volume = vzx.volume()

    label = f"volume = {volume}, excess = +{volume - len(node_type_restrictions)}, time={runtime}s"
    viewer = VolumetricZxGraphViewer(graph = vzx, label = label, layout = CycleLayout(vzx))
    viewer.display()

    return volume, runtime, ring

attributes_zx.ZX_COLORING = True
# The number of spiders in the ring to realise
RING_SIZE = 4
# The choices of restrictions among which to pick for the chain requested
NODE_TYPE_CHOICES = [NodeType.X, NodeType.Z]

if __name__ == "__main__":
    all_spider_permutations = set(
        itertools.chain.from_iterable(
            itertools.permutations(combination)
            for combination in itertools.combinations_with_replacement(NODE_TYPE_CHOICES, RING_SIZE)
        )
    )
    all_legs_permutations = set(
        itertools.chain.from_iterable(
            itertools.permutations(combination)
            for combination in itertools.combinations_with_replacement(EdgeType, RING_SIZE)
        )
    )

    __benchmark_ring(restrictions = zip(
        [ NodeType.X for _ in range(4) ],
        [ EdgeType.IDENTITY if e % 2 == 0 else EdgeType.HADAMARD for e in range(4) ]
    ))

    # count = 0
    # for spiders, legs in itertools.product(all_spider_permutations, all_legs_permutations):
    #     __benchmark_ring(restrictions = zip(spiders, legs))
    #
    #     count += 1
    #     if count == 1:
    #         break