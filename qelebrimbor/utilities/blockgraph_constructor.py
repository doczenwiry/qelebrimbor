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
        for edge, proposal in specifications.items():
            source, target = edge

            zx_edge = graph.get_zx_edge(*edge)
            if zx_edge.is_realised():
                console.warning(f"Edge: {source} -> {target} is already realised : {zx_edge.realisation}")
                continue

            console.info(f"Realisation of edge {zx_edge}")
            console.info(f"> Proposal : {proposal}")
            if graph.is_path_valid(source, target, proposal):
                graph.realise_zx_edge(source, target, proposal)
            else:
                raise Exception(f"> Invalid path proposal for edge {edge} [{proposal}]")