from enum import Enum

from qelebrimbor.common.coordinates import Coordinates

class Octant(Enum):
    PPP = Coordinates(+1, +1, +1)
    PPM = Coordinates(+1, +1, -1)
    PMP = Coordinates(+1, -1, +1)
    PMM = Coordinates(+1, -1, -1)
    MPP = Coordinates(-1, +1, +1)
    MPM = Coordinates(-1, +1, -1)
    MMP = Coordinates(-1, -1, +1)
    MMM = Coordinates(-1, -1, -1)

    def __getitem__(self, index):
        return self.value[index]

class Step(Enum):
    XP = Coordinates(+1,  0,  0)
    XM = Coordinates(-1,  0,  0)
    YP = Coordinates( 0, +1,  0)
    YM = Coordinates( 0, -1,  0)
    ZP = Coordinates( 0,  0, +1)
    ZM = Coordinates( 0,  0, -1)

class Spacetime:
    ORIGIN = Coordinates(0, 0, 0)

    XP = Coordinates(+1,  0,  0)
    XM = Coordinates(-1,  0,  0)
    YP = Coordinates( 0, +1,  0)
    YM = Coordinates( 0, -1,  0)
    ZP = Coordinates( 0,  0, +1)
    ZM = Coordinates( 0,  0, -1)

    XYZ = Coordinates(+1, +1, +1)
    XY  = Coordinates( 0,  0, +1)
    XZ  = Coordinates( 0, +1,  0)
    YZ  = Coordinates(+1,  0,  0)

    STEPS = [ XP ,YP, ZP, XM, YM, ZM ]
    PLANES = [ XY, XZ, YZ ]

    @staticmethod
    def contains(reach: Coordinates, step: Coordinates) -> bool:
        return reach.dot(step) == 0

    @staticmethod
    def get_direction(source: Coordinates, target: Coordinates) -> Coordinates:
        differences = [ 1 if cs != ct else 0 for cs, ct in zip(source, target) ]

        if sum(differences) != 1:
            raise Exception(f"Coordinates are not co-linear and thus do not have a line-of-sight [{source}/{target}.")

        deltas = [ +1 if cs - ct < 0 else -1 for cs, ct in zip(source, target) ]

        line_of_sight = Coordinates.from_list( [ difference * delta for difference, delta in zip(differences, deltas) ] )

        if Spacetime.ORIGIN.get_manhattan_distance(line_of_sight) != 1:
            raise Exception(f"Erroneous computation of line of sight [{source}/{target} = {line_of_sight}].")

        return line_of_sight

    @staticmethod
    def get_step_constellation(reach: Coordinates) -> list[Coordinates]:
        return [step for step in Spacetime.STEPS if reach.dot(step) == 0]

    @staticmethod
    def get_constellation(position: Coordinates, restriction: Coordinates = None) -> list[Coordinates]:
        constellation = []
        for step in Spacetime.STEPS:
            if restriction is None or restriction.dot(step) == 0:
                constellation.append(position + step)
        return constellation

    @staticmethod
    def in_octant(position: Coordinates, octant : Octant = Octant.PPP) -> bool:
        return all( position[i] * octant[i] >= 0 for i in range(3) )