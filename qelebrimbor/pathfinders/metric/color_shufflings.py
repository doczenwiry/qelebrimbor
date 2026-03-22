from dataclasses import dataclass


@dataclass
class ColorShuffling:
    shuffle: str = 'xyz'

    def __post_init__(self):
        if self.shuffle.count('o') != 1:
            raise Exception("Invalid color shuffling. Must contain a single opening.")

    def extend(self, other):
        if self.shuffle == 'xyz':
            return other
        elif other.shuffle == 'xyz':
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
    csX = ColorShuffling("oyz")
    csY = ColorShuffling("xoz")
    csZ = ColorShuffling("xyo")
    csYX = csY.extend(csX)
    csYXZ = csYX.extend(csZ)
    print(f"{csY} -> {csX} = {csYX}")
    print(f"{csY} -> {csX} -> {csZ} = {csYXZ}")