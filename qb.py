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

from os import path
import pyzx
from argparse import ArgumentParser
from time import time
import networkx as nx


from qelebrimbor.common.components import ZxEdge
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.inflaters.breadth_first_search import ZxGraphInflaterBFS
from qelebrimbor.inflaters.least_remaining_ports import ZxGraphInflaterPorts
from qelebrimbor.inflaters.rings import ZxGraphInflaterRings
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer
from qelebrimbor.vedo.zx_layout.circuit import CircuitLayout
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
logging.basicConfig(level=logging.INFO)
console = logging.getLogger("qelebrimbor")
# logging.getLogger("qelebrimbor.pathfinders.depth_first_search").setLevel(logging.CRITICAL)
# logging.getLogger("qelebrimbor.inflaters.least_remaining_ports").setLevel(logging.INFO)

parser = ArgumentParser(
    prog = "qb",
    description = "A tool to construct a Volumetric ZX-graph (a.k.a. BlockGraph) from an input ZX-graph. Currently accepted files are *.json containing a PyZX graph in JSON format."
)
parser.add_argument('filepath', help = "path to the file containing the input ZX-graph.")
parser.add_argument('-c', '--check-equivalence', action = 'store_true', help = "check equivalence of the final construct against the input ZX-graph.")
parser.add_argument('-v', '--visualization', action='store_true', help = "display the visualisation of the constructed Volumetric ZX-graph at the end of the construction.")
parser.add_argument('-V', '--force-visualization', action='store_true', help = "force the visualisation for constructed Volumetric ZX-graph with more than 100 cubes.")
parser.add_argument('-f', '--fullscreen', action='store_true', help = "display the visualisation in a fullscreen window.")
parser.add_argument('-w', '--write-construct', action='store_true', help = "write the constructed Volumetric ZX-graph to a file.")
parser.add_argument('-s', '--summary', action='store_true', help = "print a summary of the construction process.")
parser.add_argument('-r', '--report', action='store_true', help = "print a detailed report of the construction process.")
parser.add_argument('--output_pyzx', action = 'store_true', help = "write the constructed Volumetric ZX-graph as a PyZX graph into a *.json file.")
args = parser.parse_args()

def __format_percentage(value: float  | None) -> str:
    if value is None:
        return "n/a %"
    else:
        rounded = round(100.0 * value, 1)
        if 0.0 < value < 0.0001:
            printed = "0.01"
        elif 0.9999 < value < 1.0:
            printed = "99.99"
        else:
            printed = str(rounded)
        return f"{printed}%"

def main():
    args = parser.parse_args()

    if args.filepath is None:
        raise Exception("Filepath to a *.json file required.")

    with open(args.filepath, 'r') as file:
        pyzx_input = pyzx.Graph().from_json(file.read())

    vzx = VolumetricZxGraph.from_pyzx_graph(pyzx_input)

    start = time()

    inflater = ZxGraphInflaterPorts(graph = vzx)
    report: dict[str, list[ZxEdge]] = inflater.process()

    final = time()
    runtime = round(final - start, 6)

    realised_nodes: int = sum(1 for node in vzx.get_zx_nodes() if node.is_realised())
    realised_edges: int = sum(1 for edge in vzx.get_zx_edges() if edge.is_realised())
    node_realisation_rate: float = realised_nodes / vzx.number_of_nodes()
    edge_realisation_rate: float = realised_edges / vzx.number_of_edges()

    due_to_insufficient_ports: float | None = None
    due_to_disconnected_component: float | None = None
    if report is not None:
        due_to_insufficient_ports = len(report["insufficient-ports"]) / vzx.number_of_edges()
        due_to_disconnected_component = len(report["disconnected-component"]) / vzx.number_of_edges()

    spider_volume: int = sum(1 for _ in filter(
        lambda bgc: bgc.kind not in [CubeKind.OOO , CubeKind.YYY] and bgc.realised_node is not None,
        vzx.get_bg_cubes()
    ))
    excess_volume: int = sum(
        1 for cube in vzx.get_bg_cubes() if cube.kind not in [CubeKind.OOO , CubeKind.YYY] and cube.realised_node is None
    )
    inflation_rate: float | None = excess_volume / spider_volume if spider_volume > 0.0 else None

    if args.report:
        print(f"Input file : {args.filepath}")
        print(f"Inflation runtime: {runtime} seconds.")
        print(f"Realised nodes: {realised_nodes} / {vzx.number_of_nodes()} [{__format_percentage(node_realisation_rate)}]")
        print(f"Realised edges: {realised_edges} / {vzx.number_of_edges()} [{__format_percentage(edge_realisation_rate)}]")

        if report is not None:
            print(f"> Insufficient ports     : {__format_percentage(due_to_insufficient_ports)}")
            print(f"> Disconnected component : {__format_percentage(due_to_disconnected_component)}")

        print(f"Complete volume  : {vzx.volume()}")
        print(f"> Spider volume : {spider_volume}")
        print(f"> Excess volume : +{excess_volume}")
        print(f"INFLATION RATE  : +{__format_percentage(inflation_rate)}")

    elif args.summary:
        summary  = f"Summary for {args.filepath}; "
        summary += f"Runtime:{runtime} seconds, "
        summary += f"NRR:{__format_percentage(node_realisation_rate)}, "
        summary += f"ERR:{__format_percentage(edge_realisation_rate)}, "
        if report is not None:
            summary += f"IPR:{__format_percentage(due_to_insufficient_ports)}, "
            summary += f"DCR:{__format_percentage(due_to_disconnected_component)}, "
        summary += f"IR:+{__format_percentage(inflation_rate)}"
        print(summary)

    if args.output_pyzx:
        pyzx_output = vzx.into_pyzx_graph()
        output = path.splitext(args.filepath)[0] + str("-compiled.json")
        print(f"Writing to {output} from {args.filepath}")
        with open(output, 'w') as file:
            file.write(pyzx_output.to_json())

    if args.visualization or args.force_visualization:
        if args.force_visualization or vzx.volume() <= 100:
            window_size = "full" if args.fullscreen else "auto"
            layout = CircuitLayout(vzx, vertical=len(vzx.get_zx_qubits()) < len(vzx.get_zx_layers()))
            viewer = VolumetricZxGraphViewer(vzx, label = args.filepath, layout = layout, size = window_size)
            viewer.display()
        else:
            print("> Visualization of a VolumetricZxGraph with more than 100 cubes is slow (Override with -V).")

    if args.check_equivalence:
        pyzx_output = vzx.into_pyzx_graph()
        # TODO: fix the labelling of BOUNDARIES in vzx.into_pyzx_graph(..) to match that of pyzx_input
        pyzx_input.auto_detect_io()
        pyzx_output.auto_detect_io()

        composition = pyzx_input.copy()
        composition.compose(pyzx_output.adjoint())
        pyzx.full_reduce(composition)
        equivalent_graphs = "SUCCESS" if composition.is_id() else "FAILURE"
        print(f"Equivalence between input and output ZX-graphs : {equivalent_graphs}")

if __name__ == "__main__":
    main()