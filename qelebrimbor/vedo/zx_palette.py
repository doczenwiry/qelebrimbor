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

from vedo import get_color  # type: ignore[import-untyped]

from qelebrimbor.core.attributes_zx import NodeType

class ZxPalette:
    BLACK = [ 255 * c for c in get_color(rgb='black')]
    LGRAY = [ 255 * c for c in get_color(rgb='k5')]
    DGRAY = [ 255 * c for c in get_color(rgb='k2')]
    WHITE = [ 255 * c for c in get_color(rgb='white')]

    MAJOR_COLORS = {
        NodeType.O: [255 * c for c in get_color(rgb='k2')],
        NodeType.X: [255 * c for c in get_color(rgb='r5')],
        NodeType.Y: [255 * c for c in get_color(rgb='g5')],
        NodeType.Z: [255 * c for c in get_color(rgb='b5')]
    }

    MINOR_COLORS = {
        NodeType.O: [255 * c for c in get_color(rgb='k3')],
        NodeType.X: [255 * c for c in get_color(rgb='r3')],
        NodeType.Y: [255 * c for c in get_color(rgb='g3')],
        NodeType.Z: [255 * c for c in get_color(rgb='b3')]
    }

    @staticmethod
    def get_major(node_type: NodeType):
        return ZxPalette.MAJOR_COLORS[node_type]

    @staticmethod
    def get_minor(node_type: NodeType):
        return ZxPalette.MINOR_COLORS[node_type]