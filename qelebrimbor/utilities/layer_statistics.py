from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph, LayerTransition


def get_layer_density(graph: VolumetricZxGraph, layer: int) -> tuple[int,int]:
    number_of_nodes = sum(1 for _ in graph.get_zx_nodes(layer = layer))
    number_of_edges = sum(1 for _ in graph.get_zx_edges(layered = (layer, LayerTransition.INTRA)))

    return number_of_nodes, number_of_edges
