from recordclass import RecordClass  # type: ignore[import-untyped]

from qelebrimbor.common.attributes_zx import NodeId, NodeType, QubitId, LayerId, EdgeType
from qelebrimbor.common.attributes_bg import CubeId, PipeId, CubeKind, PipeType
from qelebrimbor.common.coordinates import Coordinates


class ZxNode(RecordClass):
    id: NodeId
    type: NodeType
    qubit: QubitId = -1
    layer: LayerId = -1
    realising_cube: CubeId = -1

    def __str__(self):
        return f"{self.id}[{self.type.name}]"

class ZxEdge(RecordClass):
    source: NodeId
    target: NodeId
    type: EdgeType
    realisation: list[PipeId] = []

class BgCube(RecordClass):
    id: CubeId
    kind: CubeKind
    position: Coordinates
    realised_node: NodeId = -1

    def __str__(self):
        return f"#{self.id}:{self.kind}@{self.position}"

class BgPipe(RecordClass):
    source: CubeId
    target: CubeId
    type: EdgeType