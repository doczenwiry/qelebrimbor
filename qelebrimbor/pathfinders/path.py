import numpy as np
from functools import total_ordering

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime

@total_ordering
class Path:
    def __init__(self, source: BgCube, target: BgCube):
        self.cubes = [ source ]
        self.occupied = { source.position }
        self.source = source
        self.target = target

    def has_reached_target(self, edge_type: EdgeType = EdgeType.IDENTITY):
        final = self.cubes[-1]
        terminal = self.cubes[-2]
        connectable = BlockGraphHelper.connectable(terminal, self.target, edge_type)
        return final.kind == self.target.kind and final.position == self.target.position and connectable

    def overhead(self):
        return self.manhattan_length() - self.source.position.get_manhattan_distance(self.target.position)

    @staticmethod
    def minimal_volume_possible(source: BgCube, target: BgCube, count_endpoints: bool = True) -> int:
        return Path.minimal_length_possible(source, target) + (+1 if count_endpoints else -1)

    @staticmethod
    def minimal_length_possible(source: BgCube, target: BgCube) -> int:
        return source.position.get_manhattan_distance(target.position) + Path.minimal_overhead_possible(source, target)

    @staticmethod
    def minimal_overhead_possible(source: BgCube, target: BgCube) -> int:
        if source.kind in [ CubeKind.OOO , CubeKind.YYY ] or target.kind in [ CubeKind.OOO , CubeKind.YYY ]:
            return 0

        overhead = 0

        source_reach = source.kind.get_reach()
        target_reach = target.kind.get_reach()

        manhattan = source.position.get_manhattan_distance(target.position)
        relative = target.position - source.position

        if np.sign( source_reach.dot(relative) ) == -1:
            source_reach *= -1
        if np.sign( target_reach.dot(relative) ) == -1:
            target_reach *= -1

        # TODO: work out the formalisation and justification of the cases for all the overhead values.
        if source.kind == target.kind:
            if manhattan >= 1 and relative == source_reach.scale(manhattan):
                overhead += 2

            if manhattan >= 2:
                if any(relative == source_reach.scale(manhattan - 1) + step
                       for step in Spacetime.get_step_constellation(source_reach)
                ):
                    overhead += 2

            if manhattan >= 3:
                if any(relative == source_reach.scale(manhattan-2) + step + source_reach.cross(step)
                       for step in Spacetime.get_step_constellation(source_reach)
                ):
                    overhead += 2
        else:
            differences = source.kind.differences(target.kind)
            overhead += sum(2 for i in range(3) if differences[i] == 1 and relative[i] == 0)
            if manhattan == 1:
                if source.kind.get_type() == target.kind.get_type():
                    overhead += 2
                elif source_reach == target_reach != relative:
                    overhead += 2
            elif manhattan == 2 and source.kind.get_type() != target.kind.get_type():
                if source_reach == target_reach != relative and source_reach.dot(relative) == 0 and relative.dot(relative) != 4:
                    overhead += 2

        return overhead

    def manhattan_distance_remaining(self) -> int:
        terminal = self.cubes[-1]
        return terminal.position.get_manhattan_distance(self.target.position)

    def manhattan_length(self):
        return len(self.cubes) - 1

    def occupies(self, position: Coordinates):
        return position in self.occupied

    def append(self, cube: BgCube):
        self.cubes.append(cube)
        self.occupied.add(cube.position)

    def copy(self):
        cp = Path(self.source, self.target)
        cp.cubes.extend(self.cubes[1:])
        cp.occupied = set(self.occupied)
        return cp

    def __lt__(self, other):
        return self.manhattan_distance_remaining() < other.manhattan_distance_remaining()

    def __str__(self):
        if len(self.cubes) == 2:
            return str(self.source) + " -> " + str(self.target)
        else:
            return str(self.source) + " -> " + str(self.cubes[1:-1]) + " -> " + str(self.target)

    def __repr__(self):
        return str(self.cubes)