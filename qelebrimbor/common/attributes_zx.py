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

from enum import Enum

import pyzx

NodeId = int
EdgeId = tuple[NodeId, NodeId]
QubitId = int
LayerId = int

class NodeType(Enum):
    O = 0 # Boundary
    X = 1 # X-Spider
    Y = 2 # Y-Spider
    Z = 3 # Z-Spider

    @staticmethod
    def convert_from_pyzx(vertex_type: pyzx.VertexType):
        if vertex_type == pyzx.VertexType.Z:
            return NodeType.Z
        elif vertex_type == pyzx.VertexType.X:
            return NodeType.X
        elif vertex_type == pyzx.VertexType.BOUNDARY:
            return NodeType.O
        else:
            raise ValueError(f"Unsupported vertex type: {vertex_type}")

    @staticmethod
    def convert_into_pyzx(self):
        if self == NodeType.Z:
            return pyzx.VertexType.Z
        elif self == NodeType.X:
            return pyzx.VertexType.X
        elif self == NodeType.O:
            return pyzx.VertexType.BOUNDARY
        else:
            raise ValueError(f"Unsupported conversion for node type: {self}")

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return self.name


class EdgeType(Enum):
    IDENTITY = 0
    HADAMARD = 1

    @staticmethod
    def convert_from_pyzx(edge_type: pyzx.EdgeType):
        if edge_type == pyzx.EdgeType.SIMPLE:
            return EdgeType.IDENTITY
        elif edge_type == pyzx.EdgeType.HADAMARD:
            return EdgeType.HADAMARD
        else:
            raise ValueError(f"Unsupported edge type: {edge_type}")

    @staticmethod
    def convert_into_pyzx(self):
        if self == EdgeType.IDENTITY:
            return pyzx.EdgeType.SIMPLE
        else: # self == EdgeType.HADAMARD:
            return pyzx.EdgeType.HADAMARD

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name