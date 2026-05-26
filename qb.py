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

import logging
import sys
from argparse import ArgumentParser
from os import path
from time import time

import pyzx
from termcolor import colored

from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.analysis.vzx_analyser import VolumetricZxGraphAnalyser
from qelebrimbor.core.zx import attributes as zx_attributes
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.formats.preprocessing.cycle_untangler import CycleUntangler
from qelebrimbor.formats.preprocessing.full_reduce import FullReduce
from qelebrimbor.formats.pyzx import PYZX
from qelebrimbor.formats.tqec import TQEC
from qelebrimbor.formats.vzx import VZX
from qelebrimbor.inflaters.rings import ZxGraphInflaterRings
from qelebrimbor.inflaters.trees import ZxGraphInflaterTrees
from qelebrimbor.utilities.qb_reporting import print_report
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.circuit import CircuitLayout
from qelebrimbor.vedo.zx_layout.planar import PlanarLayout

logging.basicConfig(level=logging.CRITICAL)

parser = ArgumentParser(
    prog="qb",
    description="A tool to construct a Volumetric ZX-graph (a.k.a. BlockGraph) from an input ZX-graph. Currently accepted files are *.json containing a PyZX graph in JSON format.",  # noqa: E501
)

parser.add_argument(
    "-a",
    "--analysis",
    action="store_true",
    help="only report the preliminary analysis of the input ZX-graph.",
)
parser.add_argument(
    "-A",
    "--analysis-style",
    choices=["text", "plot"],
    default="text",
    help="controls whether to report the analysis in text of plot form.",
)
parser.add_argument(
    "-c",
    "--check-equivalence",
    action="store_true",
    default=True,
    help="check equivalence of the final construct against the input ZX-graph.",
)
parser.add_argument(
    "-f",
    "--fullscreen",
    action="store_true",
    help="display the visualisation in a fullscreen window.",
)
parser.add_argument(
    "-i",
    "--index",
    action="store",
    type=int,
    default=-1,
    help="index of the step at which to stop the inflation process.",
)
parser.add_argument(
    "-p",
    "--output-pyzx",
    action="store_true",
    help="save the Volumetric ZX-graph as a PyZX graph to a *.pyzx.json file.",
)
parser.add_argument(
    "-r",
    "--preprocessor",
    action="store",
    choices=["none", "full-reduce", "default"],
    default="default",
    help="choose which preprocessor to use on the input ZX-graph.",
)
parser.add_argument(
    "-s",
    "--summary",
    action="store_true",
    help="print a summary of the construction process.",
)
parser.add_argument(
    "-t",
    "--output-tqec",
    action="store_true",
    help="save the Volumetric ZX-graph to a *.tqec file.",
)
parser.add_argument(
    "-v",
    "--visualization",
    action="store_true",
    help="display the visualisation of the constructed Volumetric ZX-graph at the end of the construction.",
)
parser.add_argument(
    "-V",
    "--force-visualization",
    action="store_true",
    help="force the visualisation for constructed Volumetric ZX-graph with more than 100 cubes.",
)
parser.add_argument(
    "-w",
    "--output-vzx",
    action="store_true",
    help="save the Volumetric ZX-graph to a *.vzx file.",
)
parser.add_argument(
    "-z",
    "--zx-coloring",
    action="store_true",
    help="toggles the coloring of ZX-types in the terminal.",
)
parser.add_argument("filepath", help="path to the file containing the input ZX-graph.")
args = parser.parse_args()


