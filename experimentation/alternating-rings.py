from qelebrimbor.augmented_zx_graph import AugmentedZxGraph
from qelebrimbor.common.components_zx import NodeType, EdgeType
from qelebrimbor.vedo.azg_viewer import AugmentedZxGraphViewer
from qelebrimbor.vedo.zx_layout.cycle import CycleLayout


def generate_ring(order: int) -> AugmentedZxGraph:
    n = 2 * order
    nodes = [ (s, NodeType.X if s % 2 == 0 else NodeType.Z) for s in range(n) ]
    edges = [ ( (s,(s+1) % n), EdgeType.IDENTITY) for s in range(n) ]
    return AugmentedZxGraph(nodes, edges)

ORDER = 4

if __name__ == "__main__":
    ring = generate_ring(order = ORDER)

    viewer = AugmentedZxGraphViewer(ring, f"ring, n={2 * ORDER}", CycleLayout(ring))
    viewer.display()