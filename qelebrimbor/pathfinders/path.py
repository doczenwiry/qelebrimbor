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

        source_reach = source_kind.get_reach()
        target_reach = target_kind.get_reach()

        manhattan = source_position.get_manhattan_distance(target_position)
        relative = target_position - source_position

        if np.sign( np.dot(relative, source_reach) ) == -1:
            source_reach *= -1
        if np.sign( np.dot(relative, target_reach) ) == -1:
            target_reach *= -1

        # TODO: work out the formalisation and justification of the cases for all the overhead values.
        if source_kind == target_kind:
            if manhattan >= 1 and relative == manhattan * source_reach:
                overhead += 2

            if manhattan >= 2:
                if any(relative == (manhattan-1) * source_reach + step
                       for step in Spacetime.get_step_constellation(source_reach)
                ):
                    overhead += 2

            if manhattan >= 3:
                if any(relative == (manhattan-2) * source_reach + step + source_reach.cross(step)
                       for step in Spacetime.get_step_constellation(source_reach)
                ):
                    overhead += 2
        else:
            differences = source_kind.differences(target_kind)
            overhead += sum(2 for i in range(3) if differences[i] == 1 and relative[i] == 0)
            if manhattan == 1:
                if source_kind.get_type() == target_kind.get_type():
                    overhead += 2
                elif source_reach == target_reach != relative:
                    overhead += 2
            elif manhattan == 2 and source_kind.get_type() != target_kind.get_type():
                # TODO: deal with the case where the reach points in the negative directions
                if source_reach == target_reach != relative and Spacetime.XYZ - source_reach == relative:
                    overhead += 2

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