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

from itertools import product

import pyzx
from pyzx import EdgeType, VertexType

from qelebrimbor.formats.preprocessing.abstract import Preprocessor


class BialgebraReduction(Preprocessor):
    @staticmethod
    def __connected(zxg: pyzx.graph.base.BaseGraph, z: int, x: int) -> bool:
        return zxg.connected(z, x) and zxg.edge_type(zxg.edge(z, x)) == EdgeType.SIMPLE

    @staticmethod
    def detect(zxg: pyzx.graph.base.BaseGraph) -> tuple[list[int], list[int]] | None:
        # TODO: detect largest pattern for applying the bialgebra reduction rule (K_{m,n} -> single edge)
        #       start from answer to https://cs.stackexchange.com/a/131087 (version: 2020-10-11)
        z_spiders = list(filter(lambda vt: zxg.type(vt) == VertexType.Z, zxg.vertices()))
        x_spiders = list(filter(lambda vt: zxg.type(vt) == VertexType.X, zxg.vertices()))

        all_edges = product(z_spiders, x_spiders)
        for z, x in filter(lambda p: BialgebraReduction.__connected(zxg, *p), all_edges):
            z_neighbors = list(filter(lambda n: n != x, zxg.neighbors(z)))
            x_neighbors = list(filter(lambda n: n != z, zxg.neighbors(x)))

            for nz, nx in filter(lambda p: BialgebraReduction.__connected(zxg, *p), product(z_neighbors, x_neighbors)):
                return [z, nx], [x, nz]

        return None

    # The following method is based on the trick used by Austin Fowler to transform the Steane Code for 7 qubits
    # cfr. https://docs.google.com/presentation/d/184GHX9jffq9dcwWzbku0K90V9xdA8_25lD8pfeEcgRg
    # > The simplification on slides 82-88 leverages the bi-algebra rule to simplify the ZX-graph further.
    # > The bialgebra rule can be used to remove any instance of K_{m,n} that appears in the ZX-graph.
    # > This becomes a powerful tool to planarize a ZX-graph !
    @staticmethod
    def reduce(zxg: pyzx.graph.base.BaseGraph, zs: list[int], xs: list[int]) -> None:
        if any(not zxg.connected(z, x) for z, x in product(zs, xs)):
            raise Exception("All zs and xs must be connected.")

        for z in zs:
            p = zxg.add_vertex(ty=VertexType.Z)
            for neighbor in list(filter(lambda nb: nb not in xs, zxg.neighbors(z))):
                zxg.remove_edge((z, neighbor))
                zxg.add_edge((p, neighbor))
            zxg.add_edge((z, p))

        for x in xs:
            p = zxg.add_vertex(ty=VertexType.X)
            for neighbor in list(filter(lambda nb: nb not in zs, zxg.neighbors(x))):
                zxg.remove_edge((x, neighbor))
                zxg.add_edge((p, neighbor))
            zxg.add_edge((x, p))

        pyzx.simplify.bialg_op_simp.apply(zxg, list(zs + xs))
        pyzx.simplify.id_simp(zxg)

    @staticmethod
    def process(graph: pyzx.graph.base.BaseGraph, limit: int | None = None) -> pyzx.graph.base.BaseGraph:
        reduced = graph.clone()

        count: int = 0
        while limit is None or count < limit:
            pattern = BialgebraReduction.detect(reduced)
            if pattern is None:
                break

            BialgebraReduction.reduce(reduced, *pattern)
            count += 1

        return reduced
