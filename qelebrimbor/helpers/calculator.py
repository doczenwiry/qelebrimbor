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

import numpy as np

from qelebrimbor.common.attributes_bg import CubeKind
from qelebrimbor.common.attributes_zx import NodeType, EdgeType
from qelebrimbor.common.components import BgCube
from qelebrimbor.helpers.spacetime import SpacetimeHelper


class ManhattanCalculator:
    @staticmethod
    def manhattan_distance(source: BgCube, target: BgCube) -> int:
        return sum([ abs(s - o) for s, o in zip(source.position, target.position) ])

    @staticmethod
    def minimal_manhattan_volume(source: BgCube, target: BgCube) -> int:
        return ManhattanCalculator.minimal_manhattan_length(source, target) + 1

    @staticmethod
    def minimal_manhattan_chain(source: BgCube, target: BgCube, node_type_restrictions: list[NodeType]) -> int:
        number_of_restrictions = len(node_type_restrictions)
        minimal_manhattan_length = ManhattanCalculator.minimal_manhattan_length(source, target)

        if number_of_restrictions < minimal_manhattan_length:
            return minimal_manhattan_length
        else:
            # TODO: validate this
            excess = 1 if (number_of_restrictions % 2 == minimal_manhattan_length % 2) else 0
            return number_of_restrictions + excess

    @staticmethod
    def minimal_manhattan_length(source: BgCube, target: BgCube) -> int:
        return source.position.get_manhattan_distance(target.position) + ManhattanCalculator.minimal_manhattan_excess(source, target)

    @staticmethod
    def minimal_manhattan_excess(source: BgCube, target: BgCube) -> int:
        if source.kind in [ CubeKind.OOO , CubeKind.YYY ] or target.kind in [ CubeKind.OOO , CubeKind.YYY ]:
            raise NotImplementedError(f"Computation only implemented for NodeType X & Z.")

        excess = 0

        source_reach = source.kind.get_reach()
        target_reach = target.kind.get_reach()

        manhattan = source.position.get_manhattan_distance(target.position)
        relative = target.position - source.position

        if np.sign( source_reach.dot(relative) ) == -1:
            source_reach *= -1
        if np.sign( target_reach.dot(relative) ) == -1:
            target_reach *= -1

        # TODO: work out the formalisation and justification of the cases for all the overhead values.
        if source.kind == target.kind:
            if manhattan >= 1 and relative == source_reach.scale(manhattan):
                excess += 2

            if manhattan >= 2:
                if any(relative == source_reach.scale(manhattan - 1) + step
                       for step in SpacetimeHelper.get_step_constellation(source_reach)
                ):
                    excess += 2

            if manhattan >= 3:
                if any(relative == source_reach.scale(manhattan-2) + step + source_reach.cross(step)
                       for step in SpacetimeHelper.get_step_constellation(source_reach)
                ):
                    excess += 2
        else:
            differences = source.kind.differences(target.kind)
            excess += sum(2 for i in range(3) if differences[i] == 1 and relative[i] == 0)
            if manhattan == 1:
                if source.kind.get_type() == target.kind.get_type():
                    excess += 2
                elif source_reach == target_reach != relative:
                    excess += 2
            elif manhattan == 2 and source.kind.get_type() != target.kind.get_type():
                if source_reach == target_reach != relative and source_reach.dot(relative) == 0 and relative.dot(relative) != 4:
                    excess += 2

        return excess

    @staticmethod
    def minimal_manhattan_excess_prefix(source: BgCube, target: BgCube, restrictions: list[NodeType]) -> int:
        if source.kind in [ CubeKind.OOO , CubeKind.YYY ] or target.kind in [ CubeKind.OOO , CubeKind.YYY ]:
            raise NotImplementedError(f"Computation only implemented for NodeType X & Z.")

        if source.position.get_manhattan_distance(target.position) - 1 < len(restrictions):
            raise ValueError(f"Computation only implemented for ")

        excess = 0

        

        return excess