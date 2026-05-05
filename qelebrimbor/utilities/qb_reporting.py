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

from termcolor import colored

from qelebrimbor import inflaters
from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeType
from qelebrimbor.common.components import ZxEdge
from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.utilities.cycle_analyser import CycleAnalyser
from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

import logging
console = logging.getLogger(__name__)


def __get_insufficient_ports_rate(graph: VolumetricZxGraph) -> float:
    all_realised_spiders = set(filter(
        lambda zxn: zxn.is_realised() and zxn.type in { NodeType.X, NodeType.Z },
        graph.get_zx_nodes()
    ))
    cubes_with_insufficient_ports: int = 0
    for node in all_realised_spiders:
        unrealised_edges = sum(
            1 for neighbor in graph.get_zx_neighbors(node) if not graph.get_zx_edge(node.id, neighbor.id).is_realised()
        )
        cube = node.realising_cube
        open_ports = sum(
            1 for position in SpacetimeHelper.get_constellation(cube.position, cube.kind.get_reach())
            if not graph.spacetime.is_occupied(position)
        )
        if open_ports < unrealised_edges:
            console.debug(f"Node {node} has insufficient ports [ue:{unrealised_edges}, op:{open_ports}]")
            cubes_with_insufficient_ports += 1
    return cubes_with_insufficient_ports / len(all_realised_spiders)

def __get_unrealised_endpoints_rate(graph: VolumetricZxGraph, unrealised: int) -> float:
    if not (0 <= unrealised <= 2):
        raise Exception(f"Requested invalid number of unrealised endpoints [{unrealised}]")

    all_unrealised_edges = set(filter(
        lambda zxe: not zxe.is_realised(),
        graph.get_zx_edges()
    ))

    unrealised_endpoints: int = 0
    for edge in all_unrealised_edges:
        if (0 if edge.source.is_realised() else 1) + (0 if edge.target.is_realised() else 1) == unrealised:
            unrealised_endpoints += 1

    return unrealised_endpoints / len(all_unrealised_edges)

def __format_percentage(value: float | None, optimum: float, increase: bool = False) -> str:
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

    if increase:
        output = '+' + output

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

    insufficient_ports_rate = __format_percentage(
        value = __get_insufficient_ports_rate(graph = vzx), optimum = 0.0
    )

    unrealised_0_endpoints_rate = __format_percentage(
        value = __get_unrealised_endpoints_rate(graph = vzx, unrealised = 0), optimum = 0.0
    )
    unrealised_1_endpoints_rate = __format_percentage(
        value = __get_unrealised_endpoints_rate(graph = vzx, unrealised = 1), optimum = 0.0
    )
    unrealised_2_endpoints_rate = __format_percentage(
        value = __get_unrealised_endpoints_rate(graph = vzx, unrealised = 2), optimum = 0.0
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
        value = inflation_rate, optimum = 0.0, increase = True
    )
    spider_count: int = sum(1 for zxn in vzx.get_zx_nodes() if zxn.type in { NodeType.X, NodeType.Z })
    overall_inflation_rate: str | None = __format_percentage(
        value = inflation_rate * spider_volume / spider_count if inflation_rate else None, optimum = 0.0, increase = True
    )

    cnrr = __format_percentage(value=CycleAnalyser.cycle_node_realisation_rate(graph=vzx), optimum=1.0)
    cerr = __format_percentage(value=CycleAnalyser.cycle_edge_realisation_rate(graph=vzx), optimum=1.0)

    if detailed:
        print(f"Inflation runtime: {"{:.6f}".format(runtime)} seconds.")

        print(f"Realised cycles:")
        print(f"> Cycle Node Realisation Rate : {cnrr}")
        print(f"> Cycle Edge Realisation Rate : {cerr}")

        print(f"Realised nodes: {realised_nodes} / {vzx.number_of_nodes()} [{node_realisation_rate}]")
        print(f"> Insufficient Ports Rate   : {insufficient_ports_rate}")
        print(f"Realised edges: {realised_edges} / {vzx.number_of_edges()} [{edge_realisation_rate}]")
        print(f"> Unrealised Endpoints Rate (0/1/2) : {unrealised_0_endpoints_rate}/{unrealised_1_endpoints_rate}/{unrealised_2_endpoints_rate}")

        print(f"Complete volume : {total_volume}")
        print(f"> Spider Volume : {spider_volume}")
        print(f"> Excess Volume : +{excess_volume}")

        print(f"Partial Inflation Rate : {partial_inflation_rate}")
        print(f"Overall Inflation Rate : {overall_inflation_rate}")
    else:
        summary  = f"RUN:{"{:.2f}".format(runtime).rjust(6, ' ')} seconds, "
        summary += f"CNRR:{cnrr}, "
        summary += f"CERR:{cerr}, "
        summary += f"OIR:{overall_inflation_rate}, "
        summary += f"PIR:{partial_inflation_rate}, "
        summary += f"NRR:{node_realisation_rate}, "
        summary += f"ERR:{edge_realisation_rate}, "
        summary += f"IPR:{insufficient_ports_rate}, "
        summary += f"UER(0/1/2):{unrealised_0_endpoints_rate}/{unrealised_1_endpoints_rate}/{unrealised_2_endpoints_rate}, "
        summary += f"TV:{str(total_volume).rjust(4, ' ')}, "
        summary += f"SV:{str(spider_volume).rjust(4, ' ')}, "
        summary += f"EV:{str(excess_volume).rjust(4, ' ')}"
        print(summary)