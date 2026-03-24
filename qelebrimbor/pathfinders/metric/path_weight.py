from itertools import product
from dataclasses import dataclass

from qelebrimbor.pathfinders.metric.color_shufflings import ColorShuffling


@dataclass
class PathWeight:
    shuffle : ColorShuffling = ColorShuffling.identity()
    distance: int = 0

    def __post_init__(self):
        if self.distance < 0:
            raise Exception("Distance cannot be negative.")

    def __mul__(self, other):
        return PathWeight(self.shuffle.extend(other.shuffle), self.distance + other.distance)
    __rmul__ = __mul__


@dataclass
class PathWeights:
    weights: list[PathWeight]

    def __post_init__(self):
        pass

    def select(self, other):
        return PathWeights(self.weights + other.weights)

    def extend(self, other):
        return PathWeights([
            weight_one * weight_two for weight_one, weight_two in product(self.weights, other.weights)
        ])

if __name__ == '__main__':
    pass
    # pw1 = PathWeight(kind = PipeKind.XZ, direction = Spacetime.XP, distance = 6)
    #
    # print(min(pw1, pw2))
    # print(min(pw1, pw3))