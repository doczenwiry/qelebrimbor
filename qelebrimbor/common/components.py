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
    kind: CubeKind
    position: Coordinates
    id: CubeId = -1
    realised_node: NodeId = -1

    def __str__(self):
        content = ""
        if self.id != -1:
            content += f"#{self.id}"
        content += f"{self.kind}@{self.position}"
        if self.realised_node != -1:
            content += f"[N{self.realised_node}]"
        return content

    def __repr__(self):
        return str(self)

class BgPipe(RecordClass):
    source: CubeId
    target: CubeId
    type: EdgeType