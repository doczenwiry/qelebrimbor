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

import qelebrimbor.core.zx.attributes
from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.colorless.path import ColorlessPath
from qelebrimbor.core.zx.chain import ZxChain
from qelebrimbor.core.zx.attributes import NodeType, EdgeType
from qelebrimbor.core.components import ZxNode, ZxEdge, BgCube
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.spacetime.colorblind.painter_chain import PainterZxChain

qelebrimbor.core.zx.attributes.ZX_COLORING = True

import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("matplotlib").setLevel(logging.CRITICAL)

if __name__ == "__main__":
    nodes = [
        ZxNode(node_id, node_type) for node_id, node_type in enumerate([
            NodeType.X, NodeType.Z, NodeType.X, NodeType.Z
        ])
    ]
    edges = [
        ZxEdge(nodes[index], nodes[index+1], EdgeType.IDENTITY) for index in range(len(nodes) - 1)
    ]

    nodes[ 0].realising_cube = BgCube(id = 4, kind = CubeKind.XZZ, position = Coordinates(0,0,0))
    nodes[-1].realising_cube = BgCube(id = 5, kind = CubeKind.XXZ, position = Coordinates(0,4,0))

    chain = ZxChain(source = nodes[0])
    for node, edge in zip(nodes[1:], edges):
        chain.append(node, edge)

    print(f"Chain : {chain}")

    colorless = ColorlessPath(start = Coordinates(0, 0, 0))
    current: Coordinates = Coordinates(0,0,0)
    for step in [ SpacetimeHelper.YP, SpacetimeHelper.YP, SpacetimeHelper.YP, SpacetimeHelper.YP ]:
        current = current + step
        colorless.append(current)

    print(f"ColorlessPath : {str(colorless)}")

    print(f"Painted : {PainterZxChain.paint(colorless, chain)}")