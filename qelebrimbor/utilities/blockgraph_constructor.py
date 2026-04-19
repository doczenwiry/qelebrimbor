from qelebrimbor.common.components import BgCube
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
                nodes_specifications: dict[NodeId, BgCube],
                edges_specifications: dict[EdgeId, PathSpecification | None]
                ):
        BlockGraphConstructor.realise_nodes(vzx, nodes_specifications)
        BlockGraphConstructor.realise_edges(vzx, edges_specifications)

    @staticmethod
    def realise_nodes(vzx: VolumetricZxGraph, specifications: dict[NodeId, BgCube]):
        for node in vzx.nodes:
            if not vzx.is_zx_node_realised(node) and node in specifications:
                vzx.realise_zx_node(node, specifications[node])

    @staticmethod
    def connect_cubes(vzx: VolumetricZxGraph, endpoints: list[tuple[CubeId, CubeId]]):
        for source, target in endpoints:
            start = vzx.get_bg_cube(source)
            final = vzx.get_bg_cube(target)
            minimal_overhead, paths = PathFinderDFS.find_minimal_paths(start, final, occupied_positions = vzx.occupied)
            path = paths[0]
            proposal = PathSpecification(
                start.id, final.id,
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
                    start = target_cube
                    final = source_cube
                else:
                    start = source_cube
                    final = target_cube
                minimal_overhead, paths = PathFinderDFS.find_minimal_paths(start, final, occupied_positions = vzx.occupied)
                path = paths[0]
                proposal = PathSpecification(
                    start.id, final.id,
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