from typing import cast

from recordclass import RecordClass  # type: ignore[import-untyped]

from qelebrimbor.common.attributes_zx import NodeId, NodeType, QubitId, LayerId, EdgeType
from qelebrimbor.common.attributes_bg import CubeId, PipeId, CubeKind, PipeType
from qelebrimbor.common.coordinates import Coordinates


class ZxNode(RecordClass):
    id: NodeId
    type: NodeType
    qubit: QubitId = -1
    layer: LayerId = -1
    __realising_cube: object = None

    def is_realised(self):
        return self.realising_cube is not None

    @property
    def realising_cube(self):
        return cast(BgCube, self.__realising_cube)

    @realising_cube.setter
    def realising_cube(self, value: BgCube):
        self.__realising_cube = value

    def __str__(self):
        return f"N{self.id}:{self.type}"

    def __repr__(self):
        return str(self)

class ZxEdge(RecordClass):
    source: ZxNode
    target: ZxNode
    type: EdgeType
    __realisation: list[object] = []

    def __post_init__(self):
        if self.source.id > self.target.id:
            self.source, self.target = self.target, self.source

    def is_realised(self):
        return len(self.__realisation) > 0

    @property
    def realisation(self):
        return iter(map(lambda pp: cast(BgPipe, pp), self.__realisation))

    @realisation.setter
    def realisation(self, value: list[BgPipe]):
        self.__realisation = value

    def __str__(self):
        return f"N{self.source.id}-{self.type.name[0]}-N{self.target.id}"

    def __repr__(self):
        return str(self)

class BgCube(RecordClass):
    kind: CubeKind
    position: Coordinates
    id: CubeId = -1
    __realised_node: object = None

    @property
    def realised_node(self):
        return cast(ZxNode, self.__realised_node)

    @realised_node.setter
    def realised_node(self, value: ZxNode):
        self.__realised_node = value

    def __str__(self):
        content = ""
        if self.id != -1:
            content += f"#{self.id}:"
        if self.realised_node is not None:
            content += f"N{self.realised_node.id}:"
        content += f"{self.kind}@{self.position}"
        return content

    def __repr__(self):
        return str(self)

class BgPipe(RecordClass):
    source: CubeId
    target: CubeId
    type: EdgeType

    def __post_init__(self):
        if self.source > self.target:
            self.source, self.target = self.target, self.source