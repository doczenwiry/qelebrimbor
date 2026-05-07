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

from collections import deque

from qelebrimbor.core.components import BgCube, ZxNode, ZxEdge
from qelebrimbor.core.attributes_zx import NodeType, EdgeType
from qelebrimbor.core.attributes_bg import CubeKind

from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import SpacetimeHelper, Octant

from qelebrimbor.core.ring import Ring
from qelebrimbor.spacetime.fabric import SpacetimeFabric
from qelebrimbor.spacetime.tracer import SpacetimeTracingReport
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker

from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)


class RingFinderBFS:
    def __init__(self,
            graph: VolumetricZxGraph = None,
            ports_tracker: OpenPortsTracker | None = None,
            tracing: SpacetimeTracingReport | None = None
    ):
        self.__graph = graph if graph else VolumetricZxGraph()
        self.__ports_tracker = ports_tracker if ports_tracker else OpenPortsTracker(self.__graph)
        self.__spacetime = graph.spacetime if graph else SpacetimeFabric()
        self.__tracing = tracing

    def find_minimal_rings(self,
        nodes: list[ZxNode],
        edges: list[ZxEdge],
        number_sought: int = 1,
        maximal_overhead: int = 0
    ):
        n = len(nodes)
        e = len(edges) if edges else 0
        rings: list[Ring] = []

        anchor = BgCube(kind = CubeKind.suitable_kinds(nodes[0].type)[0], position = SpacetimeHelper.ORIGIN)

        queue: deque[Ring] = deque()
        queue.append( Ring(anchor) )

        console.info(f"Starting at {anchor} [n={n}, e={e}]")
        console.info(f"> Nodes : {nodes}")

        while len(queue) > 0 and len(rings) != number_sought:
            ring: Ring = queue.popleft()
            length: int = ring.volume()
            terminal: BgCube = ring.terminal
            node_types: set[NodeType] = { nodes[length].type } if length < n else { NodeType.X , NodeType.Z }
            pipe_type: EdgeType = edges[ length-1 ].type if edges and length <= e else EdgeType.IDENTITY
            console.debug(f"Terminal cube: {terminal} [{pipe_type}]")

            for candidate in BlockGraphHelper.get_candidate_constellation(terminal, node_types = node_types, pipe_type = pipe_type):
                console.debug(f"> Candidate : {candidate}")
                # Only consider cubes placed in the PPP octant
                if SpacetimeHelper.in_octant(candidate.position, Octant.PPP):
                    continue

                # Skip if the next_position is already occupied
                if ring.occupies(candidate.position):
                    console.debug(f"> Candidate position already occupied [{candidate}]")
                    continue

                # Skip if the next_kind is not of the color specified
                if length < n and candidate.kind.get_type() != nodes[length].type:
                    console.debug(f"> Candidate doesn't have requested node type [{candidate}]")
                    continue

                extended = ring.extend(candidate, pipe_type)
                # extended: Ring = ring.copy()
                # extended.append(candidate)

                # Check whether the ring satisfies the specification
                console.debug(f"Extended : {str(extended.cubes)}")
                console.debug(f"> {extended.volume()} <= {n} + {maximal_overhead}?")
                if length >= n-1 and anchor.position.get_manhattan_distance(candidate.position) == 1:
                    console.debug(f"Target reached : {ring}")
                    step = candidate.position - anchor.position
                    reach_condition = SpacetimeHelper.contains(anchor.kind.get_reach(), step) and SpacetimeHelper.contains(candidate.kind.get_reach(), step)
                    console.debug(f"> {step} ? [{reach_condition}]")
                    if reach_condition and pipe_type in BlockGraphHelper.infer_pipe_type(anchor.kind, candidate.kind):
                        rings.append(extended)
                else:
                    if extended.volume() + extended.manhattan_distance_anchor() <= n + maximal_overhead:
                        queue.append(extended)
                    else:
                        console.debug(f"> Candidate is too far away [{candidate}]")

        return rings