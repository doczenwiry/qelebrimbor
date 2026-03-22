from dataclasses import dataclass
from functools import total_ordering

from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import Spacetime

@dataclass
class PathWeight:
    source_reach: Coordinates
    target_reach: Coordinates
    color_flips: int = 0
    distance: int = 0

    def __post_init__(self):
        if self.source_reach not in [Spacetime.XP, Spacetime.YP, Spacetime.ZP]:
            raise Exception("Source reach must be in { XP, YP, ZP }.")

        if self.target_reach not in [Spacetime.XP, Spacetime.YP, Spacetime.ZP]:
            raise Exception("Target reach must be in { XP, YP, ZP }.")

        if self.distance < 0:
            raise Exception("Distance cannot be negative.")

    def extend(self, other):
        return PathWeight(
            source_reach = self.source_reach,
            target_reach = other.target_reach,
            color_flips = self.color_flips, # flip color along the other.axis if self.source.reach =
            distance = self.distance + other.distance
        )
        # if self.kind.chainable(other.kind):
        #     return PathWeight(self.kind, self.direction, self.distance + other.distance)
        # else:
        #     return PathWeight(PipeKind.NN, Spacetime.ORIGIN, -1)

    @total_ordering
    def __lt__(self, other):
        pass
        # return other.kind == PipeKind.UU or (self.kind == other.kind and self.distance < other.distance)

if __name__ == '__main__':
    pass
    # pw1 = PathWeight(kind = PipeKind.XZ, direction = Spacetime.XP, distance = 6)
    #
    # print(min(pw1, pw2))
    # print(min(pw1, pw3))