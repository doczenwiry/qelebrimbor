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

from numpy import number

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.helpers.calculator import ManhattanCalculator

from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.spacetime.chainfinders.depth_first_search import ChainfinderDFS
from qelebrimbor.vedo.zx_layout.planar import PlanarLayout

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("qelebrimbor.spacetime").setLevel(logging.INFO)

# VolumetricZxGraph parameters
SOURCE: int = 0
TARGET: int = 1
NODES = [(SOURCE, NodeType.X), (TARGET, NodeType.X)]
EDGES = [(SOURCE, TARGET, EdgeType.IDENTITY)]

# The distance between the SOURCE and TARGET in spacetime
DISTANCE = 3
# The number of restrictions to consider along the chain requested
RESTRICTIONS_COUNT = 2
# The choices of restrictions among which to pick for the chain requested
RESTRICTIONS_CHOICES = [ NodeType.X, NodeType.Z ]

if __name__ == "__main__":
    inconsistencies_with_calculator = 0

    all_possible_permutations = list(
        itertools.chain.from_iterable(
            itertools.permutations(combination)
            for combination in itertools.combinations_with_replacement(RESTRICTIONS_CHOICES, RESTRICTIONS_COUNT)
        )
    )

    print(f"Benchmarking chainfinder for distance {DISTANCE} [restrictions:{RESTRICTIONS_COUNT}, permutations:{len(all_possible_permutations)}].")
    for node_type_restrictions in all_possible_permutations:
        edge_type_restrictions = [EdgeType.IDENTITY for _ in range(RESTRICTIONS_COUNT + 1)]
        chain_restrictions = (node_type_restrictions, edge_type_restrictions)

        print(f"NodeType restrictions : {node_type_restrictions}")
        print(f"EdgeType restrictions : {edge_type_restrictions}")
        sys.stdout.flush()

        vzx = VolumetricZxGraph(NODES, EDGES)

        node0 = vzx.get_zx_node(SOURCE)
        node1 = vzx.get_zx_node(TARGET)

        vzx.realise_zx_node(node = node0, cube = BgCube(CubeKind.ZXZ, SpacetimeHelper.ORIGIN))
        vzx.realise_zx_node(node = node1, cube = BgCube(CubeKind.ZZX, DISTANCE * SpacetimeHelper.XM))

        chainfinder = ChainfinderDFS(vzx, branch_and_bound = True, tracing = False)
        start = time()
        chain = chainfinder.find_optimum(node0.realising_cube, node1.realising_cube, restrictions = chain_restrictions)
        final = time()
        runtime = round(final - start, 2)

        if chain is None:
            print(f"> Failed to find optimal chain.")
            continue

        vzx.realise_zx_edge(chain.start.realised_node.id, chain.final.realised_node.id, chain)

        ml = chain.manhattan_length()
        md = chain.start.position.get_manhattan_distance(chain.final.position)
        mce = ManhattanCalculator.minimal_manhattan_excess(chain.start, chain.final)
        print(f"> Manhattan distance = {md}, Manhattan length = {ml}, Excess volume : +{ml - md} [MC:{mce}] ({runtime} seconds)")

        if mce != ml - md:
            inconsistencies_with_calculator += 1

        label = f"manhattan distance = {md}, manhattan length = {ml}, excess volume = +{ml - md}, time={runtime}s"
        viewer = VolumetricZxGraphViewer(graph = vzx, label = label, layout = PlanarLayout(vzx, scale = 2))
        viewer.display()

    print(f"Inconsistencies w.r.t. minimal Manhattan Calculator : {inconsistencies_with_calculator}")