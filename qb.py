from os import path
import pyzx
from argparse import ArgumentParser
from time import time

from qelebrimbor.inflaters.breadth_first_search import ZxGraphInflaterBFS
from qelebrimbor.inflaters.least_remaining_ports import ZxGraphInflaterPorts
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
logging.basicConfig(level=logging.WARNING)
console = logging.getLogger(__name__)
logging.getLogger("qelebrimbor.pathfinders.depth_first_search").setLevel(logging.CRITICAL)

parser = ArgumentParser(
    prog = "qb",
    description = "A tool to construct a Volumetric ZX-graph (a.k.a. BlockGraph) from an input ZX-graph. Currently accepted files are *.json containing a PyZX graph in JSON format."
)
parser.add_argument('filepath', help = "path to the file containing the input ZX-graph.")
parser.add_argument('-V', '--validation', action = 'store_true', help = "validate equivalence of the final construct against the input ZX-graph.")
parser.add_argument('-v', '--visualization', action='store_true', help = "display the visualisation of the constructed Volumetric ZX-graph at the end of the construction.")
parser.add_argument('-f', '--fullscreen', action='store_true', help = "display the visualisation in a fullscreen window.")
parser.add_argument('--output_pyzx', action = 'store_true', help = "write the constructed Volumetric ZX-graph as a PyZX graph into a *.json file.")
args = parser.parse_args()

if __name__ == "__main__":
    args = parser.parse_args()

    if args.filepath is None:
        raise Exception("Filepath to a *.json file required.")

    with open(args.filepath, 'r') as file:
        pyzx_input = pyzx.Graph().from_json(file.read())

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_input)

    start = time()

    # try:
    root = max(vzx.get_zx_nodes(), key = lambda zxn: vzx.get_zx_degree(zxn.id))
    inflater = ZxGraphInflaterPorts(vzx)
    inflater.process(vzx, root = root)
    # except Exception as e:
    #     console.error(f"Exception: {e}")

    final = time()

    console.info(f"Time to Inflate: {final - start} seconds")

    unrealised_edges = sum(1 for edge in vzx.get_zx_edges() if not edge.is_realised())
    console.info(f"Unrealised edges: {unrealised_edges} / {vzx.number_of_edges()}")

    if args.output_pyzx:
        pyzx_output = vzx.into_pyzx_graph()
        output = path.splitext(args.filepath)[0] + str("-compiled.json")
        console.info(f"Writing to {output} from {args.filepath}")
        with open(output, 'w') as file:
            file.write(pyzx_output.to_json())

    if args.visualization:
        window_size = "full" if args.fullscreen else "auto"
        viewer = VolumetricZxGraphViewer(vzx, label = args.filepath, size = window_size)
        viewer.display()

    if args.validation:
        pyzx_output = vzx.into_pyzx_graph()
        # TODO: fix the labelling of BOUNDARIES in vzx.into_pyzx_graph(..) to match that of pyzx_input
        pyzx_input.auto_detect_io()
        pyzx_output.auto_detect_io()

        composition = pyzx_input.copy()
        composition.compose(pyzx_output.adjoint())
        pyzx.full_reduce(composition)
        console.info(f"Validation : {composition.is_id()}")