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

from qelebrimbor.common.components import BgCube
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.common.coordinates import Coordinates

from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.attributes_bg import CubeKind

from logging import getLogger
console = getLogger(__name__)

class BlockGraphHelper:
    @staticmethod
    def infer_pipe_type(source: CubeKind, target: CubeKind) -> set[EdgeType]:
        source_type = source.get_type()
        target_type = target.get_type()
        source_reach = source.get_reach()
        target_reach = target.get_reach()

        if source_type in [ NodeType.O , NodeType.Y ] or target_type in [ NodeType.O , NodeType.Y ]:
            return { EdgeType.IDENTITY , EdgeType.HADAMARD }

        same_type = source_type == target_type
        same_reach = source_reach == target_reach

        return { EdgeType.IDENTITY } if same_type == same_reach else { EdgeType.HADAMARD }

    @staticmethod
    def connectable(
            source: BgCube,
            target: BgCube,
            edge_type: EdgeType
    ) -> bool:
        step = target.position - source.position
        space_condition = source.position.get_manhattan_distance(target.position) == 1
        reach_condition = SpacetimeHelper.contains(source.kind.get_reach(), step) and SpacetimeHelper.contains(target.kind.get_reach(), step)
        pipe_condition = edge_type in BlockGraphHelper.infer_pipe_type(source.kind, target.kind)
        console.debug(f"Connectable: {source} - {target} : {space_condition}/{reach_condition}/{pipe_condition}")
        return space_condition and reach_condition and pipe_condition

    @staticmethod
    def get_candidate_constellation(
        origin: BgCube,
        node_types: set[NodeType] | None = None,
        pipe_type: EdgeType = EdgeType.IDENTITY
    ) -> list[BgCube]:
        considered_node_types = node_types or { NodeType.O, NodeType.X, NodeType.Y, NodeType.Z }

        constellation = []

        for step in SpacetimeHelper.get_step_constellation(origin.kind.get_reach()):
            candidate_position = origin.position + step

            for node_type in considered_node_types:
                for candidate_kind in CubeKind.suitable_kinds(node_type):
                    cube_reach = candidate_kind.get_reach()
                    if SpacetimeHelper.contains(cube_reach, step):
                        if pipe_type in BlockGraphHelper.infer_pipe_type(candidate_kind, origin.kind):
                            constellation.append( BgCube(kind = candidate_kind, position = candidate_position) )

        console.debug(f"Constellation of {len(constellation)} points.")
        for cube in constellation:
            console.debug(f"> {cube}")

        return constellation