import qelebrimbor.volumetric_zx_graph as vzx


class NoMoreThanFourLegsConstraint:
    @staticmethod
    def enforce(graph: vzx.VolumetricZxGraph):
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
            node_type = graph.get_node_type(node)
            node_qubit = graph.get_node_qubit(node)
            node_layer = graph.get_node_layer(node)

            remaining_neighbors = degree - 3
            next(neighbors); next(neighbors); next(neighbors)
            previous = node
            while remaining_neighbors > 0:
                extra_node_id = graph.number_of_nodes()

                graph.add_node(extra_node_id)
                extra_node = graph.nodes[extra_node_id]
                extra_node[vzx.VolumetricZxGraph.KEY_ZX_NODE_TYPE] = node_type
                extra_node[vzx.VolumetricZxGraph.KEY_ZX_NODE_QUBIT] = node_qubit
                extra_node[vzx.VolumetricZxGraph.KEY_ZX_NODE_LAYER] = node_layer
                extra_node[vzx.VolumetricZxGraph.KEY_ZX_NODE_BG_CUBES] = set()

                # Make zx-edge between previous node of chain and new extra_node
                graph.add_edge(previous, extra_node_id)

                neighbors_to_graft = remaining_neighbors if remaining_neighbors <= 3 else 2
                for _ in range(neighbors_to_graft):
                    neighbor = next(neighbors)
                    edge_type = graph.get_edge_type(extra_node_id, neighbor)

                    graph.remove_edge(node, neighbor)
                    graph.add_edge(extra_node_id, neighbor)
                    extra_edge = graph.edges[extra_node_id, neighbor]
                    extra_edge[vzx.VolumetricZxGraph.KEY_ZX_EDGE_TYPE] = edge_type
                    extra_edge[vzx.VolumetricZxGraph.KEY_ZX_EDGE_BG_PATH] = []

                remaining_neighbors -= neighbors_to_graft
                previous = extra_node_id

        return graph