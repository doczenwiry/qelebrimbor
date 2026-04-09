from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.common.coordinates import Coordinates

from qelebrimbor.common.components_zx import NodeType, EdgeType
from qelebrimbor.common.components_bg import CubeKind

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
            source: tuple[CubeKind, Coordinates],
            target: tuple[CubeKind, Coordinates],
            edge_type: EdgeType
    ) -> bool:
        source_kind, source_position = source
        target_kind, target_position = target
        step = target_position - source_position
        space_condition = source_position.get_manhattan_distance(target_position) == 1
        reach_condition = Spacetime.contains(source_kind.get_reach(), step) and Spacetime.contains(target_kind.get_reach(), step)
        pipe_condition = edge_type in BlockGraphHelper.infer_pipe_type(source_kind, target_kind)
        console.debug(f"Connectable: {source} - {target} : {space_condition}/{reach_condition}/{pipe_condition}")
        return space_condition and reach_condition and pipe_condition

    @staticmethod
    def get_candidate_constellation(
        origin: tuple[CubeKind, Coordinates],
        node_types: set[NodeType] | None = None,
        pipe_type: EdgeType = EdgeType.IDENTITY
    ) -> list[tuple[CubeKind, Coordinates]]:
        if node_types is None:
            considered_node_types = { NodeType.O, NodeType.X, NodeType.Y, NodeType.Z }
        else:
            considered_node_types = node_types

        constellation = []

        origin_kind, origin_position = origin
        origin_reach = origin_kind.get_reach()

        for step in Spacetime.get_step_constellation(origin_reach):
            candidate_position = origin_position + step

            for node_type in considered_node_types:
                for candidate_kind in CubeKind.suitable_kinds(node_type):
                    cube_reach = candidate_kind.get_reach()
                    if Spacetime.contains(cube_reach, step):
                        if pipe_type in BlockGraphHelper.infer_pipe_type(candidate_kind, origin_kind):
                            constellation.append( (candidate_kind, candidate_position) )

        console.debug(f"Constellation of {len(constellation)} points.")
        for kind, position in constellation:
            console.debug(f"> {kind}@{position}")

        return constellation