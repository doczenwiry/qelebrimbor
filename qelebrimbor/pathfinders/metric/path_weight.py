from dataclasses import dataclass
from functools import total_ordering
from itertools import product

from qelebrimbor.pathfinders.metric.color_shufflings import ColorShuffling


@dataclass
class PathWeight:
    source: ColorShuffling
    target: ColorShuffling
    distance: int = 0

    def __post_init__(self):
        if self.distance < 0:
            raise Exception("Distance cannot be negative.")

    def __mul__(self, other):
        return PathWeight(
            source = self.target if self.source.is_identity() else self.source,
            target = self.target.extend(other.target),
            distance = self.distance + other.distance
        )

    @total_ordering
    def __lt__(self, other):
        pass
        # return other.kind == PipeKind.UU or (self.kind == other.kind and self.distance < other.distance)

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