from qelebrimbor.common.components import ZxNode, ZxEdge
from qelebrimbor.common.attributes_zx import NodeId
import qelebrimbor.volumetric_zx_graph as vzg


class NoMoreThanFourLegsConstraint:
    @staticmethod
    def enforce(graph: vzg.VolumetricZxGraph):
        """Ensures that all spiders of a VolumetricZxGraph have at most four legs (i.e. No-More-Than-Four-Legs).
            N.B. the provided graph is altered by this method to perform the enforcing.

        Args:
            graph: A VolumetricZxGraph

        Returns:
            graph: An equivalent (under spider fusion) VolumetricZxGraph with every node having at most four edges.

        """

        # Process all zx-nodes with more than four zx-edges
        for node in filter(lambda nd: graph.degree[nd] > 4, graph.nodes):
            neighbors = graph.neighbors(node)
            degree = graph.degree[node]
            zx_node = graph.get_zx_node(node)

            remaining_neighbors = degree - 3
            next(neighbors); next(neighbors); next(neighbors)
            previous = node
            while remaining_neighbors > 0:
                extra_id = graph.number_of_nodes()

                graph.add_node(extra_id)
                extra_node = graph.nodes[extra_id]
                extra_zx_node = ZxNode(id = extra_id, type = zx_node.type, qubit = zx_node.qubit, layer = zx_node.layer)
                extra_node[vzg.VolumetricZxGraph.KEY_ZX_NODE] = extra_zx_node

                # Make zx-edge between previous node of chain and new extra_node
                graph.add_edge(previous, extra_id)

                neighbors_to_graft = remaining_neighbors if remaining_neighbors <= 3 else 2
                for _ in range(neighbors_to_graft):
                    neighbor_id: NodeId = next(neighbors)
                    edge_type = graph.get_zx_edge(extra_id, neighbor_id).type

                    graph.remove_edge(node, neighbor_id)
                    source, target = (extra_id, neighbor_id) if extra_id < neighbor_id else neighbor_id, extra_id
                    graph.add_edge(extra_id, neighbor_id)
                    graph.edges[extra_id, neighbor_id][vzg.VolumetricZxGraph.KEY_ZX_EDGE] = ZxEdge(source, target, edge_type)
                    # extra_edge[vzg.VolumetricZxGraph.KEY_ZX_EDGE_TYPE] = edge_type
                    # extra_edge[vzg.VolumetricZxGraph.KEY_ZX_EDGE_BG_PATH] = []

                remaining_neighbors -= neighbors_to_graft
                previous = extra_id

        return graph