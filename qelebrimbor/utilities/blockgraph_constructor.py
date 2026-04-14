from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.components_zx import NodeId, EdgeId, EdgeType
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
            source, target = edge
            console.debug(f"Realising edge: {source} -> {target}")

            if vzx.is_edge_realised(*edge):
                console.warning(f"Edge: {source} -> {target} is already realised : {vzx.get_edge_realisation(source, target)}")
                continue

            if edge in specifications:
                proposal = specifications[edge]
            elif vzx.is_node_realised(source) and vzx.is_node_realised(target):
                proposal = PathSpecification(
                    source_cube = min(vzx.get_realising_cubes(source)),
                    target_cube = min(vzx.get_realising_cubes(target)),
                    pipes = [ vzx.get_edge_type(source, target) ]
                )
            else:
                proposal = None

            console.debug(f"> Proposal considered : {proposal}")

            if proposal is not None and vzx.is_path_valid(source, target, proposal):
                console.debug(f"Realisation: {source} -> {target} [{vzx.get_edge_type(source, target)}]")
                vzx.realise_edge(source, target, proposal)