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

from ast import literal_eval as make_tuple

from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.zx.attributes import NodeId, NodeType, QubitId, LayerId, EdgeId, EdgeType
from qelebrimbor.core.bg.attributes import CubeId, PipeId, CubeKind
from qelebrimbor.core.components import BgCube, BgPipe
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph


class VZX:
    __HEADERS = {
        'vzx' : {
            'MAIN'  : "VOLUMETRIC-ZX-GRAPH 0.0.1",
            'NODES' : "NODES: index;type;qubit;layer;realising_cube",
            'EDGES' : "EDGES: source;target;type;realisation",
            'CUBES' : "CUBES: index;x;y;z;kind",
            'PIPES' : "PIPES: source;target;type"
        },
        # TODO: remove this eventually
        'ang' : {
            'MAIN'  : "BLOCKGRAPH 0.1.0;",
            'NODES' : "NODES: index;type;qubit;layer;realising_cube",
            'EDGES' : "EDGES: source;target;type;realisation",
            'CUBES' : "CUBES: index;x;y;z;kind;label;",
            'PIPES' : "PIPES: src;tgt;kind;"
        }
    }

    @staticmethod
    def into_file(graph: VolumetricZxGraph, filepath: str):
        with (open(filepath, 'w') as file):
            file.write(f"{VZX.__HEADERS['vzx']['MAIN']}\n")

            # Store node information
            file.write(f"\n{VZX.__HEADERS['vzx']['NODES']}\n")
            file.writelines(
                [
                    f"{node.id};{node.type.name};{node.qubit};{node.layer};{node.realising_cube.id if node.realising_cube else -1}\n"
                    for node in graph.get_zx_nodes()
                ]
            )

            # Store edge information
            file.write(f"\n{VZX.__HEADERS['vzx']['EDGES']}\n")
            file.writelines(
                [
                    f"{edge.source.id};{edge.target.id};{edge.type};[{':'.join(map(lambda pp: f"({pp[0].id},{pp[1].id})", edge.realisation))}]\n"
                    for edge in graph.get_zx_edges()
                ]
            )

            # Store cube information
            file.write(f"\n{VZX.__HEADERS['vzx']['CUBES']}\n")
            file.writelines(
                [
                    f"{cube.id};{';'.join(map(str, iter(cube.position)))};{cube.kind.name}\n"
                    for cube in graph.get_bg_cubes()
                ]
            )

            # Store pipe information
            file.write(f"\n{VZX.__HEADERS['vzx']['PIPES']}\n")
            file.writelines(
                [
                    f"{pipe.source.id};{pipe.target.id};{pipe.type.name}\n"
                    for pipe in graph.get_bg_pipes()
                ]
            )

    @staticmethod
    def from_file(filepath: str, ang_format: bool = False):
        with open(filepath, 'r') as file:
            nodes: list[tuple[NodeId, NodeType]] = []
            edges: list[tuple[NodeId, NodeId, EdgeType]] = []
            qubits: dict[NodeId, QubitId] = dict()
            layers: dict[NodeId, LayerId] = dict()

            realised_nodes: dict[CubeId, NodeId] = dict()
            realisations: dict[EdgeId, list[PipeId]] = dict()

            headers = VZX.__HEADERS['vzx'] if not ang_format else VZX.__HEADERS['ang']

            # Read the blockgraph header
            header = file.readline().rstrip()
            if header != headers['MAIN']:
                raise Exception(f"Invalid file format. Header <{headers['MAIN']}> not found [got={header}].")

            # Read the empty line between the blockgraph header and the cubes header
            file.readline()

            # Read the nodes header
            header = file.readline().rstrip()
            if header != headers['NODES']:
                raise Exception(f"Invalid file format. Header for <{headers['NODES']}> not found [got={header}].")

            # Read all the lines describing nodes
            current_line = file.readline().rstrip()
            while current_line and current_line != "\n":
                if current_line != "":
                    node_id, node_type, qubit_id, layer_id, realising_cube_id = current_line.split(';')
                    node = int(node_id)
                    qubit = int(qubit_id)
                    layer = int(layer_id)
                    realising_cube = int(realising_cube_id)
                    nodes.append( (node, NodeType[node_type]) )
                    if qubit != -1:
                        qubits[node] = qubit
                    if layer != -1:
                        layers[node] = layer
                    realised_nodes[realising_cube] = node
                current_line = file.readline().rstrip()

            # Read the edges header
            header = file.readline().rstrip()
            if header != headers['EDGES']:
                raise Exception(f"Invalid file format. Header for <{headers['EDGES']}> not found [got={header}].")

            # Read all the lines describing edges
            current_line = file.readline().rstrip()
            while current_line and current_line != "\n":
                if current_line != "":
                    source_id, target_id, edge_type, realisation = current_line.split(';')
                    source = int(source_id)
                    target = int(target_id)
                    edges.append( (source, target, EdgeType[edge_type]) )
                    realisations[source, target] = [make_tuple(pair) for pair in realisation[1:-1].split(':')]
                current_line = file.readline().rstrip()

            vzx = VolumetricZxGraph(nodes, edges, qubits, layers)

            # Read the cubes header
            header = file.readline().rstrip()
            if header != headers['CUBES']:
                raise Exception(f"Invalid file format. Header for <{headers['CUBES']}> not found [got={header}].")

            # Read all the lines describing cubes
            current_line = file.readline().rstrip()
            while current_line and current_line != "\n":
                if current_line != "":
                    if ang_format:
                        cube_id, x, y, z, kind, label, _ = current_line.split(';')
                        position = Coordinates(int(x) // 3, int(y) // 3, int(z) // 3)
                    else:
                        cube_id, x, y, z, kind = current_line.split(';')
                        position = Coordinates(int(x), int(y), int(z))

                    cube = int(cube_id)
                    vzx.blockgraph.add_node(cube)

                    bg_cube = BgCube(id = cube, kind = CubeKind[kind.upper()], position = position)
                    vzx.blockgraph.nodes[cube][VolumetricZxGraph.KEY_BG_CUBE] = bg_cube
                current_line = file.readline().rstrip()

            # Read the pipes header
            header = file.readline().rstrip()
            if header != headers['PIPES']:
                raise Exception(f"Invalid file format. Header for <{headers['PIPES']}> not found [got={header}].")

            # Read all the lines describing pipes
            current_line = file.readline().rstrip()
            while current_line and current_line != "\n":
                if current_line != "":
                    if ang_format:
                        source_id, target_id, pipe_kind, _ = current_line.split(';')
                        pipe_type = EdgeType.HADAMARD if 'h' in pipe_kind else EdgeType.IDENTITY
                    else:
                        source_id, target_id, pipe_type = current_line.split(';')
                        pipe_type = EdgeType[pipe_type]

                    source = vzx.get_bg_cube(int(source_id))
                    target = vzx.get_bg_cube(int(target_id))
                    bg_pipe = BgPipe(source, target, pipe_type)
                    vzx.blockgraph.add_edge(source.id, target.id)
                    vzx.blockgraph.edges[source.id, target.id][VolumetricZxGraph.KEY_BG_PIPE] = bg_pipe
                current_line = file.readline().rstrip()

            # Encode correspondence between ZX and BG
            for cube, node in realised_nodes.items():
                zx_node = vzx.get_zx_node(node)
                bg_cube = vzx.get_bg_cube(cube)
                bg_cube.realised_node = zx_node
                zx_node.realising_cube = bg_cube

            for edge, pipe_ids in realisations.items():
                zx_edge = vzx.get_zx_edge(*edge)
                zx_edge.realisation = list(map(lambda pp: vzx.get_bg_pipe(*pp), pipe_ids))

            return vzx