def main() -> int:
    arguments = parser.parse_args()

    if arguments.filepath is None:
        raise Exception("Filepath to a *.json file required.")

    verbose: bool = not arguments.summary

    pyzx_input = PYZX.from_file(arguments.filepath)
    input_spider_count: int = sum(
        1 for node in pyzx_input.vertices() if pyzx_input.type(node) in [pyzx.VertexType.X, pyzx.VertexType.Z]
    )

    if arguments.zx_coloring:
        zx_attributes.ZX_COLORING = True

    # Preliminary analysis stage.
    if verbose:
        print("ANALYSIS STAGE.")
        print(f"> Input file : {arguments.filepath}")
        start = time()
        vzx = PYZX.from_pyzx_graph(pyzx_input)
        VolumetricZxGraphAnalyser.report(graph=vzx)
        runtime = round(time() - start, 2)
        print(f"> Completed in {'{:.2f}'.format(runtime)} seconds.")

    # Preprocessing stage.
    pyzx_internal: pyzx.graph.base.BaseGraph = PYZX.from_file(arguments.filepath)
    if verbose:
        print("\nPREPROCESSING STAGE.")

    start = time()

    if arguments.preprocessor != "none":
        if verbose:
            print(f"> Applying preprocessor : {FullReduce.__name__}")
        FullReduce.process(pyzx_internal)

        if arguments.preprocessor == "default":
            if verbose:
                print(f"> Applying preprocessor : {CycleUntangler.__name__}")
            CycleUntangler.process(pyzx_internal)

    vzx = PYZX.from_pyzx_graph(pyzx_internal)
    cycles: list[ZxCycle]

    if verbose:
        VolumetricZxGraphAnalyser.report(graph=vzx)
        cycles = CycleAnalyser.analyse(graph=vzx, minimal=True, plot=arguments.analysis_style == "plot")
        runtime = round(time() - start, 2)
        print(f"> Completed in {'{:.2f}'.format(runtime)} seconds.")
    else:
        cycles = CycleAnalyser.decompose(graph=vzx, minimal=True)

    if arguments.output_pyzx:
        output = path.splitext(arguments.filepath)[0] + str(".internal.json")
        if verbose:
            print(f"> Writing PyZX internal to {output}")

        PYZX.into_file(pyzx_internal, output)

    if arguments.analysis:
        return 0

    # Inflation stage
    if verbose:
        print("\nINFLATION STAGE.")

    ring_inflater = ZxGraphInflaterRings(graph=vzx, cycles=cycles, verbose=verbose)

    if verbose:
        print("> " + colored(f"Phase  I : {ring_inflater.__class__.__name__}", attrs=["underline"], force_color=True))

    sys.stdout.flush()
    sys.stderr.flush()

    start = time()
    ring_inflater_realisations: int
    try:
        ring_inflater_realisations = ring_inflater.process(abort_on_index=arguments.index)
    except Exception as e:
        print(colored("FAILURE [Rings] :", color="red", attrs=["underline"], force_color=True) + f" {e}")
        if verbose:
            raise e
        else:
            exit(-1)
    runtime = round(time() - start, 6)

    if verbose:
        print(f">> Total runtime : {'{:.3f}'.format(runtime)}s")

    tree_inflater = ZxGraphInflaterTrees(graph=vzx, verbose=verbose)
    if verbose:
        print("> " + colored(f"Phase II : {tree_inflater.__class__.__name__}", attrs=["underline"], force_color=True))

    sys.stdout.flush()
    sys.stderr.flush()

    if ring_inflater_realisations > 0:
        start = time()
        try:
            tree_inflater.process(abort_on_index=arguments.index)
        except Exception as e:
            print(colored("FAILURE [Trees] :", color="red", attrs=["underline"], force_color=True) + f" {e}")
            if verbose:
                raise e
            else:
                exit(-1)
        runtime = round(time() - start, 6)

        if verbose:
            print(f">> Total runtime : {'{:.3f}'.format(runtime)}s")
    else:
        if verbose:
            print(">> Inflation aborted.")

    sys.stdout.flush()
    sys.stderr.flush()

    # Reporting stage
    if verbose:
        print("\nREPORTING STAGE.")
    else:
        print(f"RUN:{'{:.3f}'.format(runtime).rjust(6, ' ')}s,", end=" ")
    print_report(vzx, input_spider_count=input_spider_count, cycles=cycles, detailed=verbose)

    # Outputting stage
    if arguments.output_pyzx or arguments.output_tqec or arguments.output_vzx:
        if verbose:
            print("\nOUTPUTTING STAGE.")
        if arguments.output_pyzx:
            output = path.splitext(arguments.filepath)[0] + str(".compiled.json")
            if verbose:
                print(f"> Writing PyZX compiled to {output}")

            pyzx_output = PYZX.into_pyzx_graph(vzx)
            # Reset the inputs/outputs identification that was lost in the construction process.
            if all(node.is_realised() for node in vzx.get_zx_nodes()):
                pyzx_output.set_inputs(pyzx_input.inputs())
                pyzx_output.set_outputs(pyzx_input.outputs())
                pyzx_output.normalize()

            PYZX.into_file(pyzx_output, output)

        if arguments.output_tqec:
            output = path.splitext(arguments.filepath)[0] + str(".tqec")
            if verbose:
                print(f"> Writing TQEC output to {output}.")
            TQEC.into_tqec_file(vzx, output)

        if arguments.output_vzx:
            output = path.splitext(arguments.filepath)[0] + str(".vzx")
            if verbose:
                print(f"> Writing VZX output to {output}.")
            VZX.into_file(vzx, output)

    # Validation stage
    if arguments.check_equivalence:
        if verbose:
            print("\nEQUIVALENCE VALIDATION STAGE.")

        if all(node.is_realised() for node in vzx.get_zx_nodes()) and all(
            edge.is_realised() for edge in vzx.get_zx_edges()
        ):
            pyzx_output = PYZX.into_pyzx_graph(vzx)
            # Reset the inputs/outputs identification that was lost in the construction process.
            pyzx_output.set_inputs(pyzx_input.inputs())
            pyzx_output.set_outputs(pyzx_input.outputs())
            pyzx_output.normalize()

            method = "iCwAI"
            try:
                composition = pyzx_input.copy()
                composition.compose(pyzx_output.adjoint())
                pyzx.full_reduce(composition)
                validation_successful = composition.is_id()
            except Exception:
                validation_successful = None

            if validation_successful is False and pyzx_input.qubit_count() <= 8:
                try:
                    method = "CT"
                    validation_successful = pyzx.compare_tensors(pyzx_input, pyzx_output)
                except Exception:
                    validation_successful = None

            if validation_successful is None:
                status, color = ("EXCEPTION", "yellow")
            elif validation_successful:
                status, color = ("SUCCESS", "green")
            else:
                status, color = ("FAILURE", "red")
        else:
            status, color = ("FAILURE", "red")
            method = "COMPL"

        equivalent_graphs = colored(status, color, attrs=["bold"], force_color=True)

        if verbose:
            print(f"> Is input equivalent to output [method:{method}] ? {equivalent_graphs}")
        else:
            print(f"EQUIVALENCE-{method.upper()}:{equivalent_graphs}")

    # Visualisation stage
    if arguments.visualization or arguments.force_visualization:
        if arguments.force_visualization or vzx.volume() <= 100:
            window_size = "full" if arguments.fullscreen else "auto"
            viewer = VolumetricZxGraphViewer(
                graph=vzx,
                label=arguments.filepath,
                size=window_size,
                cycles=cycles,
                layout=PlanarLayout(vzx, scale=3.0) if arguments.preprocessor != "none" else CircuitLayout(vzx),
            )
            viewer.display()
        elif verbose:
            print("> Visualization of a VolumetricZxGraph with more than 100 cubes is slow (Override with -V).")

    return 0


if __name__ == "__main__":
    main()
