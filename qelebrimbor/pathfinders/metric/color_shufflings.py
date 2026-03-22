from dataclasses import dataclass


@dataclass
class ColorShuffling:
    shuffle: str = 'xyz'

    def __post_init__(self):
        if len(self.shuffle) != 3:
            raise Exception("Invalid color shuffling. Must contain three specifiers among {o, x, y, z}.")

        if self.shuffle.count('o') > 1:
            raise Exception("Invalid color shuffling. Must contain at most one O.")

        if self.shuffle.count('x') > 1:
            raise Exception("Invalid color shuffling. Must contain at most one X.")

        if self.shuffle.count('y') > 1:
            raise Exception("Invalid color shuffling. Must contain at most one Y.")

        if self.shuffle.count('z') > 1:
            raise Exception("Invalid color shuffling. Must contain at most one Z.")

    def is_identity(self):
        return self.shuffle == 'xyz'

    def extend(self, other):
        if self.is_identity():
            return other
        elif other.is_identity():
            return self
        else:
            closing = self.shuffle.index('o')
            opening = other.shuffle.index('o')
            shuffled = ""
            for i in range(3):
                if i == opening:
                    shuffled += 'o'
                elif i == closing:
                    shuffled += self.shuffle[opening]
                else:
                    shuffled += self.shuffle[i]
            return ColorShuffling(shuffled)

    def __str__(self):
        return self.shuffle

if __name__ == '__main__':
    csO = ColorShuffling('xyz')
    csX = ColorShuffling("oyz")
    csY = ColorShuffling("xoz")
    csZ = ColorShuffling("xyo")
    csYX = csY.extend(csX)
    csYXZ = csYX.extend(csZ)
    print(f"{csO} -> {csX} = {csO.extend(csX)}")
    print(f"{csY} -> {csX} = {csYX}")
    print(f"{csY} -> {csX} -> {csZ} = {csYXZ}")