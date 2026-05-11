#   Copyright 2026 Seweryn Dynerowicz
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import argparse

from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.vedo.zx_layout.circuit import CircuitLayout
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

from qelebrimbor.formats.vzx import VZX

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

    print(f"Visualisation of {args.filepath}.")

    use_ang_format: bool
    if args.filepath.endswith(".vzx"):
        use_ang_format = False
    elif args.filepath.endswith(".ang"):
        use_ang_format = True
    else:
        raise Exception(f"Unknown file type: {args.filepath} [must be *.vzx or *.ang]")

    vzx: VolumetricZxGraph = VZX.from_file(args.filepath, ang_format = use_ang_format)
    # vzx.print_summary()

    excess_volume = 0
    for edge in vzx.get_zx_edges():
        volume = len(list(edge.realisation)) - 1
        if volume > 0:
            print(f"Edge {edge} [+v={volume}] : {list(edge.realisation)}")
        excess_volume += volume

    boundaries = sum(1 for _ in vzx.get_bg_cubes(kind = CubeKind.OOO))
    print(f"Total volume : {vzx.number_of_cubes() - boundaries}")
    print(f"Excess volume: +{excess_volume}")

    circuit_layout = CircuitLayout(vzx, vertical =len(vzx.get_zx_qubits()) < len(vzx.get_zx_layers()))
    viewer = VolumetricZxGraphViewer(vzx, label = args.filepath, layout = circuit_layout, size = window_size)
    viewer.display()