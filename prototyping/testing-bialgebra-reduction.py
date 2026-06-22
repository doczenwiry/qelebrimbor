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

import itertools

import pyzx
from pyzx import VertexType


# The following method is based on the trick used by Austin Fowler to transform the Steane Code for 7 qubits
# cfr. https://docs.google.com/presentation/d/184GHX9jffq9dcwWzbku0K90V9xdA8_25lD8pfeEcgRg/edit?usp=sharing
# > The simplification on slides 82-88 leverages the bi-algebra rule to .
# > The bialgebra rule can be used to remove any instance of K_{m,n} that appears in the ZX-graph.
def perform_bialgebra_reduction(graph: pyzx.graph.base.BaseGraph, zs: list[int], xs: list[int]) -> None:
    if any(not graph.connected(z, x) for z, x in itertools.product(zs, xs)):
        raise Exception("All zs and xs must be connected.")

    for z in zs:
        p = graph.add_vertex(ty=VertexType.Z)
        for neighbor in list(filter(lambda nb: nb not in xs, graph.neighbors(z))):
            graph.remove_edge((z, neighbor))
            graph.add_edge((p, neighbor))
        graph.add_edge((z, p))

    for x in xs:
        p = graph.add_vertex(ty=VertexType.X)
        for neighbor in list(filter(lambda nb: nb not in zs, graph.neighbors(x))):
            graph.remove_edge((x, neighbor))
            graph.add_edge((p, neighbor))
        graph.add_edge((x, p))

    pyzx.simplify.bialg_op_simp.apply(graph, list(zs + xs))
    pyzx.simplify.id_simp(graph)


def detect_bialgebra_pattern(graph: pyzx.graph.base.BaseGraph) -> tuple[list[int], list[int]]:
    zs: list[int] = []
    xs: list[int] = []

    # TODO: implement detection of largest pattern for applying the bialgebra reduction rule (K_{m,n} -> single edge)

    return zs, xs


if __name__ == "__main__":
    with open("../assets/pyzx/steane/steane-code-qubits7.json", "r") as file:
        graph = pyzx.Graph().from_json(file.read())
        pyzx.draw(graph, labels=True)
        pyzx.full_reduce(graph)
        pyzx.to_rg(graph)
        graph.pack_circuit_rows()
        pyzx.draw(graph, labels=True)
        perform_bialgebra_reduction(graph, zs=[7, 17], xs=[9, 11])
        # PYZX.into_file(graph, "../prototyping/output.json")
        pyzx.draw(graph, labels=True)
