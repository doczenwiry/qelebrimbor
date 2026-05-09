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

import sys
import itertools
from time import time

from qelebrimbor.core.attributes_bg import CubeKind
from qelebrimbor.core.attributes_zx import NodeType, EdgeType
from qelebrimbor.core.components import BgCube, ZxNode
from qelebrimbor.core.coordinates import Coordinates

from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.spacetime.subringfinders.depth_first_search import SubringfinderDFS
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport
from qelebrimbor.vedo.zx_layout.planar import PlanarLayout

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
logging.basicConfig(level=logging.CRITICAL)

# The distance between the SOURCE and TARGET in spacetime
DISTANCE = 3
# The number of restrictions to consider along the chain requested
RESTRICTIONS_COUNT = 2
# The choices of restrictions among which to pick for the chain requested
RESTRICTIONS_CHOICES = [ NodeType.X, NodeType.Z ]

# Endpoints considered
ENDPOINTS: dict[str, BgCube] = {
    'source' : BgCube(CubeKind.ZXZ, Coordinates(0, 0, 0)),
    'target' : BgCube(CubeKind.XXZ, DISTANCE * SpacetimeHelper.XM)
}

def __benchmark_restrictions(node_type_restrictions: list[NodeType]):
    nodes = [ (0, ENDPOINTS['source'].kind.get_type()) ]
    for index in range(len(node_type_restrictions)):
        nodes.append( (index+1, node_type_restrictions[index]) )
    nodes.append( (len(node_type_restrictions) + 1, ENDPOINTS['target'].kind.get_type()) )

    edges = [ (index, index+1, EdgeType.IDENTITY) for index in range(len(node_type_restrictions) + 1) ]

    vzx = VolumetricZxGraph(nodes, edges)

    source = vzx.get_zx_node(0)
    target = vzx.get_zx_node(len(node_type_restrictions) + 1)

    vzx.realise_zx_node(node = source, cube = ENDPOINTS['source'])
    vzx.realise_zx_node(node = target, cube = ENDPOINTS['target'])

    subringfinder = SubringfinderDFS(vzx, branch_and_bound = True, tracing = SpacetimeTracingReport.FINAL)

    chain_nodes = [ vzx.get_zx_node(node_id) for node_id in range(1, len(node_type_restrictions) + 1 )]
    chain_edges = [ vzx.get_zx_edge(node_id, node_id + 1) for node_id in range(len(node_type_restrictions) + 1) ]
    chain = (source, chain_nodes, chain_edges, target)

    print(f"Chain : {chain}")

    start = time()
    completion = subringfinder.find_optimum(chain, maximal_excess = 12)
    final = time()
    runtime = round(final - start, 2)

    if completion is None:
        print(f"> Failed to find optimal chain.")
        return -1, -1, chain

    vzx.realise_zx_chain(chain, completion)

    length = completion.manhattan_length()
    distance = completion.start.position.get_manhattan_distance(completion.final.position)

    label = f"number of restrictions = {len(node_type_restrictions)}, manhattan length = {length}, excess volume = +{length - distance - len(node_type_restrictions)}, time={runtime}s"
    viewer = VolumetricZxGraphViewer(graph = vzx, label = label, layout = PlanarLayout(vzx, scale = 2))
    viewer.display()

    return length, runtime, chain

if __name__ == "__main__":
    all_possible_permutations = list(
        itertools.chain.from_iterable(
            itertools.permutations(combination)
            for combination in itertools.combinations_with_replacement(RESTRICTIONS_CHOICES, RESTRICTIONS_COUNT)
        )
    )

    _, _ ,_ = __benchmark_restrictions([
        NodeType.Z, NodeType.X,
        NodeType.Z, NodeType.X,
        NodeType.Z, NodeType.X,
        NodeType.Z, NodeType.X
    ])

    # inconsistencies_with_calculator = 0
    #
    # print(f"Benchmarking chainfinder for distance {DISTANCE} [restrictions:{RESTRICTIONS_COUNT}, permutations:{len(all_possible_permutations)}].")
    # for node_type_restrictions in all_possible_permutations:
    #     md, ml, runtime, chain = __benchmark_restrictions(node_type_restrictions)
    #
    #     mce = ManhattanCalculator.minimal_manhattan_excess(chain.start, chain.final)
    #     print(f"> Manhattan distance = {md}, Manhattan length = {ml}, Excess volume : +{ml - md} [MC:{mce}] ({runtime} seconds)")
    #
    #     if mce != ml - md:
    #         inconsistencies_with_calculator += 1
    #
    # print(f"Inconsistencies w.r.t. minimal Manhattan Calculator : {inconsistencies_with_calculator}")