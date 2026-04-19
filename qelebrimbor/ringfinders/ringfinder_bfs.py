import logging

from qelebrimbor.common.components import BgCube

console = logging.getLogger(__name__)

from collections import deque

from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.attributes_bg import CubeKind
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
        e = len(edges) if edges else 0
        rings: list[Ring] = []

        root = BgCube(kind = CubeKind.suitable_kinds(nodes[0])[0], position = Spacetime.ORIGIN)

        queue: deque = deque()
        queue.append( Ring(root) )

        console.info(f"Starting at {root} [n={n}, e={e}]")

        while len(queue) > 0 and len(rings) != number_sought:
            ring = queue.popleft()
            length = len(ring.cubes)
            terminal: BgCube = ring.cubes[-1]
            node_types = { nodes[ length ] } if length < n else { NodeType.X , NodeType.Z }
            pipe_type = edges[ length-1 ] if edges and length <= e else EdgeType.IDENTITY
            console.info(f"Terminal cube: {terminal} [{pipe_type}]")

            for candidate in BlockGraphHelper.get_candidate_constellation(terminal, node_types = node_types, pipe_type = pipe_type):
                console.debug(f"> {candidate}")
                # Only consider cubes placed in the PPP octant
                if not all(c >= 0 for c in candidate.position):
                    continue

                # Skip if the next_position is already occupied
                if ring.occupies(candidate.position):
                    console.info(f"> Candidate position already occupied [{candidate}]")
                    continue

                # Skip if the next_kind is not of the color specified
                if length < n and candidate.kind.get_type() != nodes[length]:
                    console.info(f"> Candidate doesn't have requested node type [{candidate}]")
                    continue

                extended: Ring = ring.copy()
                extended.append(candidate)

                # Check whether the ring satisfies the specification
                console.info(f"Extended : {extended}")
                console.debug(f"> {extended.manhattan_length()} <= {n} + {maximal_overhead}?")
                if length >= n-1 and root.position.get_manhattan_distance(candidate.position) == 1:
                    console.info(f"Target reached : {extended}")
                    step = candidate.position - root.position
                    reach_condition = Spacetime.contains(root.kind.get_reach(), step) and Spacetime.contains(candidate.kind.get_reach(), step)
                    console.debug(f"> {step} ? [{reach_condition}]")
                    if reach_condition and pipe_type in BlockGraphHelper.infer_pipe_type(root.kind, candidate.kind):
                        rings.append(extended)

                if extended.manhattan_length() + extended.manhattan_distance_anchor() <= n + maximal_overhead:
                    queue.append(extended)
                else:
                    console.info(f"> Candidate is too far away [{candidate}]")

        return rings