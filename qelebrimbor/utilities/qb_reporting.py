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
from mypy.types import PartialType
from termcolor import colored

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeType
from qelebrimbor.common.components import ZxEdge
from qelebrimbor.utilities.cycle_analyser import CycleAnalyser
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph


def __format_percentage(value: float | None, optimum: float) -> str:
    if value is None:
        output = "  n/a  "
    else:
        rounded = round(100.0 * value, 2)
        if 0.0 < value < 0.0001:
            printed = "0.01"
        elif 0.9999 < value < 1.0:
            printed = "99.99"
        else:
            printed = "{:.2f}".format(rounded)
        output = f"{printed.rjust(6, ' ')}%"

    if value == optimum:
        output = colored(output, 'green', attrs = ['bold'], force_color = True)
    else:
        output = colored(output, 'red', attrs = ['bold'], force_color = True)

    return output

def print_report(vzx: VolumetricZxGraph, runtime: float, report: dict[str, list[ZxEdge]] | None, detailed: bool = True):
    realised_nodes: int = sum(1 for node in vzx.get_zx_nodes() if node.is_realised())
    realised_edges: int = sum(1 for edge in vzx.get_zx_edges() if edge.is_realised())
    node_realisation_rate: str = __format_percentage(realised_nodes / vzx.number_of_nodes(), optimum = 1.0)
    edge_realisation_rate: str = __format_percentage(realised_edges / vzx.number_of_edges(), optimum = 1.0)

    due_to_insufficient_ports = __format_percentage(
        value = len(report["insufficient-ports"]) / vzx.number_of_edges() if report else 0.0, optimum = 0.0
    )

    due_to_disconnected_component = __format_percentage(
        value = len(report["disconnected-component"]) / vzx.number_of_edges() if report else 0.0, optimum = 0.0
    )

    total_volume = vzx.volume()
    spider_volume: int = sum(1 for _ in filter(
        lambda bgc: bgc.kind not in [CubeKind.OOO , CubeKind.YYY] and bgc.realised_node is not None,
        vzx.get_bg_cubes()
    ))
    excess_volume: int = sum(
        1 for cube in vzx.get_bg_cubes() if cube.kind not in [CubeKind.OOO , CubeKind.YYY] and cube.realised_node is None
    )
    inflation_rate: float | None = excess_volume / spider_volume if spider_volume > 0.0 else None
    partial_inflation_rate: str | None = __format_percentage(
        value = inflation_rate, optimum = 0.0
    )
    spider_count: int = sum(1 for zxn in vzx.get_zx_nodes() if zxn.type in { NodeType.X, NodeType.Z })
    overall_inflation_rate: str | None = __format_percentage(
        value = inflation_rate * spider_volume / spider_count if inflation_rate else None, optimum = 0.0
    )

    cnrr = __format_percentage(value=CycleAnalyser.cycle_node_realisation_rate(graph=vzx), optimum=1.0)
    cerr = __format_percentage(value=CycleAnalyser.cycle_edge_realisation_rate(graph=vzx), optimum=1.0)

    if detailed:
        print(f"Inflation runtime: {"{:.6f}".format(runtime)} seconds.")

        print(f"Realised cycles:")
        print(f"> Cycle Node Realisation Rate : {cnrr}")
        print(f"> Cycle Edge Realisation Rate : {cerr}")

        print(f"Realised nodes: {realised_nodes} / {vzx.number_of_nodes()} [{node_realisation_rate}]")
        print(f"Realised edges: {realised_edges} / {vzx.number_of_edges()} [{edge_realisation_rate}]")
        print(f"> Insufficient Ports     : {due_to_insufficient_ports}")
        print(f"> Disconnected Component : {due_to_disconnected_component}")

        print(f"Complete volume : {total_volume}")
        print(f"> Spider Volume : {spider_volume}")
        print(f"> Excess Volume : +{excess_volume}")

        print(f"Partial Inflation Rate : +{partial_inflation_rate}")
        print(f"Overall Inflation Rate : +{overall_inflation_rate}")
    else:
        summary  = f"RUN:{"{:.2f}".format(runtime).rjust(6, ' ')} seconds, "
        summary += f"CNRR: {cnrr}, "
        summary += f"CERR: {cerr}, "
        summary += f"OIR:+{overall_inflation_rate}, "
        summary += f"PIR:+{partial_inflation_rate}, "
        summary += f"NRR:{node_realisation_rate}, "
        summary += f"ERR:{edge_realisation_rate}, "
        summary += f"IPR:{due_to_insufficient_ports}, "
        summary += f"DCR:{due_to_disconnected_component}, "
        summary += f"TV:{str(total_volume).rjust(4, ' ')}, "
        summary += f"SV:{str(spider_volume).rjust(4, ' ')}, "
        summary += f"EV:{str(excess_volume).rjust(4, ' ')}"
        print(summary)