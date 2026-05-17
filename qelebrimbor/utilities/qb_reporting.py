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
import math

from termcolor import colored

from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType, NodeType
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.helpers.spacetime import SpacetimeHelper

console = logging.getLogger(__name__)


def __get_insufficient_ports_rate(graph: VolumetricZxGraph) -> tuple[int, float]:
    all_realised_spiders = set(
        filter(
            lambda zxn: zxn.is_realised() and zxn.type in {NodeType.X, NodeType.Z},
            graph.get_zx_nodes(),
        )
    )
    if len(all_realised_spiders) == 0:
        return 0, 0.0

    cubes_with_insufficient_ports: int = 0
    for node in all_realised_spiders:
        unrealised_edges = sum(
            1 for neighbor in graph.get_zx_neighbors(node) if not graph.get_zx_edge(node.id, neighbor.id).is_realised()
        )
        cube = node.realising_cube
        open_ports = sum(
            1
            for position in SpacetimeHelper.get_constellation(cube.position, cube.kind.get_reach())
            if not graph.spacetime.occupied(position)
        )
        if open_ports < unrealised_edges:
            console.debug(f"Node {node} has insufficient ports [ue:{unrealised_edges}, op:{open_ports}]")
            cubes_with_insufficient_ports += 1
    return cubes_with_insufficient_ports, cubes_with_insufficient_ports / len(all_realised_spiders)


def __get_unrealised_endpoints_rate(graph: VolumetricZxGraph, unrealised: int) -> float:
    if not (0 <= unrealised <= 2):
        raise Exception(f"Requested invalid number of unrealised endpoints [{unrealised}]")

    all_unrealised_edges = set(filter(lambda zxe: not zxe.is_realised(), graph.get_zx_edges()))

    if len(all_unrealised_edges) == 0:
        return 0.0

    unrealised_endpoints: int = 0
    for edge in all_unrealised_edges:
        if (0 if edge.source.is_realised() else 1) + (0 if edge.target.is_realised() else 1) == unrealised:
            unrealised_endpoints += 1

    return unrealised_endpoints / len(all_unrealised_edges)


def __format_percentage(
    value: float | None, optimum: float | None = None, lower_better: bool = False, inflation: bool = False
) -> str:
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
        if inflation and value is not None:
            if value > 0.0:
                printed = "+" + printed
        output = f"{printed.rjust(7, ' ')}%"

    if optimum is not None and value is not None:
        if lower_better:
            color = "green" if value <= optimum else "red"
        else:
            color = "green" if optimum <= value else "red"
        output = colored(output, color, attrs=["bold"], force_color=True)

    return output


