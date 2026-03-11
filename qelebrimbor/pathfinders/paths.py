from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates

class Path:
    def __init__(self, source: tuple[CubeKind, Coordinates] = None):
        self.cubes = []
        self.occupied = set()

        if source is not None:
            self.cubes.append(source)
            self.occupied.add(source[1])

    def volume(self):
        return len(self.cubes) - 1

    def contains(self, position: Coordinates):
        return position in self.occupied

    def append(self, kind: CubeKind, position: Coordinates):
        self.cubes.append((kind, position))
        self.occupied.add(position)

    def copy(self):
        cp = Path()
        cp.cubes.extend(self.cubes)
        cp.occupied = set(self.occupied)
        return cp

    def __str__(self):
        return str(self.cubes)

    def __repr__(self):
        return str(self.cubes)