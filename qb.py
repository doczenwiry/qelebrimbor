import networkx as nx
import pyzx
import argparse

from qelebrimbor.inflater import ZxGraphInflater
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)
logging.getLogger("qelebrimbor.pathfinders.depth_first_search").setLevel(logging.INFO)

parser = argparse.ArgumentParser(
    prog = "qb",
    description = "A tool to construct a Volumetric ZX-graph (a.k.a. BlockGraph) from an input ZX-graph. Currently accepted files are *.json containing a PyZX graph."
)
parser.add_argument('filepath', help = "path to the file containing the input ZX-graph.")
parser.add_argument('-v', '--visualization', action='store_true', help = "display the visualisation of the constructed Volumetric ZX-graph.")
parser.add_argument('-f', '--fullscreen', action='store_true', help = "display the visualisation in a fullscreen window.")
args = parser.parse_args()

if __name__ == "__main__":
    args = parser.parse_args()

    if args.filepath is None:
        raise Exception("Filepath to a *.json file required.")

    with open(args.filepath, 'r') as file:
        pyzx_input = pyzx.Graph().from_json(file.read())

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_input)
    vzx.print_summary()

    root = max(vzx.get_zx_nodes(), key = lambda zxn: vzx.get_zx_degree(zxn.id))
    ZxGraphInflater.process(vzx, root = root)

    if args.visualization:
        window_size = "full" if args.fullscreen else "auto"
        viewer = VolumetricZxGraphViewer(vzx, label = args.filepath, size = window_size)
        viewer.display()