def print_report(vzx: VolumetricZxGraph, input_spider_count: int, cycles: list[ZxCycle], detailed: bool = True):
    realised_nodes: int = sum(1 for node in vzx.get_zx_nodes() if node.is_realised())
    realised_edges: int = sum(1 for edge in vzx.get_zx_edges() if edge.is_realised())
    node_realisation_rate: str = __format_percentage(
        realised_nodes / vzx.number_of_nodes(), optimum=1.0, lower_better=False
    )
    edge_realisation_rate: str = __format_percentage(
        realised_edges / vzx.number_of_edges(), optimum=1.0, lower_better=False
    )

    insufficient_ports_count, rate = __get_insufficient_ports_rate(graph=vzx)
    insufficient_ports_rate = __format_percentage(value=rate, optimum=0.0, lower_better=True)

    unrealised_0_endpoints_rate = __format_percentage(
        value=__get_unrealised_endpoints_rate(graph=vzx, unrealised=0), optimum=0.0, lower_better=True
    )
    unrealised_1_endpoints_rate = __format_percentage(
        value=__get_unrealised_endpoints_rate(graph=vzx, unrealised=1), optimum=0.0, lower_better=True
    )
    unrealised_2_endpoints_rate = __format_percentage(
        value=__get_unrealised_endpoints_rate(graph=vzx, unrealised=2), optimum=0.0, lower_better=True
    )

    total_volume = vzx.volume()
    spider_count: int = sum(1 for zxn in vzx.get_zx_nodes() if zxn.type in {NodeType.X, NodeType.Z})
    spider_volume: int = sum(
        1
        for _ in filter(
            lambda bgc: bgc.kind not in [CubeKind.OOO, CubeKind.YYY],
            vzx.get_bg_cubes(),
        )
    )
    excess_volume: int = spider_volume - spider_count
    achieved_inflation_rate: str | None = __format_percentage(
        value=(total_volume - input_spider_count) / input_spider_count,
        optimum=0.0,
        inflation=True,
        lower_better=True,
    )

    # Every cycle of four nodes will require two extra cubes to be realised
    excess_required = sum(2 for cycle in cycles if len(cycle) == 4)
    # Every node with more than four legs will need to be unfused so that every cube has no more than four pipes
    for node in vzx.get_zx_nodes():
        degree = vzx.get_zx_degree(node.id)
        if degree > 4:
            excess_required += (degree - 4 + (degree % 2)) // 2
    required_inflation_rate = __format_percentage(excess_required / spider_count, lower_better=True, inflation=True)

    internal_inflation_rate: str | None = __format_percentage(
        value=excess_volume / spider_count, optimum=(excess_required / spider_count), lower_better=True, inflation=True
    )

    if detailed:
        print("> Realisation of input ZX-graph: ")

        realised_nodes_dict: dict[NodeType, int] = {
            nodetype: sum(1 for node in vzx.get_zx_nodes(node_type=nodetype) if node.is_realised())
            for nodetype in NodeType
            if vzx.number_of_zx_nodes(node_type=nodetype) > 0
        }
        breakdown = "/".join(
            str(nodetype)
            + ":"
            + __format_percentage(
                value=count / vzx.number_of_zx_nodes(node_type=nodetype)
                if vzx.number_of_zx_nodes(node_type=nodetype) != 0.0
                else None,
                optimum=1.0,
                lower_better=False,
            )
            for nodetype, count in realised_nodes_dict.items()
        )
        print(
            f">> Nodes realised : {sum(realised_nodes_dict.values())}/{vzx.number_of_nodes()} [{node_realisation_rate}]; {breakdown}"  # noqa: E501
        )
        print(
            f">>> Insufficient ports : {insufficient_ports_count}/{vzx.number_of_nodes()} [{insufficient_ports_rate}]"
        )

        realised_edges_dict: dict[EdgeType, int] = {
            edgetype: sum(1 for node in vzx.get_zx_edges(edge_type=edgetype) if node.is_realised())
            for edgetype in EdgeType
            if vzx.number_of_zx_edges(edge_type=edgetype) > 0
        }
        breakdown = ",".join(
            str(edgetype)
            + ":"
            + __format_percentage(
                value=count / vzx.number_of_zx_edges(edge_type=edgetype)
                if vzx.number_of_zx_edges(edge_type=edgetype) != 0.0
                else None,
                optimum=1.0,
                lower_better=False,
            )
            for edgetype, count in realised_edges_dict.items()
        )
        print(
            f">> Edges realised : {sum(realised_edges_dict.values())}/{vzx.number_of_edges()} [{edge_realisation_rate}]; {breakdown}"  # noqa: E501
        )

        print(
            f"> Unrealised Endpoints Rate (0/1/2) : {unrealised_0_endpoints_rate}/{unrealised_1_endpoints_rate}/{unrealised_2_endpoints_rate}"  # noqa: E501
        )

        volume_digits = int(math.log10(total_volume)) + 1 if total_volume > 0 else 0
        print(
            f"> {colored('Total volume', attrs=['underline'], force_color=True)}   :  {str(total_volume).rjust(volume_digits, ' ')}"  # noqa: E501
        )
        # print(f">> Spider Volume :  {str(spider_volume).rjust(volume_digits, ' ')}")
        # print(f">> Excess Volume : +{str(excess_volume).rjust(volume_digits, ' ')}")

        print(f"> Internal Inflation Rate : {internal_inflation_rate} [required:{required_inflation_rate}]")
        print(
            f"> {colored('Achieved Inflation Rate', attrs=['underline'], force_color=True)} : {achieved_inflation_rate}"
        )
    else:
        summary = f"NRR:{node_realisation_rate}, "
        summary += f"ERR:{edge_realisation_rate}, "
        summary += f"AIR:{achieved_inflation_rate}, "
        summary += f"IIR:{internal_inflation_rate}, "
        summary += f"RIR:{required_inflation_rate}, "
        summary += f"IPR:{insufficient_ports_rate}, "
        summary += (
            f"UER(0/1/2):{unrealised_0_endpoints_rate}/{unrealised_1_endpoints_rate}/{unrealised_2_endpoints_rate}, "
        )
        summary += f"SC:{str(input_spider_count).rjust(4, ' ')}, "
        summary += f"TV:{str(total_volume).rjust(4, ' ')}, "
        print(summary)
