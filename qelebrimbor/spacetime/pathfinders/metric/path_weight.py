#   Copyright 2026 Seweryn Dynerowicz
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from itertools import product, combinations
from dataclasses import dataclass
from functools import total_ordering

from qelebrimbor.spacetime.pathfinders.metric.color_shufflings import ColorShuffling

@dataclass
@total_ordering
class PathWeight:
    shuffle : ColorShuffling = ColorShuffling.identity()
    distance: int = 0

    def __post_init__(self):
        if self.distance < 0:
            raise Exception("Distance cannot be negative.")

    @staticmethod
    def generate(max_distance: int = 1, include_identity: bool = False) -> list[PathWeight]:
        elements = [
            PathWeight(shuffle, distance)
            for shuffle, distance in product(ColorShuffling.generate(), range(1, max_distance + 1))
            if shuffle != ColorShuffling.identity()
        ]

        if include_identity:
            elements.append(PathWeight(ColorShuffling.identity(), 0))

        return elements

    def extend(self, other):
        return PathWeight(self.shuffle.extend(other.shuffle), self.distance + other.distance)

    def __lt__(self, other):
        return self.shuffle == other.shuffle and self.distance < other.distance

    def __str__(self):
        return str(self.shuffle) + ':' + str(self.distance)

@dataclass
class PathWeights:
    weights: list[PathWeight]

    def __post_init__(self) -> None:
        to_remove: list[PathWeight] = []

        for weight in self.weights:
            if any(other < weight for other in self.weights):
                to_remove.append(weight)

        for weight in to_remove:
            self.weights.remove(weight)

    def select(self, other):
        return PathWeights(self.weights + other.weights)

    def extend(self, other):
        return PathWeights([
            weight_one.extend(weight_two) for weight_one, weight_two in product(self.weights, other.weights)
        ])

if __name__ == '__main__':
    pwI = PathWeight()
    pws = PathWeight.generate(max_distance = 1)

    for c in combinations(pws, 2):
        pw = PathWeights(list(c))
        print(f"> {pw}")

    # print(min(pw1, pw2))
    # print(min(pw1, pw3))