from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.components_zx import EdgeType
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper


class Ring:
    def __init__(self, n: int, anchor: tuple[CubeKind, Coordinates]):
        self.anchor = anchor
        self.cubes = [ anchor ]
        self.total_length = n
        self.occupied = { anchor[1] }

    def has_reached_target(self):
        terminal_kind, terminal_position = self.cubes[-1]
        length_achieved = len(self.cubes) == self.total_length
        distance_anchor = terminal_position.get_manhattan_distance(self.anchor[1]) == 1
        identity_connection = EdgeType.IDENTITY in BlockGraphHelper.infer_pipe_type(self.anchor[0], terminal_kind)
        return length_achieved and distance_anchor and identity_connection

    def manhattan_length_missing(self):
        return self.total_length - self.manhattan_length()

    def manhattan_distance_anchor(self) -> int:
        _, terminal_position = self.cubes[-1]
        return terminal_position.get_manhattan_distance(self.anchor[1])

    def manhattan_length(self):
        return len(self.cubes) - 1

    def occupies(self, position: Coordinates):
        return position in self.occupied

    def append(self, kind: CubeKind, position: Coordinates):
        self.cubes.append( (kind, position) )
        self.occupied.add(position)

    def copy(self):
        cp = Ring(self.total_length, self.anchor)
        cp.cubes.extend(self.cubes[1:])
        cp.occupied = set(self.occupied)
        return cp

    def __str__(self):
        return str(self.cubes)

    def __repr__(self):
        return str(self.cubes)