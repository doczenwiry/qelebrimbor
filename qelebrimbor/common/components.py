from recordclass import RecordClass  # type: ignore[import-untyped]
from typing import cast

from qelebrimbor.common.attributes_zx import NodeId, NodeType, QubitId, LayerId, EdgeType
from qelebrimbor.common.attributes_bg import CubeId, CubeKind
from qelebrimbor.common.coordinates import Coordinates

import logging
console = logging.getLogger(__name__)

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
    def is_intra_layer(self):
        return self.source.layer == self.target.layer

    @property
    def is_inter_layer(self):
        return self.source.layer != self.target.layer

    @property
    def number_of_pipes(self):
        return len(self.__realisation)

    @property
    def excess_volume(self):
        return len(self.__realisation) - 1

    @property
    def excess_cubes(self):
        start_pipe = cast(BgPipe, self.__realisation[0])
        if self.source.realising_cube == start_pipe.source or self.source.realising_cube == start_pipe.target:
            previous_cube = self.source.realising_cube
        else:
            previous_cube = self.target.realising_cube
        excess: list[BgCube] = []
        for index in range(self.number_of_pipes-1):
            pipe = cast(BgPipe, self.__realisation[index])
            extra = pipe.source if pipe.source != previous_cube else pipe.target
            excess.append( extra )
            previous_cube = extra
        return excess

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

    def matches(self, other):
        return self.kind == other.kind and self.position == other.position

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

    def __hash__(self):
        return hash( (self.kind, self.position.x, self.position.y, self.position.z) )

class BgPipe(RecordClass):
    source: BgCube
    target: BgCube
    type: EdgeType

    def __post_init__(self):
        if self.source.id > self.target.id:
            self.source, self.target = self.target, self.source