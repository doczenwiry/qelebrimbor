from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_zx import NodeId, EdgeId
from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification

import logging
console = logging.getLogger(__name__)

class BlockGraphConstructor:
    @staticmethod
    def realise(azx: AugmentedZxGraph,
                nodes_specifications: dict[NodeId, tuple[CubeKind, Coordinates]],
                edges_specifications: dict[EdgeId, PathSpecification]
    ):
        BlockGraphConstructor.realise_nodes(azx, nodes_specifications)
        BlockGraphConstructor.realise_edges(azx, edges_specifications)

    @staticmethod
    def realise_nodes(azx: AugmentedZxGraph, specifications: dict[NodeId, tuple[CubeKind, Coordinates]]):
        for node in azx.nodes:
            if node in specifications:
                azx.realise_node(node, *specifications[node])

    @staticmethod
    def realise_edges(azx: AugmentedZxGraph, specifications: dict[EdgeId, PathSpecification]):
        for edge in azx.edges:
            source, target = edge
            alt = (target, source)
            if edge in specifications:
                azx.realise_edge(source, target, specifications[edge])
            elif alt in specifications:
                azx.realise_edge(target, source, specifications[alt])
            elif azx.is_node_realised(source) and azx.is_node_realised(target):
                source_cube = min(azx.get_realising_cubes(source))
                target_cube = min(azx.get_realising_cubes(target))

                if azx.get_cube_position(source_cube).get_manhattan_distance(azx.get_cube_position(target_cube)) != 1:
                    continue

                proposal = PathSpecification(
                    source_cube = source_cube,
                    target_cube = target_cube
                )
                console.debug(f"Realising: {source} -> {target}")
                if azx.is_edge_realised(source, target):
                    console.debug(
                        f"Edge: {source} -> {target} is realised : {azx.get_edge_realisation(source, target)}")
                    raise Exception(f"WTF: {source} -> {target}")
                azx.realise_edge(source, target, proposal)