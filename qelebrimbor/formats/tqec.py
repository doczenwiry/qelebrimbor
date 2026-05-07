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

from qelebrimbor.core.components import BgCube
from qelebrimbor.core.attributes_bg import CubeKind
from qelebrimbor.core.attributes_zx import EdgeType
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph


class TQEC:
    @staticmethod
    def __infer_pipe_kind(graph: VolumetricZxGraph, source: BgCube, target: BgCube) -> str:
        # cellcolors are for faces (X, Y, Z) +  'h' if Hadamard pipe
        colors = ""
        distances = target.position - source.position
        for c in range(3):
            if distances[c] == 0 and (
                    source.kind not in [CubeKind.OOO, CubeKind.YYY] or target.kind not in [CubeKind.OOO, CubeKind.YYY]):
                color = source.kind.name[c] if source.kind not in [CubeKind.OOO, CubeKind.YYY] else target.kind.name[c]
            else:
                color = 'o'
            colors += color

        if graph.get_bg_pipe(source.id, target.id).type == EdgeType.HADAMARD:
            colors += 'h'

        return colors.lower()

    @staticmethod
    def __format_label(graph: VolumetricZxGraph, cube: BgCube):
        label = ""
        if cube.kind == CubeKind.OOO and cube.realised_node is not None:
            zx_node = cube.realised_node
            if zx_node.layer == 0:
                label = f"in_{zx_node.qubit}"
            elif zx_node.layer == len(graph.get_zx_layers()) - 1:
                label = f"out_{zx_node.qubit}"
        return label

    @staticmethod
    def into_tqec_file(graph: VolumetricZxGraph, filepath: str):
        with (open(filepath, 'w') as file):
            file.write(f"BLOCKGRAPH 0.0.1\n")

            # Store cube information
            file.write("\nCUBES: index;x;y;z;kind;label;\n")
            file.writelines(
                [
                    f"{cube.id};{';'.join(map(str, iter(cube.position)))};{cube.kind.name.lower()};{TQEC.__format_label(graph, cube)};\n"
                    for cube in graph.get_bg_cubes()
                ]
            )

            # Store pipe information
            file.write("\nPIPES: src;tgt;kind;\n")
            file.writelines(
                [
                    f"{pipe.source.id};{pipe.target.id};{TQEC.__infer_pipe_kind(graph, pipe.source, pipe.target)};\n"
                    for pipe in graph.get_bg_pipes()
                ]
            )