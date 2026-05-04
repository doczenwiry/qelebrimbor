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
import sys
from time import time
from random import seed, randint

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

seed(42)

def check_restrictions(distance: int, number_of_restrictions: int = 0):
    all_permutations = list(
        itertools.chain.from_iterable(
            itertools.permutations(combination)
            for combination in itertools.combinations_with_replacement([NodeType.X, NodeType.Z], number_of_restrictions)
        )
    )

    inconsistencies = 0

    print(f"Benchmarking chainfinder for distance {distance} [restrictions:{number_of_restrictions}, combinations:{len(all_permutations)}].")
    for restrictions in all_permutations:
        chain_restrictions = list(zip(restrictions, [ EdgeType.IDENTITY for _ in range(number_of_restrictions) ]))

        printable_restrictions = list(map(
            lambda restriction: f"({restriction[1].name[0]},{restriction[0].name})", chain_restrictions)
        )
        # print(f"Chain-restrictions {printable_restrictions}")
        sys.stdout.flush()

        vzx = VolumetricZxGraph(nodes, edges)

        node0 = vzx.get_zx_node(0)
        node1 = vzx.get_zx_node(1)

        vzx.realise_zx_node(node = node0, cube = BgCube(CubeKind.ZXZ, SpacetimeHelper.ORIGIN))
        vzx.realise_zx_node(node = node1, cube = BgCube(CubeKind.ZZX, distance * SpacetimeHelper.XM))

        chainfinder = ChainfinderDFS(vzx, branch_and_bound = True, tracing = False)
        start = time()
        chain = chainfinder.find_optimum(node0.realising_cube, node1.realising_cube, restrictions = chain_restrictions)
        final = time()

        if chain is None:
            # print(f"Failed to find optimal chain.")
            continue

        vzx.realise_zx_edge(chain.start.realised_node.id, chain.final.realised_node.id, chain)
        ml = chain.manhattan_length()
        md = chain.start.position.get_manhattan_distance(chain.final.position)

        mce = ManhattanCalculator.minimal_manhattan_excess(chain.start, chain.final)
        # print(f"> Excess volume : {ml - md} [MC:{mce}] ({round(final - start, 2)} seconds)")

        if mce != ml - md:
            inconsistencies += 1

        # viewer = VolumetricZxGraphViewer(
        #     graph = vzx,
        #     label = f"manhattan distance = {md}, manhattan length = {ml}, excess volume = +{ml - md}, time={round(final - start, 2)}s",
        #     layout = PlanarLayout(vzx, scale = 2)
        # )
        # viewer.display()

    print(f"Inconsistencies w.r.t. minimal Manhattan Calculator : {inconsistencies}")

if __name__ == "__main__":
    nodes = [ (0, NodeType.X), (1, NodeType.X) ]
    edges = [ (0, 1, EdgeType.IDENTITY) ]

    check_restrictions(6, 6)
