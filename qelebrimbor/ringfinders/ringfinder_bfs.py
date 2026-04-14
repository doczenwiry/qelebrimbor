import logging
console = logging.getLogger(__name__)

from collections import deque

from qelebrimbor.common.components_zx import NodeType, EdgeType
from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.ringfinders.ring import Ring


class RingFinderBFS:
    @staticmethod
    def find_minimal_rings(
        nodes: list[NodeType],
        edges: list[EdgeType] | None = None,
        number_sought: int = 1,
        maximal_overhead: int = 0
    ):
        n = len(nodes)
        rings: list[Ring] = []

        root_kind = CubeKind.suitable_kinds(nodes[0])[0]
        root_position = Spacetime.ORIGIN

        root = (root_kind, root_position)

        queue: deque = deque()
        queue.append( Ring(root) )

        console.debug(f"Starting at {root}")

        while len(queue) > 0 and len(rings) != number_sought:
            ring = queue.popleft()
            length = len(ring.cubes)
            terminal_cube = ring.cubes[-1]
            terminal_kind, terminal_position = terminal_cube
            node_types = { nodes[ length ] } if length < n else { NodeType.X , NodeType.Z }
            pipe_type = edges[ length-1 ] if edges and length <= n else EdgeType.IDENTITY
            console.debug(f"Terminal cube: {terminal_kind}@{terminal_position} [{pipe_type}]")

            for next_kind, next_position in BlockGraphHelper.get_candidate_constellation(terminal_cube, node_types = node_types, pipe_type = pipe_type):
                console.debug(f"> {next_kind}@{next_position}")
                # Only consider cubes placed in the PPP octant.
                if not all(c >= 0 for c in next_position):
                    continue

                # Skip if next_position is already occupied.
                if ring.occupies(next_position):
                    continue

                # Skip if the next_kind is not of the color specified
                if length < n and next_kind.get_type() != nodes[length]:
                    continue

                extended: Ring = ring.copy()
                extended.append(next_kind, next_position)

                # Check whether the ring satisfies the specification
                console.debug(f"Extended : {extended}")
                console.debug(f"> {extended.manhattan_length()} <= {n} + {maximal_overhead}?")
                if length >= n-1 and root_position.get_manhattan_distance(next_position) == 1:
                    console.debug(f"Target reached : {extended}")
                    step = next_position - root_position
                    reach_condition = Spacetime.contains(root_kind.get_reach(), step) and Spacetime.contains(next_kind.get_reach(), step)
                    console.debug(f"> {step}? [{reach_condition}]")
                    if reach_condition and pipe_type in BlockGraphHelper.infer_pipe_type(root_kind, next_kind):
                        rings.append(extended)

                if extended.manhattan_length() + extended.manhattan_distance_anchor() <= n + maximal_overhead:
                    queue.append(extended)

        return rings