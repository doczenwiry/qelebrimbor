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
    def convert(vertex_type: pyzx.VertexType):
        if vertex_type == pyzx.VertexType.Z:
            return NodeType.Z
        elif vertex_type == pyzx.VertexType.X:
            return NodeType.X
        elif vertex_type == pyzx.VertexType.BOUNDARY:
            return NodeType.O
        else:
            raise ValueError(f"Unsupported vertex type: {vertex_type}")

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return self.name


class EdgeType(Enum):
    IDENTITY = 0
    HADAMARD = 1

    @staticmethod
    def convert(edge_type: pyzx.EdgeType):
        if edge_type == pyzx.EdgeType.SIMPLE:
            return EdgeType.IDENTITY
        elif edge_type == pyzx.EdgeType.HADAMARD:
            return EdgeType.HADAMARD
        else:
            raise ValueError(f"Unsupported edge type: {edge_type}")

    def __str__(self):
        return self.name