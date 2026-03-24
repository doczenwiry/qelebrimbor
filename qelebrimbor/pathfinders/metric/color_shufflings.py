from dataclasses import dataclass

from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.spacetime import Spacetime


@dataclass
class ColorShuffling:
    VALID_SYMBOLS = ['o', 'x', 'y', 'z']

    GENERATORS = {
        Spacetime.ORIGIN: 'xyz',
        Spacetime.XP: 'oyz',
        Spacetime.YP: 'xoz',
        Spacetime.ZP: 'xyo'
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
    def convert(move: Coordinates):
        return ColorShuffling.GENERATORS[move]

    @staticmethod
    def identity():
        return ColorShuffling('xyz')

    def is_identity(self):
        return self.start == 'xyz' and self.final == 'xyz'

    def extend(self, other):
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
        print(f"> {element}")

    cs = ColorShuffling('oyz', 'yzo')
    cs2 = cs.extend(cs)

    print(f"{cs} * {cs} = {cs2}")
    print(f"{cs} * {cs2} = {cs.extend(cs2)}")
    print(f"{cs2} * {cs} = {cs2.extend(cs)}")