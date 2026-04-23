import argparse
import sys

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.vedo.zx_layout.circuit import CircuitLayout
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    prog = "qb-viewer",
    description = "A tool to visualize jointly the ZX-graph and its BG-graph stored in a file. Accepted files can be either in *.vzx or *.ang format."
)
parser.add_argument('filepath', help = "path to the file to visualize")
parser.add_argument('-f', '--fullscreen', action='store_true', help = "display the visualisation in fullscreen mode")
args = parser.parse_args()

if __name__ == '__main__':
    args = parser.parse_args()

    if args.filepath is None:
        raise Exception("Filepath to a *.vzx or *.ang file required.")

    window_size = "full" if args.fullscreen else "auto"

    console.info(f"Visualisation of {args.filepath}.")

    vzx: VolumetricZxGraph
    if args.filepath.endswith(".vzx"):
        vzx = VolumetricZxGraph.from_file(args.filepath)
    elif args.filepath.endswith(".ang"):
        vzx = VolumetricZxGraph.from_topologiq_file(args.filepath)
    else:
        raise Exception(f"Unknown file type: {args.filepath} [must be *.vzx or *.ang]")

    vzx.log_summary()

    excess_volume = 0
    for edge in vzx.get_zx_edges():
        console.info(f"Edge {edge} : {list(edge.realisation)}")
        volume = len(list(edge.realisation)) - 1
        if volume > 0:
            console.info(f"Edge {edge} [+v={volume}] : {list(edge.realisation)}")
        excess_volume += volume

    boundaries = len(list(vzx.get_bg_cubes(kind= CubeKind.OOO)))
    console.info(f"Total volume : {vzx.number_of_cubes() - boundaries}")
    console.info(f"Excess volume: +{excess_volume}")

    circuit_layout = CircuitLayout(vzx, vertical =len(vzx.get_zx_qubits()) < len(vzx.get_zx_layers()))
    viewer = VolumetricZxGraphViewer(vzx, label = args.filepath, layout = circuit_layout, size = window_size)
    viewer.display()