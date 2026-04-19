from qelebrimbor.common.components import BgCube
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper


class Ring:
    def __init__(self, anchor: BgCube):
        self.anchor = anchor
        self.cubes = [ anchor ]
        self.occupied = { anchor[1] }

    def manhattan_distance_anchor(self) -> int:
        terminal = self.cubes[-1]
        return terminal.position.get_manhattan_distance(self.anchor.position)

    def manhattan_length(self):
        return len(self.cubes) - 1

    def occupies(self, position: Coordinates):
        return position in self.occupied

    def append(self, cube: BgCube):
        self.cubes.append( cube )
        self.occupied.add(cube.position)

    def copy(self):
        cp = Ring(self.anchor)
        cp.cubes.extend(self.cubes[1:])
        cp.occupied = set(self.occupied)
        return cp

    def __str__(self):
        return str(self.cubes)

    def __repr__(self):
        return str(self.cubes)