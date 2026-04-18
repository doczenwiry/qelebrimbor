from qelebrimbor.pathfinders.pathfinder_dfs import PathFinderDFS
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.common.attributes_zx import NodeId, EdgeId, EdgeType
from qelebrimbor.common.attributes_bg import CubeId, CubeKind
from qelebrimbor.common.coordinates import Coordinates
from qelebrimbor.common.paths import PathSpecification

import logging
console = logging.getLogger(__name__)

class BlockGraphConstructor:
    @staticmethod
    def realise(vzx: VolumetricZxGraph,
                nodes_specifications: dict[NodeId, tuple[CubeKind, Coordinates]],
                edges_specifications: dict[EdgeId, PathSpecification | None]
                ):
        BlockGraphConstructor.realise_nodes(vzx, nodes_specifications)
        BlockGraphConstructor.realise_edges(vzx, edges_specifications)

    @staticmethod
    def realise_nodes(vzx: VolumetricZxGraph, specifications: dict[NodeId, tuple[CubeKind, Coordinates]]):
        for node in vzx.nodes:
            if not vzx.is_zx_node_realised(node) and node in specifications:
                vzx.realise_zx_node(node, *specifications[node])

    @staticmethod
    def connect_cubes(vzx: VolumetricZxGraph, endpoints: list[tuple[CubeId, CubeId]]):
        for source, target in endpoints:
            start_cube = vzx.get_bg_cube(source)
            final_cube = vzx.get_bg_cube(target)
            start = (start_cube.kind, start_cube.position)
            final = (final_cube.kind, final_cube.position)
            minimal_overhead, paths = PathFinderDFS.find_minimal_paths(start, final, occupied_positions = vzx.occupied)
            path = paths[0]
            proposal = PathSpecification(
                start_cube.id, final_cube.id,
                extras = path.cubes[1:-1],
                pipes = [ EdgeType.IDENTITY for _ in range(len(path.cubes) - 1) ]
            )

            # if vzx.is_path_valid(source, target, proposal):
            vzx.connect_path(proposal)

    @staticmethod
    def realise_edges(vzx: VolumetricZxGraph, specifications: dict[EdgeId, PathSpecification | None]):
        for edge in vzx.edges:
            source, target = edge

            if vzx.is_zx_edge_realised(*edge):
                console.warning(f"Edge: {source} -> {target} is already realised : {vzx.get_zx_edge(source, target).realisation}")
                continue

            if edge in specifications:
                proposal = specifications[edge]
            elif vzx.is_zx_node_realised(source) and vzx.is_zx_node_realised(target):
                source_cube = vzx.get_bg_cube(vzx.get_zx_node(source).realising_cube)
                target_cube = vzx.get_bg_cube(vzx.get_zx_node(target).realising_cube)
                if source_cube.kind in [ CubeKind.OOO, CubeKind.YYY ]:
                    start = (target_cube.kind, target_cube.position)
                    final = (source_cube.kind, source_cube.position)
                else:
                    start = (source_cube.kind, source_cube.position)
                    final = (target_cube.kind, target_cube.position)
                minimal_overhead, paths = PathFinderDFS.find_minimal_paths(start, final, occupied_positions = vzx.occupied)
                path = paths[0]
                proposal = PathSpecification(
                    source_cube.id, target_cube.id,
                    extras = path.cubes[1:-1],
                    pipes = [ vzx.get_zx_edge(source_cube.realised_node, target_cube.realised_node).type for _ in range(len(path.cubes) - 1) ]
                )
            else:
                proposal = None

            console.debug(f"> Proposal for edge {source}-{target} : {proposal.extras if proposal else None}")

            if proposal is not None:
                if vzx.is_path_valid(source, target, proposal):
                    console.debug(f"Realisation: {source} -> {target} [{vzx.get_zx_edge(source, target).type}]")
                    vzx.realise_zx_edge(source, target, proposal)
                else:
                    console.error(f"Proposal {source}{vzx.get_zx_edge(source,target).type.name[0]}{target} is invalid : {proposal.extras}")