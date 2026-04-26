import logging as lgr

from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.components import BgCube

console = lgr.getLogger(__name__)

from typing import Iterable
from queue import PriorityQueue
from collections import defaultdict

from qelebrimbor.common.attributes_bg import CubeId, CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.helpers.spacetime import SpacetimeHelper

from qelebrimbor.pathfinders.path import Path

class PathFinderDFS:
    @staticmethod
    def find_minimal_paths(
        start: BgCube, final: BgCube,
        node_types: list[NodeType] | None = None, edge_types: list[EdgeType] | None = None,
        unavailable_positions: set[Coordinates] | None = None,
        maximal_overhead: int = 6
    ) -> list[Path]:
        node_type_restrictions: list[NodeType] = node_types if node_types else []
        edge_type_restrictions: list[EdgeType] = edge_types if edge_types else []

        unavailable = unavailable_positions or set()

        if any(tr in {NodeType.O, NodeType.Y} for tr in node_type_restrictions):
            raise Exception(f"Path cannot contain cubes of NodeType.O or NodeType.Y.")

        nt = len(node_type_restrictions)
        et = len(edge_type_restrictions)

        paths: list[Path] = []

        minimal_number_of_cubes = nt if nt % 2 == 0 else nt + 1
        maximal_volume = max(start.position.get_manhattan_distance(final.position), minimal_number_of_cubes) + maximal_overhead + 2

        initial = Path( start , final )
        queue: PriorityQueue[Path] = PriorityQueue[Path]()
        queue.put( initial )

        console.info(f"Searching for paths from {start} to {final} [{node_types}].")
        console.info(f"> Maximal volume allowed : {maximal_volume}")
        console.info(f"> Unavailable positions  : {unavailable}")

        while not queue.empty():
            path: Path = queue.get()
            terminal = path.get_terminal()
            length = len(path.extras) + 1
            console.debug(f"Current path : {path.extras}")
            node_type_required = { node_type_restrictions[length-1] } if length <= nt else { NodeType.X, NodeType.Y, NodeType.Z, NodeType.O }
            pipe_type_required =   edge_type_restrictions[length-1]   if length <= et else EdgeType.IDENTITY
            console.debug(f"> Types required : {node_type_required}")
            for candidate in BlockGraphHelper.get_candidate_constellation(terminal, node_types = node_type_required, pipe_type = pipe_type_required):
                if path.has_reached_target() and path.manhattan_length() >= nt:
                    manhattan_length = path.manhattan_length()
                    path_overhead = path.overhead()

                    console.debug(f"> Target reached : {candidate} [+{path_overhead}]")
                    console.debug(f">> {path}")

                    if manhattan_length < maximal_volume:
                        maximal_volume = manhattan_length
                        paths.clear()

                    if manhattan_length == maximal_volume:
                        paths.append( path )

                if candidate.kind in [ CubeKind.YYY, CubeKind.OOO ]:
                    continue

                if path.occupies(candidate.position) or candidate.position in unavailable:
                    continue

                extended: Path = path.copy()
                extended.append(candidate)

                if extended.manhattan_length() + extended.manhattan_distance_remaining() < maximal_volume:
                    console.debug(f"> {candidate}")
                    queue.put( extended )

        return paths

    @staticmethod
    def find_paths(
            final: tuple[CubeKind, Coordinates],
            start: tuple[CubeKind, Coordinates] = (CubeKind.XZZ, SpacetimeHelper.ORIGIN),
            maximal_overheads: Iterable[int] | None = None
    ):
        if maximal_overheads is None:
            return PathFinderDFS.__core_find_paths(final, start)
        else:
            for mo in maximal_overheads:
                paths = PathFinderDFS.__core_find_paths(final, start, mo)
                if len(paths) > 0:
                    return paths

        return {}

    @staticmethod
    def __core_find_paths(
            final: tuple[CubeKind, Coordinates],
            start: tuple[CubeKind, Coordinates] = (CubeKind.XZZ, SpacetimeHelper.ORIGIN),
            maximal_overhead: int = 6
    ) -> defaultdict[int, list[Path]]:
        paths = defaultdict(list)

        start_kind, start_position = start
        final_kind, final_position = final

        maximal_volume = start_position.get_manhattan_distance(final_position) + maximal_overhead

        initial = Path( start , final )
        queue: PriorityQueue[Path] = PriorityQueue[Path]()
        queue.put( initial )

        console.info(f"Searching for paths from {start_kind}@{start_position} to {final_kind}@{final_position}.")

        while not queue.empty():
            path = queue.get()
            current = path.extras[-1]
            kind, position = current
            console.debug(f"Current : {kind}@{position}")
            for next_kind, next_position in BlockGraphHelper.get_candidate_constellation(current):
                if path.occupies(next_position):
                    continue

                if next_kind in [ CubeKind.YYY , CubeKind.OOO ]:
                    continue

                extended: Path = path.copy()
                extended.append( BgCube(next_kind,next_position) )

                if extended.has_reached_target():
                    extended_overhead = extended.overhead()
                    console.info(f"> Target reached : {next_kind}@{next_position} [+{extended_overhead}]")
                    console.debug(f">> {extended}")
                    paths[ extended_overhead ].append( extended )

                if extended.manhattan_length() + extended.manhattan_distance_remaining() < maximal_volume:
                    console.debug(f"> {next_kind}@{next_position}")
                    queue.put( extended )

        return paths