import numpy as np
from functools import total_ordering

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import Spacetime


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

    def minimal_length_possible(self) -> int:
        _, source_position = self.source
        _, target_position = self.target

        return source_position.get_manhattan_distance(target_position) + self.minimal_overhead_possible()

    def minimal_overhead_possible(self):
        source_kind, source_position = self.source
        target_kind, target_position = self.target

        if source_kind in [ CubeKind.OOO , CubeKind.YYY ] or target_kind in [ CubeKind.OOO , CubeKind.YYY ]:
            return 0

        overhead = 0
        if source_kind == target_kind:
            overhead -= 1
            # reached = abs(np.dot(relative, manhattan * source_kind.get_reach())) == 1
            # if reached:
            #     overhead += 2
            # if manhattan >= 2:
            #     reached = any( abs(np.dot(relative, manhattan * source_kind.get_reach())) == 1 for step in [ Spacetime.XP])
            #     reach_xp = abs(np.dot(relative, manhattan * source_kind.get_reach() + Spacetime.XP))
            #     reach_xm = abs(np.dot(relative, manhattan * source_kind.get_reach() + Spacetime.XM))
            #     reach_zp = abs(np.dot(relative, manhattan * source_kind.get_reach() + Spacetime.ZP))
            #     reach_zm = abs(np.dot(relative, manhattan * source_kind.get_reach() + Spacetime.ZM))
            #     if 1 in [ reach_xp , reach_xm , reach_zp , reach_zm ]:
            #         overhead += 2
        else:
            relative = target_position - source_position

            differences = source_kind.differences(target_kind)
            overhead += sum(2 for i in range(3) if differences[i] == 1 and relative[i] == 0)
            # if manhattan == 1:
            #     overhead = 1
            # elif manhattan == 2:
            #     overhead = 2

        return overhead

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