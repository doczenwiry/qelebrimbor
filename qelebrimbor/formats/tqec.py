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

from qelebrimbor.core.bg.attributes import CubeKind
from qelebrimbor.core.components import BgCube
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.attributes import EdgeType


class TQEC:
    @staticmethod
    def __infer_pipe_kind(
        graph: VolumetricZxGraph,
        source: BgCube,
        target: BgCube,
    ) -> str:
        # Cell colors are for faces (X, Y, Z) + 'h' if Hadamard pipe.
        colors = ""
        distances = target.position - source.position

        for c in range(3):
            if distances[c] == 0 and (
                source.kind not in [CubeKind.OOO, CubeKind.YYY]
                or target.kind not in [CubeKind.OOO, CubeKind.YYY]
            ):
                color = (
                    source.kind.name[c]
                    if source.kind not in [CubeKind.OOO, CubeKind.YYY]
                    else target.kind.name[c]
                )
            else:
                color = "o"

            colors += color

        if graph.get_bg_pipe(source.id, target.id).type == EdgeType.HADAMARD:
            colors += "h"

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
        with open(filepath, "w") as file:
            file.write("BLOCKGRAPH 0.0.1\n")

            file.write("\nCUBES: index;x;y;z;kind;label;\n")
            file.writelines(
                [
                    f"{cube.id};{';'.join(map(str, iter(cube.position)))};"
                    f"{cube.kind.name.lower()};"
                    f"{TQEC.__format_label(graph, cube)};\n"
                    for cube in graph.get_bg_cubes()
                ]
            )

            file.write("\nPIPES: src;tgt;kind;\n")
            file.writelines(
                [
                    f"{pipe.source.id};{pipe.target.id};"
                    f"{TQEC.__infer_pipe_kind(graph, pipe.source, pipe.target)};\n"
                    for pipe in graph.get_bg_pipes()
                ]
            )

    @staticmethod
    def into_dae_file(
        graph: VolumetricZxGraph,
        filepath: str,
        pipe_length: float = 2.0,
    ) -> None:
        """Export a VolumetricZxGraph to a COLLADA DAE file."""
        import collada
        import numpy as np

        colors = {
            "x": (1.0, 127 / 255, 127 / 255, 1.0),
            "y": (99 / 255, 198 / 255, 118 / 255, 1.0),
            "z": (115 / 255, 150 / 255, 1.0, 1.0),
            "h": (1.0, 1.0, 101 / 255, 1.0),
        }

        mesh = collada.Collada()
        materials = {}

        for name, rgba in colors.items():
            effect = collada.material.Effect(
                f"{name}-effect",
                [],
                "phong",
                diffuse=rgba,
                double_sided=True,
            )
            material = collada.material.Material(
                f"{name}-material",
                name.upper(),
                effect,
            )
            mesh.effects.append(effect)
            mesh.materials.append(material)
            materials[name] = material

        def add_face(
            name,
            center,
            axis,
            sign,
            width,
            height,
            material_name,
        ):
            center = np.asarray(center, dtype=np.float32)

            axes = [0, 1, 2]
            axes.remove(axis)
            a, b = axes

            vertices = np.array(
                [
                    center + np.eye(3)[a] * width / 2
                    + np.eye(3)[b] * height / 2,
                    center - np.eye(3)[a] * width / 2
                    + np.eye(3)[b] * height / 2,
                    center - np.eye(3)[a] * width / 2
                    - np.eye(3)[b] * height / 2,
                    center + np.eye(3)[a] * width / 2
                    - np.eye(3)[b] * height / 2,
                ],
                dtype=np.float32,
            )

            normal = np.zeros(3, dtype=np.float32)
            normal[axis] = sign

            normals = np.array(
                [normal] * 4,
                dtype=np.float32,
            )

            source = collada.source.FloatSource(
                f"{name}-positions",
                vertices,
                ("X", "Y", "Z"),
            )

            normal_source = collada.source.FloatSource(
                f"{name}-normals",
                normals,
                ("X", "Y", "Z"),
            )

            geometry = collada.geometry.Geometry(
                mesh,
                f"{name}-geometry",
                name,
                [source, normal_source],
            )

            input_list = collada.source.InputList()
            input_list.addInput(
                0,
                "VERTEX",
                f"#{source.id}",
            )
            input_list.addInput(
                1,
                "NORMAL",
                f"#{normal_source.id}",
            )

            indices = np.array(
                [0, 1, 2, 0, 2, 3],
                dtype=np.int32,
            )

            triangles = geometry.createTriangleSet(
                indices,
                input_list,
                material_name,
            )

            geometry.primitives.append(triangles)
            mesh.geometries.append(geometry)

            material_node = collada.scene.MaterialNode(
                material_name,
                materials[material_name],
                [],
            )

            return collada.scene.GeometryNode(
                geometry,
                [material_node],
            )

        def cube_color(kind_name):
            for char in kind_name.lower():
                if char in ("x", "y", "z"):
                    return char
            return "z"

        def get_direction(source, target):
            dx = target.position.x - source.position.x
            dy = target.position.y - source.position.y
            dz = target.position.z - source.position.z

            values = (dx, dy, dz)

            for axis, value in enumerate(values):
                if value != 0:
                    return axis, 1 if value > 0 else -1

            raise ValueError("Pipe endpoints must be adjacent.")

        def scaled_position(position):
            scale = 1.0 + pipe_length

            return np.array(
                [
                    position.x * scale,
                    position.y * scale,
                    position.z * scale,
                ],
                dtype=np.float32,
            )

        root = collada.scene.Node("SketchUp")

        cubes = list(graph.get_bg_cubes())
        pipes = list(graph.get_bg_pipes())

        for cube in cubes:
            if cube.kind == CubeKind.OOO:
                continue

            position = scaled_position(cube.position)

            popped_faces = set()

            for pipe in pipes:
                if pipe.source.id == cube.id:
                    axis, sign = get_direction(
                        cube,
                        pipe.target,
                    )
                    popped_faces.add((axis, sign))

                elif pipe.target.id == cube.id:
                    axis, sign = get_direction(
                        cube,
                        pipe.source,
                    )
                    popped_faces.add((axis, sign))

            if cube.kind == CubeKind.YYY:
                z_shift = 0.0

                for pipe in pipes:
                    if pipe.source.id == cube.id:
                        other = pipe.target
                    elif pipe.target.id == cube.id:
                        other = pipe.source
                    else:
                        continue

                    dz = other.position.z - cube.position.z

                    if dz == 1:
                        z_shift = 0.5
                    elif dz == -1:
                        z_shift = -0.5

                position[2] += z_shift

                faces = [
                    (0, -1, 1.0, 0.5),
                    (0, 1, 1.0, 0.5),
                    (1, -1, 0.5, 1.0),
                    (1, 1, 0.5, 1.0),
                    (2, -1, 1.0, 1.0),
                    (2, 1, 1.0, 1.0),
                ]

                for axis, sign, width, height in faces:
                    if (axis, sign) in popped_faces:
                        continue

                    node = add_face(
                        f"yyy-{cube.id}-{axis}-{sign}",
                        position
                        + np.eye(3)[axis] * sign * 0.5,
                        axis,
                        sign,
                        width,
                        height,
                        "y",
                    )

                    root.children.append(node)

                continue

            color = cube_color(cube.kind.name)

            for axis, sign in (
                (0, -1),
                (0, 1),
                (1, -1),
                (1, 1),
                (2, -1),
                (2, 1),
            ):
                if (axis, sign) in popped_faces:
                    continue

                node = add_face(
                    f"cube-{cube.id}-{axis}-{sign}",
                    position
                    + np.eye(3)[axis] * sign * 0.5,
                    axis,
                    sign,
                    1.0,
                    1.0,
                    color,
                )

                root.children.append(node)

        for pipe in pipes:
            source = pipe.source
            target = pipe.target

            axis, sign = get_direction(source, target)

            source_position = scaled_position(source.position)

            kind = TQEC.__infer_pipe_kind(
                graph,
                source,
                target,
            )

            primary_color = "z"

            for char in kind:
                if char in ("x", "y", "z"):
                    primary_color = char
                    break

            is_hadamard = kind.endswith("h")

            if is_hadamard:
                lengths = [
                    (pipe_length * 0.45, primary_color),
                    (pipe_length * 0.10, "h"),
                    (pipe_length * 0.45, primary_color),
                ]
            else:
                lengths = [
                    (pipe_length, primary_color),
                ]

            current = source_position[axis] + sign * 1.0

            for section_index, (length, material_name) in enumerate(
                lengths
            ):
                centre = source_position.copy()

                start = current
                end = current + sign * length

                centre[axis] = (start + end) / 2

                dimensions = [1.0, 1.0, 1.0]
                dimensions[axis] = length

                for face_axis in range(3):
                    for face_sign in (-1, 1):
                        half_extent = np.array(
                            [
                                dimensions[0] / 2,
                                dimensions[1] / 2,
                                dimensions[2] / 2,
                            ],
                            dtype=np.float32,
                        )

                        face_position = centre.copy()

                        face_position[face_axis] += (
                            face_sign
                            * half_extent[face_axis]
                        )

                        other_axes = [0, 1, 2]
                        other_axes.remove(face_axis)

                        node = add_face(
                            f"pipe-{source.id}-{target.id}-"
                            f"{section_index}-{face_axis}-{face_sign}",
                            face_position,
                            face_axis,
                            face_sign,
                            2 * half_extent[other_axes[0]],
                            2 * half_extent[other_axes[1]],
                            material_name,
                        )

                        root.children.append(node)

                current = end

        mesh.assetInfo.unitname = "meter"
        mesh.assetInfo.unitmeter = 1.0
        mesh.assetInfo.upaxis = "Z_UP"

        scene = collada.scene.Scene(
            "Scene",
            [root],
        )

        mesh.scenes.append(scene)
        mesh.scene = scene

        mesh.write(filepath)