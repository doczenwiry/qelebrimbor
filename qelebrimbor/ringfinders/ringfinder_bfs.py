from collections import deque

from qelebrimbor.common.components import BgCube, ZxNode, ZxEdge
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import Spacetime, Octant
from qelebrimbor.ringfinders.ring import Ring

import logging
console = logging.getLogger(__name__)

class RingFinderBFS:
    @staticmethod
    def find_minimal_rings(
        nodes: list[ZxNode],
        edges: list[ZxEdge],
        number_sought: int = 1,
        maximal_overhead: int = 0
    ):
        n = len(nodes)
        e = len(edges) if edges else 0
        rings: list[Ring] = []

        anchor = BgCube(kind = CubeKind.suitable_kinds(nodes[0].type)[0], position = Spacetime.ORIGIN)

        queue: deque[Ring] = deque()
        queue.append( Ring(anchor) )

        console.info(f"Starting at {anchor} [n={n}, e={e}] {len(rings) < number_sought}")
        console.info(f"> Nodes : {nodes}")

        while len(queue) > 0 and len(rings) != number_sought:
            ring: Ring = queue.popleft()
            length: int = ring.manhattan_length()
            terminal: BgCube = ring.get_terminal()
            node_types: set[NodeType] = { nodes[length].type } if length < n else { NodeType.X , NodeType.Z }
            pipe_type: EdgeType = edges[ length-1 ].type if edges and length <= e else EdgeType.IDENTITY
            console.debug(f"Terminal cube: {terminal} [{pipe_type}]")

            for candidate in BlockGraphHelper.get_candidate_constellation(terminal, node_types = node_types, pipe_type = pipe_type):
                console.debug(f"> Candidate : {candidate}")
                # Only consider cubes placed in the PPP octant
                if Spacetime.in_octant(candidate.position, Octant.PPP):
                    continue

                # Skip if the next_position is already occupied
                if ring.occupies(candidate.position):
                    console.debug(f"> Candidate position already occupied [{candidate}]")
                    continue

                # Skip if the next_kind is not of the color specified
                if length < n and candidate.kind.get_type() != nodes[length].type:
                    console.debug(f"> Candidate doesn't have requested node type [{candidate}]")
                    continue

                extended: Ring = ring.copy()
                extended.append(candidate)

                # Check whether the ring satisfies the specification
                console.debug(f"Extended : {extended}")
                console.debug(f"> {extended.manhattan_length()} <= {n} + {maximal_overhead}?")
                if length >= n-1 and anchor.position.get_manhattan_distance(candidate.position) == 1:
                    console.debug(f"Target reached : {ring}")
                    step = candidate.position - anchor.position
                    reach_condition = Spacetime.contains(anchor.kind.get_reach(), step) and Spacetime.contains(candidate.kind.get_reach(), step)
                    console.debug(f"> {step} ? [{reach_condition}]")
                    if reach_condition and pipe_type in BlockGraphHelper.infer_pipe_type(anchor.kind, candidate.kind):
                        rings.append(extended)
                else:
                    if extended.manhattan_length() + extended.manhattan_distance_anchor() <= n + maximal_overhead:
                        queue.append(extended)
                    else:
                        console.debug(f"> Candidate is too far away [{candidate}]")

        return rings