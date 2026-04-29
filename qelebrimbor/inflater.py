import networkx as nx

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import EdgeType
from qelebrimbor.common.components import ZxNode, BgCube
from qelebrimbor.common.paths import PathSpecification
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.pathfinders.depth_first_search import PathfinderDFS
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger("qelebrimbor.main")

class ZxGraphInflater:
    @staticmethod
    def process(graph: VolumetricZxGraph, root: ZxNode, root_kind: CubeKind | None = None):
        console.info(f"Starting inflation from root {root}")

        node_realisations = 0
        edge_realisations = 0

        # Realise the root of the construction.
        chosen_kind = root_kind if root_kind else CubeKind.suitable_kinds(root.type)[0]
        graph.realise_zx_node(root, BgCube(chosen_kind, SpacetimeHelper.ORIGIN))

        for edge in nx.edge_bfs(graph, root.id):
            console.info(f"> BFS-EDGE : {edge}")
            zx_edge = graph.get_zx_edge(*edge)

            if edge == (113, 112):
                break

            if zx_edge.is_realised():
                continue

            source, target = (zx_edge.source, zx_edge.target) if zx_edge.source.is_realised() else (zx_edge.target, zx_edge.source)

            if source.is_realised() and target.is_realised():
                # Cross-edge
                console.info(f"> Searching edge-realisation : {source} - {target}")

                path = PathfinderDFS.find_optimal_paths(graph, source.realising_cube, target.realising_cube)

                if path is None:
                    console.error(f"Failed to find any path for edge-realisation {source} - {target}")
                    continue

                console.info(f"> Optimal path found : {path}")

                proposal = PathSpecification(
                    source.realising_cube, target.realising_cube,
                    extras=path.extras, pipes=[EdgeType.IDENTITY for _ in range(path.manhattan_length())]
                )
                graph.realise_zx_edge(source.id, target.id, proposal)

                edge_realisations += 1

            elif source.is_realised() or target.is_realised():
                # First-pass
                console.info(f"> Searching node-realisation : {source} - {target}")
                path = PathfinderDFS.find_closest_realisation(graph, source.realising_cube, target)

                if path is None:
                    console.error(f"Failed to find any path for node-realisation {source} - {target}")
                    continue

                console.info(f"> Optimal path found : {path}")

                graph.realise_zx_node(target, path.target)

                proposal = PathSpecification(
                    source.realising_cube, target.realising_cube,
                    extras=path.extras, pipes=[EdgeType.IDENTITY for _ in range(path.manhattan_length())]
                )
                graph.realise_zx_edge(source.id, target.id, proposal)

                node_realisations += 1
            else:
                console.error(f"> Unrealisable edge : {edge}")

        console.info(f"Number of node-realisations: {node_realisations}")
        console.info(f"Number of edge-realisations: {edge_realisations}")

        for edge in graph.get_zx_edges():
            if not edge.is_realised():
                console.warning(f"> Unrealised edge : {edge}")

    @staticmethod
    def __find_node_realisation(vzx: VolumetricZxGraph):
        pass

    @staticmethod
    def __find_edge_realisation(vzx: VolumetricZxGraph):
        pass