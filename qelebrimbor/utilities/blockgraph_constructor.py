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
    def realise(graph: VolumetricZxGraph,
            nodes_specifications: dict[NodeId, BgCube],
            edges_specifications: dict[EdgeId, PathSpecification]
    ):
        BlockGraphConstructor.realise_nodes(graph, nodes_specifications)
        BlockGraphConstructor.realise_edges(graph, edges_specifications)

    @staticmethod
    def realise_nodes(graph: VolumetricZxGraph, specifications: dict[NodeId, BgCube]):
        for node in graph.get_zx_nodes():
            if not node.is_realised() and node.id in specifications:
                console.debug(f"Node: {node} -> {specifications[node.id]}")
                graph.realise_zx_node(node, specifications[node.id])

    @staticmethod
    def realise_edges(graph: VolumetricZxGraph, specifications: dict[EdgeId, PathSpecification]):
        for edge in graph.edges:
            source, target = edge

            if graph.is_zx_edge_realised(*edge):
                console.debug(f"Edge: {source} -> {target} is already realised : {graph.get_zx_edge(source, target).realisation}")
                continue

            if edge in specifications:
                proposal = specifications[edge]

                console.info(f"Realisation: {source} -> {target} [{graph.get_zx_edge(source, target).type}]")
                console.info(f"> Proposal for edge {source}-{target} : {proposal}")
                if graph.is_path_valid(source, target, proposal):
                    console.info(f"> Proposal: {proposal}")
                    graph.realise_zx_edge(source, target, proposal)
                # else:
                #     alternative = PathSpecification(
                #         source_cube = proposal.source_cube, target_cube = proposal.target_cube,
                #         extras = list(reversed(proposal.extras)), pipes = list(reversed(proposal.pipes))
                #     )
                #     if graph.is_path_valid(source, target, alternative):
                #         console.info(f"> Alternative: {alternative}")
                #         graph.realise_zx_edge(source, target, alternative)
                else:
                    raise Exception(f"> Invalid path proposal for {source}-{target} : {proposal}")