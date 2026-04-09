from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.components_zx import NodeId, EdgeId
from qelebrimbor.common.components_bg import CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification

import logging
console = logging.getLogger(__name__)

class BlockGraphConstructor:
    @staticmethod
    def realise(vzx: VolumetricZxGraph,
                nodes_specifications: dict[NodeId, tuple[CubeKind, Coordinates]],
                edges_specifications: dict[EdgeId, PathSpecification]
                ):
        BlockGraphConstructor.realise_nodes(vzx, nodes_specifications)
        BlockGraphConstructor.realise_edges(vzx, edges_specifications)

    @staticmethod
    def realise_nodes(vzx: VolumetricZxGraph, specifications: dict[NodeId, tuple[CubeKind, Coordinates]]):
        for node in vzx.nodes:
            if not vzx.is_node_realised(node) and node in specifications:
                vzx.realise_node(node, *specifications[node])

    @staticmethod
    def realise_edges(vzx: VolumetricZxGraph, specifications: dict[EdgeId, PathSpecification]):
        for edge in vzx.edges:
            if vzx.is_edge_realised(*edge):
                continue

            source, target = edge
            alt = (target, source)
            if edge in specifications:
                vzx.realise_edge(source, target, specifications[edge])
            elif alt in specifications:
                vzx.realise_edge(target, source, specifications[alt])
            elif vzx.is_node_realised(source) and vzx.is_node_realised(target):
                source_cube = min(vzx.get_realising_cubes(source))
                target_cube = min(vzx.get_realising_cubes(target))

                if vzx.get_cube_position(source_cube).get_manhattan_distance(vzx.get_cube_position(target_cube)) != 1:
                    continue

                proposal = PathSpecification(
                    source_cube = source_cube,
                    target_cube = target_cube
                )
                console.debug(f"Realising: {source} -> {target}")
                if vzx.is_edge_realised(source, target):
                    console.debug(
                        f"Edge: {source} -> {target} is realised : {vzx.get_edge_realisation(source, target)}")
                    raise Exception(f"WTF: {source} -> {target}")
                vzx.realise_edge(source, target, proposal)