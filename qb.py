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

import sys
from os import path
from argparse import ArgumentParser
from time import time
import pyzx

from qelebrimbor.core import attributes_zx

from qelebrimbor.formats.pyzx import PYZX
from qelebrimbor.formats.tqec import TQEC
from qelebrimbor.formats.vzx import VZX

from qelebrimbor.analysis.analyser import VolumetricZxGraphAnalyser

from qelebrimbor.inflaters.rings import ZxGraphInflaterRings
from qelebrimbor.inflaters.breadth_first_search import ZxGraphInflaterBFS

from qelebrimbor.utilities.qb_reporting import print_report

from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

import logging
logging.basicConfig(level=logging.INFO)

parser = ArgumentParser(
    prog = "qb",
    description = "A tool to construct a Volumetric ZX-graph (a.k.a. BlockGraph) from an input ZX-graph. Currently accepted files are *.json containing a PyZX graph in JSON format."
)

parser.add_argument('-a', '--analysis', action ='store_true', help = "only report the preliminary analysis of the input ZX-graph.")
parser.add_argument('-A', '--analysis-style', choices = ['text', 'plot'], default = 'text', help = "controls whether to report the analysis in text of plot form.")
parser.add_argument('-c', '--check-equivalence', action = 'store_true', help = "check equivalence of the final construct against the input ZX-graph.")
parser.add_argument('-f', '--fullscreen', action='store_true', help = "display the visualisation in a fullscreen window.")
parser.add_argument('-p', '--output-pyzx', action = 'store_true', help = "save the Volumetric ZX-graph as a PyZX graph to a *.pyzx.json file.")
parser.add_argument('-s', '--summary', action='store_true', help = "print a summary of the construction process.")
parser.add_argument('-t', '--output-tqec', action = 'store_true', help = "save the Volumetric ZX-graph to a *.tqec file.")
parser.add_argument('-v', '--visualization', action='store_true', help = "display the visualisation of the constructed Volumetric ZX-graph at the end of the construction.")
parser.add_argument('-V', '--force-visualization', action='store_true', help = "force the visualisation for constructed Volumetric ZX-graph with more than 100 cubes.")
parser.add_argument('-w', '--output-vzx', action='store_true', help = "save the Volumetric ZX-graph to a *.vzx file.")
parser.add_argument('-z', '--zx-coloring', action='store_true', help = "toggles the coloring of ZX-types in the terminal.")
parser.add_argument('filepath', help = "path to the file containing the input ZX-graph.")
args = parser.parse_args()

def main():
    arguments = parser.parse_args()

    if arguments.filepath is None:
        raise Exception("Filepath to a *.json file required.")

    vzx = PYZX.from_file(arguments.filepath)

    if arguments.zx_coloring:
        attributes_zx.ZX_COLORING = True

    # Preliminary analysis stage
    zx_cycles, components_count = VolumetricZxGraphAnalyser.analyse(vzx, plot = arguments.analysis_style == 'plot')

    if arguments.analysis:
        return 0

    # Inflation stage
    if len(zx_cycles) > 0:
        inflater = ZxGraphInflaterRings(graph = vzx, cycles = zx_cycles)
    else:
        print("WARNING: The input ZX-graph has no cycles: cannot use Rings strategy. Falling back to BFS.")
        inflater = ZxGraphInflaterBFS(graph = vzx)

    sys.stdout.flush()
    sys.stderr.flush()

    start = time()
    inflater.process()
    final = time()
    runtime = round(final - start, 6)

    sys.stdout.flush()
    sys.stderr.flush()

    # Reporting stage
    if arguments.summary:
        print_report(vzx, runtime, inflater, detailed = False)
    else:
        print_report(vzx, runtime, inflater)

    # Outputting stage
    if arguments.output_pyzx:
        output = path.splitext(arguments.filepath)[0] + str(".compiled.json")
        print(f"Writing PyZX output to {output}")
        PYZX.into_file(vzx, output)

    if arguments.output_tqec:
        output = path.splitext(arguments.filepath)[0] + str(".tqec")
        print(f"Writing TQEC output to {output}.")
        TQEC.into_tqec_file(vzx, output)

    if arguments.output_vzx:
        output = path.splitext(arguments.filepath)[0] + str(".vzx")
        print(f"Writing VZX output to {output}.")
        VZX.into_file(vzx, output)

    # Equivalence checking stage
    if arguments.check_equivalence:
        with open(arguments.filepath, 'r') as file:
            pyzx_input = pyzx.Graph().from_json(file.read())
        pyzx_output = PYZX.into_pyzx_graph(vzx)
        # TODO: fix the labelling of BOUNDARIES in vzx.into_pyzx_graph(..) to match that of pyzx_input
        pyzx_input.auto_detect_io()
        pyzx_output.auto_detect_io()

        try:
            composition = pyzx_input.copy()
            composition.compose(pyzx_output.adjoint())
            pyzx.full_reduce(composition)
            equivalent_graphs = "SUCCESS" if composition.is_id() else "FAILURE"
        except TypeError:
            equivalent_graphs = "FAILURE"
        print(f"Equivalence between input and output ZX-graphs [composition-with-adjoint method] : {equivalent_graphs}")

    # Visualisation stage
    if arguments.visualization or arguments.force_visualization:
        if arguments.force_visualization or vzx.volume() <= 100:
            window_size = "full" if arguments.fullscreen else "auto"
            viewer = VolumetricZxGraphViewer(vzx, label = arguments.filepath, size = window_size)
            viewer.display()
        else:
            print("> Visualization of a VolumetricZxGraph with more than 100 cubes is slow (Override with -V).")

if __name__ == "__main__":
    main()