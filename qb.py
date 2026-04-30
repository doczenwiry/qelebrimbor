import os
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

    root = max(vzx.get_zx_nodes(), key = lambda zxn: vzx.get_zx_degree(zxn.id))
    inflater = ZxGraphInflater(vzx)
    inflater.process(vzx, root = root)

    if args.output_pyzx:
        pyzx_output = vzx.into_pyzx_graph()
        output = os.path.splitext(args.filepath)[0] + str("-compiled.json")
        console.info(f"Writing to {output} from {args.filepath}")
        with open(output, 'w') as file:
            file.write(pyzx_output.to_json())

    if args.validation:
        pyzx_output = vzx.into_pyzx_graph()
        # TODO: understand why the following two are needed
        pyzx_input.auto_detect_io()
        pyzx_output.auto_detect_io()
        console.info(f"Validation : {pyzx.compare_tensors(pyzx_input, pyzx_output)}")

    if args.visualization:
        window_size = "full" if args.fullscreen else "auto"
        viewer = VolumetricZxGraphViewer(vzx, label = args.filepath, size = window_size)
        viewer.display()
