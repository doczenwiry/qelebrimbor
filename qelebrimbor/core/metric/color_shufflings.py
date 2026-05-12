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

from dataclasses import dataclass

from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import SpacetimeHelper


@dataclass
class ColorShuffling:
    VALID_SYMBOLS = ['o', 'x', 'y', 'z']

    GENERATORS = {
        SpacetimeHelper.ORIGIN: 'xyz',
        SpacetimeHelper.XP: 'oyz',
        SpacetimeHelper.XM: 'oyz',
        SpacetimeHelper.YP: 'xoz',
        SpacetimeHelper.YM: 'xoz',
        SpacetimeHelper.ZP: 'xyo',
        SpacetimeHelper.ZM: 'xyo'
    }

    start: str = 'xyz'
    final: str = 'xyz'

    def __init__(self, start: str, final: str = None):
        if final is None:
            final = start

        if len(start) != 3 or len(final) != 3:
            raise Exception(f"Invalid color shuffling. Must contain three specifiers among {ColorShuffling.VALID_SYMBOLS}.")

        for symbol in ColorShuffling.VALID_SYMBOLS:
            if start.count(symbol) > 1 or final.count(symbol) > 1:
                raise Exception(f"Invalid color shuffling. Must contain at most one {symbol} [{start}-{final}].")

        self.start = start
        self.final = final

    @staticmethod
    def convert(move: Coordinates) -> ColorShuffling:
        if SpacetimeHelper.ORIGIN.get_manhattan_distance(move) != 1:
            raise ValueError(f"ColorShuffling conversion only works with unit steps in spacetime. [move={move}]")

        return ColorShuffling(ColorShuffling.GENERATORS[move])

    @staticmethod
    def identity():
        return ColorShuffling('xyz')

    def hadamard(self) -> ColorShuffling:
        if self.is_identity():
            raise NotImplementedError(f"Hadamard not supported for identity shuffling.")

        color_one, color_two = tuple(filter(lambda face : face != 'o', self.start))
        color_permutation = str.maketrans({ color_one : color_two, color_two : color_one })
        return ColorShuffling(self.start, self.final.translate(color_permutation))

    def is_identity(self):
        return self.start == 'xyz' and self.final == 'xyz'

    def extend(self, other) -> ColorShuffling:
        if self.is_identity():
            return other
        elif other.is_identity():
            return self
        else:
            closing = self.final.index('o')
            opening = other.start.index('o')
            shuffled = [ sym for sym in other.final ]
            locations = { shuffled[idx] : idx for idx in range(3) }
            for idx in filter(lambda i : i != closing, range(3)):
                symbol = other.start[closing] if idx == opening else other.start[idx]
                shuffled[ locations[symbol] ] = self.final[idx]
            return ColorShuffling(self.start, "".join(shuffled))

    def compatible(self, source: CubeKind, target: CubeKind) -> bool:
        encoded_source: dict[str, str] = dict()
        for marker, face in zip(self.start, source.name):
            encoded_source[marker] = face

        encoded_target: dict[str, str] = dict()
        for marker, face in zip(self.final, target.name):
            encoded_target[marker] = face

        for marker in 'xyz':
            if marker in encoded_source and marker in encoded_target:
                if encoded_source[marker] != encoded_target[marker]:
                    return False
            elif marker in encoded_source or marker in encoded_target:
                raise Exception(f"Internal inconsistency {marker} {encoded_source} {encoded_target}.")

        return True

    def __eq__(self, other):
        return self.start == other.start and self.final == other.final

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return f"{self.start}-{self.final}"

    @staticmethod
    def generate():
        elements = { ColorShuffling(gen) for gen in ColorShuffling.GENERATORS.values() }
        discovered = elements.copy()
        while discovered:
            discovered.clear()
            for current in elements:
                for extender in elements:
                    updated = current.extend(extender)
                    if updated not in elements:
                        discovered.add(updated)
            elements.update(discovered)
        return elements

if __name__ == '__main__':
    csO = ColorShuffling('xyz')
    csX = ColorShuffling('oyz')
    csY = ColorShuffling('xoz')
    csZ = ColorShuffling('xyo')
    print(f"{csO} -> {csX} = {csO.extend(csX)}")
    print(f"({csY} ->  {csX}) -> {csZ}  = {csY.extend(csX).extend(csZ)}")
    print(f" {csY} -> ({csX}  -> {csZ}) = {csY.extend(csX.extend(csZ))}")

    generated = ColorShuffling.generate()
    print(f"Elements [{len(generated)}]:")
    for element in generated:
        if not element.is_identity():
            print(f"> {element} =H=> {element.hadamard()}")

    cs = ColorShuffling('oyz', 'yzo')
    cs2 = cs.extend(cs)

    print(f"{cs} * {cs} = {cs2}")
    print(f"{cs} * {cs2} = {cs.extend(cs2)}")
    print(f"{cs2} * {cs} = {cs2.extend(cs)}")