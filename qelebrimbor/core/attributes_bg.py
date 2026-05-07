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

import numpy as np

from enum import Enum
from functools import total_ordering

from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.core.attributes_zx import NodeType

CubeId = int
PipeId = tuple[CubeId, CubeId]

@total_ordering
class CubeKind(Enum):
    OOO = 0
    ZZX = 1
    ZXZ = 2
    ZXX = 3
    XZZ = 4
    XZX = 5
    XXZ = 6
    YYY = 7

    def differences(self, other) -> np.ndarray:
        combination = self.value ^ other.value
        result = np.zeros(3, dtype = np.int32)
        for i in range(3):
            result[2 - i] = combination & 0x1
            combination >>= 1
        return result

    @staticmethod
    def suitable_kinds(node_type: NodeType):
        if   node_type == NodeType.X:
            return [CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZZX]
        elif node_type == NodeType.Y:
            return [CubeKind.YYY]
        elif node_type == NodeType.Z:
            return [CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ]
        elif node_type == NodeType.O:
            return [CubeKind.OOO]
        else:
            raise Exception(f"{node_type} has no representation as a cube of any kind.")

    @staticmethod
    def convert(node_type: NodeType, node_reach: Coordinates):
        if node_type == NodeType.X:
            if node_reach == SpacetimeHelper.XY:
                return CubeKind.ZZX
            elif node_reach == SpacetimeHelper.XZ:
                return CubeKind.ZXZ
            else:
                return CubeKind.XZZ
        elif node_type == NodeType.Z:
            if node_reach == SpacetimeHelper.XY:
                return CubeKind.XXZ
            elif node_reach == SpacetimeHelper.XZ:
                return CubeKind.XZX
            else:
                return CubeKind.ZXX
        elif node_type == NodeType.Y:
            return CubeKind.YYY
        else: # node_type == NodeType.O:
            return CubeKind.OOO

    def get_type(self) -> NodeType:
        if   self == CubeKind.XZZ or self == CubeKind.ZXZ or self == CubeKind.ZZX:
            return NodeType.X
        elif self == CubeKind.ZXX or self == CubeKind.XZX or self == CubeKind.XXZ:
            return NodeType.Z
        elif self == CubeKind.YYY:
            return NodeType.Y
        else: # self == CubeKind.OOO
            return NodeType.O

    # TODO: a CubeKind.YYY has Spacetime.XYZ and single port ?
    def get_reach(self) -> Coordinates:
        if self == CubeKind.XZZ or self == CubeKind.ZXX:
            return SpacetimeHelper.YZ
        elif self == CubeKind.ZXZ or self == CubeKind.XZX:
            return SpacetimeHelper.XZ
        elif self == CubeKind.ZZX or self == CubeKind.XXZ:
            return SpacetimeHelper.XY
        elif self == CubeKind.OOO or self == CubeKind.YYY:
            # TODO: be careful about issues this might cause
            return SpacetimeHelper.ORIGIN
        else:
            raise ValueError(f"Not applicable to cube kind {self.name}")

    def __lt__(self, other):
        return self.value.__lt__(other.value)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.name

class PipeType(Enum):
    IDENTITY = 0
    HADAMARD = 1

    def __str__(self):
        return self.name