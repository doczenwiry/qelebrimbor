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

import logging

from qelebrimbor.core import zx
from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.bg.path import Path
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType, NodeType
from qelebrimbor.core.zx.chain import ZxChain
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.spacetime.strandfinders.colorblind_fusion_dfs import StrandfinderColorblindFusionDFS
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

logging.basicConfig(level=logging.INFO)
logging.getLogger("qelebrimbor.spacetime.strandfinders.colorblind_fusion_dfs").setLevel(logging.INFO)

zx.attributes.ZX_COLORING = True

if __name__ == "__main__":
    vzx = VolumetricZxGraph(
        nodes=[(node_id, NodeType.Z) for node_id in range(4)],
        edges=[(node_id, (node_id + 1) % 4, EdgeType.HADAMARD) for node_id in range(4)],
    )

    vzx.realise_zx_node(vzx.get_zx_node(0), BgCube(CubeKind.ZXX, SpacetimeHelper.ZP))
    vzx.realise_zx_node(vzx.get_zx_node(1), BgCube(CubeKind.XZX, SpacetimeHelper.ORIGIN))
    vzx.realise_zx_edge(
        source=0,
        target=1,
        proposal=Path(vzx.get_zx_node(0).realising_cube).extend(vzx.get_zx_node(1).realising_cube, EdgeType.HADAMARD),
    )

    chain = (
        ZxChain(source=vzx.get_zx_node(0))
        .extend(node=vzx.get_zx_node(3), edge=vzx.get_zx_edge(0, 3))
        .extend(node=vzx.get_zx_node(2), edge=vzx.get_zx_edge(2, 3))
        .extend(node=vzx.get_zx_node(1), edge=vzx.get_zx_edge(1, 2))
    )
    print(f"Chain : {chain}")

    strandfinder = StrandfinderColorblindFusionDFS(graph=vzx)
    strand = strandfinder.find_optimum(chain, maximal_excess=2)

    # Strand :
    # #4:N0:ZXX@( 0, 0, 1) --H-- XZZ@( 0,-1, 1) --I-- N3:XZX@( 0,-1, 0) --H-- N2:XXZ@(-1,-1, 0)
    # --H-- ZZX@(-1, 0, 0) --I-- #5:N1:XZX@( 0, 0, 0)
    if strand is not None:
        print(f"Strand : {strand}")
        vzx.realise_zx_chain(chain, strand)

    VolumetricZxGraphViewer(graph=vzx, label="fusion-finders").display()
