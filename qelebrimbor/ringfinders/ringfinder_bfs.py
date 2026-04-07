import logging
console = logging.getLogger(__name__)

from collections import deque

from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime

from qelebrimbor.ringfinders.ring import Ring


class RingFinderBFS:
    @staticmethod
    def find_minimal_alternating_rings(
        order: int = 2,
        root: tuple[CubeKind, Coordinates] = (CubeKind.XZZ, Spacetime.ORIGIN),
        number_sought: int = 1
    ) -> list[Ring]:
        n = 2 * order
        rings: list[Ring] = []

        queue: deque = deque()
        queue.append( Ring(n,root) )

        while len(queue) > 0 and len(rings) != number_sought:
            ring = queue.popleft()
            kind, position = ring.cubes[-1]
            console.debug(f"Current: {kind}@{position}")

            for next_kind, next_position in BlockGraphHelper.get_candidate_constellation(kind, position):
                # Only consider cubes placed in the PPP octant.
                if not all(c >= 0 for c in next_position):
                    continue

                # Skip if next_position is already occupied.
                if ring.contains(next_position):
                    continue

                # Skip if next_kind doesn't allow for further connections.
                if next_kind in [ CubeKind.OOO, CubeKind.YYY ]:
                    continue

                # Skip if the next_kind is not of the opposite color to the current
                if kind.get_type() == next_kind.get_type():
                    continue

                extended: Ring = ring.copy()
                extended.append(next_kind, next_position)

                console.debug(f"> Extended : {extended} [{extended.has_reached_target()}]")
                console.debug(f">> {extended.manhattan_length()} + {extended.manhattan_distance_anchor()} <= {n} ?")

                if extended.has_reached_target():
                    rings.append(extended)

                if extended.manhattan_length() + extended.manhattan_distance_anchor() <= n:
                    queue.append(extended)

        return rings