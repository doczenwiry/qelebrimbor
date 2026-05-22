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

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("qelebrimbor.spacetime.strandfinders.colorblind_fusion_dfs").setLevel(logging.DEBUG)

zx.attributes.ZX_COLORING = True

if __name__ == "__main__":
    vzx = VolumetricZxGraph(
        nodes=[(node_id, NodeType.Z) for node_id in range(4)],
        edges=[(0, 1, EdgeType.IDENTITY), (0, 3, EdgeType.IDENTITY), (2, 3, EdgeType.IDENTITY)],
        qubits={0: 0, 1: 1, 2: 1, 3: 0},
        layers={node_id: node_id for node_id in range(4)},
    )

    for node_id in range(4):
        vzx.realise_zx_node(vzx.get_zx_node(node_id), cube=BgCube(CubeKind.XXZ, node_id * SpacetimeHelper.YP))

    for node_id in [0, 2]:
        vzx.realise_zx_edge(
            node_id,
            (node_id + 1) % 4,
            proposal=Path(vzx.get_zx_node(node_id).realising_cube).extend(
                vzx.get_zx_node((node_id + 1) % 4).realising_cube, EdgeType.IDENTITY
            ),
        )

    chain = ZxChain(source=vzx.get_zx_node(0)).extend(vzx.get_zx_node(3), vzx.get_zx_edge(0, 3))
    strandfinder = StrandfinderColorblindFusionDFS(graph=vzx)
    strand = strandfinder.find_optimum(chain)

    print(f"Chain : {chain}")

    if strand is not None:
        print(f"Strand : {strand}")
        vzx.realise_zx_chain(chain, strand)

    VolumetricZxGraphViewer(vzx, label="fusion-finders").display()
