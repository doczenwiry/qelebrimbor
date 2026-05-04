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
from time import time

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.path import Path

from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.spacetime.chainfinders.depth_first_search import ChainfinderDFS
from qelebrimbor.vedo.zx_layout.planar import PlanarLayout

from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.circuit import CircuitLayout

import logging
logging.basicConfig(level=logging.CRITICAL)
# logging.getLogger("qelebrimbor.spacetime").setLevel(logging.DEBUG)

if __name__ == "__main__":
    print(f"Benchmarking chainfinder.")

    sys.stdout.flush()

    vzx = VolumetricZxGraph(
        nodes = [ (0, NodeType.X), (1, NodeType.X), (2, NodeType.Z), (3, NodeType.Z), (4, NodeType.X) ],
        edges = [ (0, 1, EdgeType.IDENTITY), (1, 2, EdgeType.IDENTITY), (2, 3, EdgeType.IDENTITY), (1, 4, EdgeType.IDENTITY), (4, 2, EdgeType.IDENTITY) ]
    )

    node0 = vzx.get_zx_node(0)
    node1 = vzx.get_zx_node(1)
    node2 = vzx.get_zx_node(2)
    node3 = vzx.get_zx_node(3)
    node4 = vzx.get_zx_node(4)

    cube0 = BgCube(CubeKind.ZXZ, SpacetimeHelper.ORIGIN)
    cube1 = BgCube(CubeKind.ZXZ, 1 * SpacetimeHelper.XM)
    cube2 = BgCube(CubeKind.XXZ, 2 * SpacetimeHelper.XM)
    cube3 = BgCube(CubeKind.XXZ, 3 * SpacetimeHelper.XM)
    cube4 = BgCube(CubeKind.ZXZ, SpacetimeHelper.XM + SpacetimeHelper.ZP)

    vzx.realise_zx_node( node0, cube0 )
    vzx.realise_zx_node( node1, cube1 )
    vzx.realise_zx_node( node2, cube2 )
    vzx.realise_zx_node( node3, cube3 )
    vzx.realise_zx_node( node4, cube4 )

    for source, target in [ (0,1), (1,2), (2,3), (1,4) ]:
        source_cube = vzx.get_zx_node(source).realising_cube
        target_cube = vzx.get_zx_node(target).realising_cube
        vzx.realise_zx_edge(
            source = source, target = target,
            proposal = Path(source_cube).extend(target_cube, EdgeType.IDENTITY)
        )

    chainfinder = ChainfinderDFS(vzx, branch_and_bound = True, tracing = True)

    start = time()
    chain = chainfinder.find_optimum(cube4, cube2)
    final = time()

    if chain:
        print(f"Optimal chain found : {chain}")
        vzx.realise_zx_edge(node4.id, node2.id, chain)
        ml = chain.manhattan_length()
    else:
        print(f"Failed to find optimal chain.")
        ml = -1

    sys.stderr.flush()

    print(f"Runtime : {round(final - start, 2)} seconds.")

    md = cube0.position.get_manhattan_distance(cube1.position)
    viewer = VolumetricZxGraphViewer(vzx, label = f"manhattan distance = {md}, manhattan length = {ml}, time={round(final - start, 2)}s", layout = PlanarLayout(vzx, scale = 2))
    viewer.display()
