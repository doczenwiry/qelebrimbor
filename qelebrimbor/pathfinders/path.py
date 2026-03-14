from functools import total_ordering

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates

@total_ordering
class Path:
    def __init__(self, source: tuple[CubeKind, Coordinates], target: tuple[CubeKind, Coordinates]):
        self.cubes = [ source ]
        self.occupied = { source[1] }
        self.source = source
        self.target = target

    def has_reached_target(self):
        terminal_kind, terminal_position = self.cubes[-1]
        target_kind, target_position = self.target
        return terminal_kind == target_kind and terminal_position == target_position

    def overhead(self):
        _, source_position = self.source
        _, target_position = self.target

        return self.manhattan_length() - source_position.get_manhattan_distance(target_position)

    def manhattan_distance_remaining(self) -> int:
        _, target_position = self.target
        _, terminal_position = self.cubes[-1]

        return terminal_position.get_manhattan_distance(target_position)

    def manhattan_length(self):
        return len(self.cubes) - 1

    def contains(self, position: Coordinates):
        return position in self.occupied

    def append(self, kind: CubeKind, position: Coordinates):
        self.cubes.append((kind, position))
        self.occupied.add(position)

    def copy(self):
        cp = Path(self.source, self.target)
        cp.cubes.extend(self.cubes[1:])
        cp.occupied = set(self.occupied)
        return cp

    def __lt__(self, other):
        return self.manhattan_distance_remaining() < other.manhattan_distance_remaining()

    def __str__(self):
        return str(self.cubes)

    def __repr__(self):
        return str(self.cubes)