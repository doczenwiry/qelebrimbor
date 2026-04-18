from collections import defaultdict
from enum import Enum
from typing import Iterable

import pyzx as zx
import networkx as nx
from ast import literal_eval as make_tuple

from qelebrimbor.common.coordinates import Coordinates

from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.helpers.blockgraph import BlockGraphHelper

from qelebrimbor.common.components import ZxNode, ZxEdge, BgCube, BgPipe
from qelebrimbor.common.attributes_zx import NodeId, NodeType, EdgeId, EdgeType, QubitId, LayerId
from qelebrimbor.common.attributes_bg import CubeId, CubeKind, PipeId
from qelebrimbor.common.paths import PathSpecification

import logging

from qelebrimbor.utilities.nmtfl_constraint import NoMoreThanFourLegsConstraint

console = logging.getLogger(__name__)
console.setLevel(logging.INFO)

class LayerTransitionType(Enum):
    EVERY = 0
    LOWER = 1
    INTRA = 2
    UPPER = 3
    OUTER = 4

# TODO: figure out what the other VertexType and EdgeType represent
# TODO: how do we deal with the last four VertexType (i.e. H_BOX, W_INPUT, W_OUTPUT, Z_BOX) ?
# TODO: do we need the last EdgeType (i.e. W_IO) ?
# TODO: how do we deal with the phase of a spider ?
# TODO: benchmarking and timing various parts
# TODO: construction of animation
class VolumetricZxGraph(nx.Graph):
    KEY_ZX_NODE = 'zx_node'
    KEY_ZX_EDGE = 'zx_edge'

    KEY_BG_CUBE = 'bg_cube'
    KEY_BG_PIPE = 'bg_pipe'

    # TODO: work around the assumption that the zx-nodes are numbered from 0..n-1
    def __init__(self,
        nodes: Iterable[tuple[NodeId, NodeType]] | None = None,
        edges: Iterable[tuple[EdgeId, EdgeType]] | None = None
    ):
        # Separate ZX-graph and BG-graph
        super(VolumetricZxGraph, self).__init__()
        self.__bg_graph: nx.Graph = nx.Graph()

        # Keeps track of which nodes appear on which qubit-line or layer of the ZX-graph
        self.__zx_qubits: dict[QubitId, list[NodeId]] = defaultdict(list)
        self.__zx_layers: dict[LayerId, list[NodeId]] = defaultdict(list)

        # Keeps track of the coordinates in 3D that are occupied by some cube
        self.occupied: set[Coordinates] = set()

        if nodes is not None:
            for node_id, node_type in nodes:
                self.add_node(node_id)
                zx_node = ZxNode(id = node_id, type = node_type)
                self.nodes[node_id][VolumetricZxGraph.KEY_ZX_NODE] = zx_node

        if edges is not None:
            for edge, edge_type in edges:
                source = min(edge)
                target = max(edge)
                self.add_edge(source, target)
                zx_edge = ZxEdge(source = source, target = target, type = edge_type)
                self.edges[source, target][VolumetricZxGraph.KEY_ZX_EDGE] = zx_edge

        # TODO: split any spider with more than 4 edges (cfr. graph_manager.py; prep_3d_g)
        # TODO: does the choice of how to split such spiders affect the minimal achievable volume ?
        NoMoreThanFourLegsConstraint.enforce(self)

        self.__next_cube_id = self.number_of_nodes()

    @staticmethod
    def from_pyzx_graph(zx_graph: zx.graph.base.BaseGraph):
        converted_node_ids: dict[NodeId, NodeId] = dict()
        nodes: list[tuple[NodeId, NodeType]] = []
        for original_id in zx_graph.vertices():
            node_id = len(converted_node_ids)
            converted_node_ids[original_id] = node_id
            nodes.append( (node_id, NodeType.convert(zx_graph.type(original_id))) )

        edges: list[tuple[EdgeId, EdgeType]] = []
        for edge in zx_graph.edges():
            source = converted_node_ids[min(edge)]
            target = converted_node_ids[max(edge)]
            edges.append( ( (source,target) , EdgeType.convert(zx_graph.edge_type(edge))) )

        vzx = VolumetricZxGraph(nodes, edges)

        # Add qubit and layer information
        for original_id, node_id in converted_node_ids.items():
            node_qubit = int(zx_graph.qubit(original_id))
            node_layer = int(zx_graph.row(original_id))

            zx_node: ZxNode = vzx.nodes[node_id][VolumetricZxGraph.KEY_ZX_NODE]
            zx_node.qubit = node_qubit
            zx_node.layer = node_layer

            vzx.__zx_qubits[node_qubit].append(node_id)
            vzx.__zx_layers[node_layer].append(node_id)

        return vzx

    @staticmethod
    def from_file(filepath: str):
        with open(filepath, 'r') as file:
            # Instantiate the VolumetricZxGraph
            vzx = VolumetricZxGraph()

            # Read the blockgraph header
            header = file.readline()
            if header != "VOLUMETRIC-ZX-GRAPH 0.0.1\n":
                raise Exception(f"Invalid file format. Header <VOLUMETRIC-ZX-GRAPH 0.0.1> not found [got={header}].")

            # Read the empty line between the blockgraph header and the cubes header
            file.readline()

            # Read the nodes header
            header = file.readline()
            if header != "NODES: id;type;qubit;layer;realising_cube\n":
                raise Exception(f"Invalid file format. Header for NODES not found [got={header}].")

            # Read all the lines describing nodes
            current_line = file.readline()
            while current_line and current_line != "\n":
                if current_line != "":
                    node_id, node_type, qubit, layer, realising_cube = current_line.split(';')
                    node = int(node_id)
                    vzx.add_node(node)
                    vzx.nodes[node][VolumetricZxGraph.KEY_ZX_NODE] = ZxNode(
                        id = node, type = NodeType[node_type],
                        qubit = int(qubit), layer = int(layer),
                        realising_cube = int(realising_cube)
                    )
                current_line = file.readline()

            # Read the edges header
            header = file.readline()
            if header != "EDGES: source;target;type;realisation\n":
                raise Exception(f"Invalid file format. Header for EDGES not found [got={header}].")

            # Read all the lines describing edges
            current_line = file.readline()
            while current_line and current_line != "\n":
                if current_line != "":
                    source_id, target_id, edge_type, realisation = current_line.split(';')
                    source = int(source_id)
                    target = int(target_id)
                    vzx.add_edge(source, target)
                    vzx.edges[source, target][VolumetricZxGraph.KEY_ZX_EDGE] = ZxEdge(
                        source = source, target = target,
                        type = EdgeType[edge_type],
                        realisation =  [ make_tuple(pair) for pair in realisation[1:-2].split(':') ]
                    )
                current_line = file.readline()

            # Read the cubes header
            header = file.readline()
            if header != "CUBES: id;x;y;z;kind;realised_node\n":
                raise Exception(f"Invalid file format. Header for CUBES not found [got={header}].")

            # Read all the lines describing cubes
            current_line = file.readline()
            while current_line and current_line != "\n":
                if current_line != "":
                    cube_id, x, y, z, kind, realised_node = current_line.split(';')
                    cube = int(cube_id)
                    vzx.__bg_graph.add_node(cube)
                    vzx.__bg_graph.nodes[cube][VolumetricZxGraph.KEY_BG_CUBE] = BgCube(
                        id = cube, kind = CubeKind[kind], position = Coordinates(int(x), int(y), int(z)),
                        realised_node = int(realised_node)
                    )
                current_line = file.readline()

            # Read the pipes header
            header = file.readline()
            if header != "PIPES: source;target;type\n":
                raise Exception(f"Invalid file format. Header for PIPES not found [got={header}].")

            # Read all the lines describing pipes
            current_line = file.readline()
            while current_line and current_line != "\n":
                if current_line != "":
                    source_id, target_id, pipe_type = current_line.split(';')
                    source = int(source_id)
                    target = int(target_id)
                    vzx.__bg_graph.add_edge(source, target)
                    vzx.__bg_graph.edges[source, target][VolumetricZxGraph.KEY_BG_PIPE] = BgPipe(
                        source = source, target = target, type = EdgeType[pipe_type[:-1]]
                    )
                current_line = file.readline()

            return vzx

    def into_file(self, filepath: str):
        with (open(filepath, 'w') as file):
            file.write(f"VOLUMETRIC-ZX-GRAPH 0.0.1\n")

            # Store node information
            file.write("\nNODES: id;type;qubit;layer;realising_cube\n")
            file.writelines(
                [
                    f"{node.id};{node.type.name};{node.qubit};{node.layer};{node.realising_cube}\n"
                    for node in self.get_zx_nodes()
                ]
            )

            # Store edge information
            file.write("\nEDGES: source;target;type;realisation\n")
            file.writelines(
                [
                    f"{edge.source};{edge.target};{edge.type};[{':'.join(map(str, edge.realisation))}]\n"
                    for edge in self.get_zx_edges()
                ]
            )

            # Store cube information
            file.write("\nCUBES: id;x;y;z;kind;realised_node\n")
            file.writelines(
                [
                    f"{cube.id};{';'.join(map(str, iter(cube.position)))};{cube.kind.name};{cube.realised_node}\n"
                    for cube in self.get_bg_cubes()
                ]
            )

            # Store pipe information
            file.write("\nPIPES: source;target;type\n")
            file.writelines(
                [
                    f"{pipe.source};{pipe.target};{pipe.type.name}\n"
                    for pipe in self.get_bg_pipes()
                ]
            )

    def get_zx_nodes(self, node_type: NodeType | None = None, qubit: QubitId | None = None, layer: LayerId | None = None):
        return map( lambda nd: self.get_zx_node(nd), self.get_nodes(node_type, qubit, layer) )

    def get_nodes(self, node_type: NodeType | None = None, qubit: QubitId | None = None, layer: LayerId | None = None):
        return filter(
            lambda node : (node_type is None or self.get_zx_node(node).type == node_type) and
                          (qubit is None or self.get_zx_node(node).qubit == qubit) and
                          (layer is None or self.get_zx_node(node).layer == layer),
            self.nodes
        )

    def get_qubits(self):
        return self.__zx_qubits.keys()

    def get_layers(self):
        return self.__zx_layers.keys()

    def get_layer_density(self, layer: int) -> tuple[int,int]:
        number_of_nodes = 0
        number_of_edges = 0
        for node in self.get_nodes(layer = layer):
            number_of_edges += sum(1 for _ in self.get_node_neighbours(node, transition = LayerTransitionType.INTRA))
            number_of_nodes += 1
        number_of_edges = number_of_edges // 2
        return number_of_nodes, number_of_edges

    def get_zx_edges(self, edge_type: EdgeType | None = None):
        return map(lambda edge: self.get_zx_edge(*edge), self.get_edges(edge_type = edge_type))

    def get_edges(self, edge_type: EdgeType | None = None):
        return filter(
            lambda eg: edge_type is None or self.get_zx_edge(*eg).type == edge_type,
            self.edges
        )

    def get_layered_edges(self, layer: int, transition: LayerTransitionType = LayerTransitionType.EVERY):
        if transition == LayerTransitionType.LOWER:
            filtering = lambda edge : self.get_zx_node(edge[0]).layer <  layer == self.get_zx_node(edge[1]).layer
        elif transition == LayerTransitionType.INTRA:
            filtering = lambda edge : self.get_zx_node(edge[0]).layer == layer == self.get_zx_node(edge[1]).layer
        elif transition == LayerTransitionType.UPPER:
            filtering = lambda edge : self.get_zx_node(edge[0]).layer == layer <  self.get_zx_node(edge[1]).layer
        elif transition == LayerTransitionType.OUTER:
            filtering = lambda edge : self.get_zx_node(edge[0]).layer <  layer <  self.get_zx_node(edge[1]).layer
        else:
            filtering = lambda edge : True

        return filter(filtering, self.edges())

    def number_of_cubes(self) -> int:
        return self.__bg_graph.number_of_nodes()

    def number_of_pipes(self) -> int:
        return self.__bg_graph.number_of_edges()

    def get_bg_cubes(self, kind: CubeKind | None = None):
        return map(lambda cb: self.get_bg_cube(cb), self.get_cubes(kind= kind))

    def get_cubes(self, kind: CubeKind | None = None):
        return filter(
            lambda cb: (kind is None or self.get_bg_cube(cb).kind == kind), self.__bg_graph.nodes()
        )

    def get_bg_pipes(self, pipe_type: EdgeType | None = None):
        return map(lambda pp: self.get_bg_pipe(*pp), self.get_pipes(pipe_type = pipe_type))

    def get_pipes(self, pipe_type: EdgeType | None = None):
        return filter(
            lambda pp: (pipe_type is None or self.get_bg_pipe(*pp).type == pipe_type),
            self.__bg_graph.edges()
        )

    def get_node_neighbours(self, node: NodeId, transition: LayerTransitionType = LayerTransitionType.EVERY):
        if transition == LayerTransitionType.EVERY:
            filtering = lambda other : True
        elif transition == LayerTransitionType.LOWER:
            filtering = lambda other : self.get_zx_node(other).layer < self.get_zx_node(node).layer
        elif transition == LayerTransitionType.INTRA:
            filtering = lambda other : self.get_zx_node(other).layer == self.get_zx_node(node).layer
        elif transition == LayerTransitionType.UPPER:
            filtering = lambda other : self.get_zx_node(node).layer < self.get_zx_node(other).layer
        else: #transition == LayerTransitionType.OUTER
            raise Exception(f"Requesting OUTER transition type for node neighbours. Will always be empty.")

        return filter(filtering, self.neighbors(node))

    def get_cube_neighbours(self, cube: CubeId):
        return self.__bg_graph.neighbors(cube)

    def get_zx_degree(self, node: NodeId) -> float:
        return self.degree[node]

    def get_zx_node(self, node: NodeId) -> ZxNode:
        return self.nodes[node][VolumetricZxGraph.KEY_ZX_NODE]

    def get_zx_edge(self, source: NodeId, target: NodeId) -> ZxEdge:
        return self.edges[source, target][VolumetricZxGraph.KEY_ZX_EDGE]

    def get_bg_cube(self, cube: CubeId) -> BgCube:
        return self.__bg_graph.nodes[cube][VolumetricZxGraph.KEY_BG_CUBE]

    def get_bg_pipe(self, source: CubeId, target: CubeId) -> BgPipe:
        return self.__bg_graph.edges[source, target][VolumetricZxGraph.KEY_BG_PIPE]

    def is_zx_node_realised(self, node: NodeId) -> bool:
        return self.get_zx_node(node).realising_cube != -1

    def realise_zx_node(self, node: NodeId, kind: CubeKind, position: Coordinates) -> CubeId:
        """Realise the node as a cube of the given kind placed at the given coordinates."""
        if kind not in CubeKind.suitable_kinds(self.get_zx_node(node).type):
            raise Exception(f"Requested {kind} is not compatible with {self.get_zx_node(node).type}")

        if not self.has_node(node):
            raise Exception(f"Node #{node} not found in the ZX-graph.")

        cube = self.place_cube(kind, position)
        self.__bg_graph.nodes[cube][VolumetricZxGraph.KEY_BG_CUBE].realised_node = node
        self.nodes[node][VolumetricZxGraph.KEY_ZX_NODE].realising_cube = cube

        console.info(f"Realising node #{node} [{self.get_zx_node(node).type}] as cube #{cube} [{kind}@{position}]")

        return cube

    def is_zx_edge_realised(self, source: NodeId, target: NodeId) -> bool:
        return len(self.get_zx_edge(source, target).realisation) > 0

    def realise_zx_edge(self, source: NodeId, target: NodeId, proposal: PathSpecification):
        if not self.is_zx_node_realised(source):
            raise Exception(f"{source} is not realised; cannot connect with a path.")

        if not self.is_zx_node_realised(target):
            raise Exception(f"{target} is not realised; cannot connect with a path.")

        if not self.has_edge(source, target):
            raise Exception(f"No edge {source}-{target} found in the ZX-graph.")

        if self.is_zx_edge_realised(source, target):
            raise Exception(f"{source}-{target} is already realized by a path.")

        source_cube = proposal.source_cube
        target_cube = proposal.target_cube

        # Reject path if it is invalid.
        if not self.is_path_valid(source, target, proposal):
            raise Exception(f"Proposed path to realise edge {source}-{target} is invalid.")

        # Representation of the path that will go into edge_realisations
        pipe_ids = []

        # Add all the extra cubes and pipes of the path to the BlockGraph
        previous_cube: int = source_cube

        for index in range(len(proposal.extras)):
            current_kind, current_position = proposal.extras[index]
            current_pipe_type = proposal.pipes[index]

            # Place the current cube and connect it to the previous cube.
            current_cube = self.place_cube(current_kind, current_position)
            # self.__bg_graph.nodes[current_cube][VolumetricZxGraph.KEY_BG_CUBE].realised_node = -1
            self.connect_pipe(previous_cube, current_cube, current_pipe_type)

            # Extend the sequence of extra node ids
            pipe = tuple(sorted((previous_cube, current_cube)))
            pipe_ids.append( pipe )

            # Prepare for the next iteration
            previous_cube = current_cube

        # Make the final connection
        if target_cube != self.get_zx_node(target).realising_cube:
            raise Exception(f"Target cube is not realising target node.")

        final_pipe_type = proposal.pipes[-1]
        self.connect_pipe(previous_cube, target_cube, final_pipe_type)

        pipe = tuple(sorted((previous_cube, target_cube)))
        pipe_ids.append( pipe )

        # Associate the path as a realisation of the edge
        self.edges[source, target][VolumetricZxGraph.KEY_ZX_EDGE].realisation = pipe_ids

        console.info(f"Realising edge {source}-{target} [type={self.get_zx_edge(source,target).type}] with pipes : {pipe_ids}")

    def place_cube(self, kind: CubeKind, position: Coordinates) -> CubeId:
        if position in self.occupied:
            raise Exception(f"Proposed position for {kind}@{position} is already occupied by another cube.")

        cube_id = self.__next_cube_id
        self.__next_cube_id += 1

        self.__bg_graph.add_node(cube_id)
        self.__bg_graph.nodes[cube_id][VolumetricZxGraph.KEY_BG_CUBE] = BgCube(id = cube_id, kind = kind, position = position)

        self.occupied.add(position)

        return cube_id

    def connect_pipe(self, source_cube: CubeId, target_cube: CubeId, pipe_type : EdgeType):
        if not self.__bg_graph.has_node(source_cube):
            raise Exception(f"Cube #{source_cube} not found in the BG-graph.")

        if not self.__bg_graph.has_node(target_cube):
            raise Exception(f"Cube #{target_cube} not found in the BG-graph.")

        if self.__bg_graph.has_edge(source_cube, target_cube):
            raise Exception(f"Cubes #{source_cube} and #{target_cube} are already connected by a pipe.")

        source_kind = self.get_bg_cube(source_cube).kind
        target_kind = self.get_bg_cube(target_cube).kind
        if not pipe_type in BlockGraphHelper.infer_pipe_type(source_kind, target_kind):
            raise Exception(f"Pipe type {pipe_type} is incompatible with source and target kinds [{source_kind}-{target_kind}].")

        # TODO: validate with respect to inferred pipe type between source and target cubes

        source_position = self.get_bg_cube(source_cube).position
        target_position = self.get_bg_cube(target_cube).position
        if source_position.get_manhattan_distance(target_position) != 1:
            raise Exception(f"Cubes #{source_cube}@{source_position} and #{target_cube}@{target_position} are not at adjacent positions.")

        self.__bg_graph.add_edge(source_cube, target_cube)
        bg_pipe = BgPipe(source = source_cube, target = target_cube, type = pipe_type)
        self.__bg_graph.edges[source_cube, target_cube][VolumetricZxGraph.KEY_BG_PIPE] = bg_pipe

    def is_path_valid(self, source: NodeId, target: NodeId, proposal: PathSpecification) -> bool:
        is_hadamard_path = False

        source_cube = proposal.source_cube

        if source_cube != self.get_zx_node(source).realising_cube:
            raise Exception(f"Cube #{source_cube} is not realising source {source}.")

        source_kind: CubeKind = self.get_bg_cube(source_cube).kind
        source_position: Coordinates = self.get_bg_cube(source_cube).position

        console.debug(f"Checking path validity:")
        console.debug(f"> Source cube #{source_cube} [{source_kind}@{source_position}]")
        console.debug(f"> Extra cubes: {proposal.extras}")

        previous_kind = source_kind
        previous_position = source_position
        previous_reach: Coordinates = source_kind.get_reach()

        extra_positions = set()

        for index in range(len(proposal.extras)):
            current_kind, current_position = proposal.extras[index]
            current_reach = current_kind.get_reach()

            # Check that the cube type is either X or Z (Y and boundaries must be leaves)
            if current_kind in [ CubeKind.OOO, CubeKind.YYY ]:
                console.debug(f"> CubeKind.OOO and CubeKind.YYY can only appear at the ends of a path : {current_kind}.")
                return False

            # Check that the current_position is not already occupied
            if current_position in self.occupied:
                console.debug(f"> Current position is already occupied : {current_kind}@{current_position}")
                return False

            # Check that the current_position is not already occupied by an extra cube
            if current_position in extra_positions:
                console.debug(f"> Current position is already in path : {current_kind}@{current_position}")
                return False
            extra_positions.add(current_position)

            # Check that the step taken lies in both reaches of successive cubes
            step_taken = current_position - previous_position
            if Spacetime.ORIGIN.get_manhattan_distance(step_taken) != 1:
                console.debug(f"> Consecutive cubes are not adjacent [{previous_position}-{current_position}]")
                return False

            if not Spacetime.contains(previous_reach, step_taken) or not Spacetime.contains(current_reach, step_taken):
                console.debug(f"> Previous reach does not contain step [{step_taken}]: {previous_kind}")
                console.debug(f"> Current reach does not contain step [{step_taken}]: {current_kind}")
                return False

            # Check that the current pipe has a type consistent with what is allowed
            current_pipe_type = proposal.pipes[index]
            inferred = BlockGraphHelper.infer_pipe_type(previous_kind, current_kind)
            if not current_pipe_type in inferred:
                console.debug(f"> Current pipe type is not allowed between {previous_kind} and {current_kind} [{current_pipe_type} not in {inferred}].")
                return False

            if current_pipe_type == EdgeType.HADAMARD:
                is_hadamard_path = not is_hadamard_path

            previous_position = current_position
            previous_kind = current_kind
            previous_reach = current_reach

        if self.is_zx_node_realised(target):
            target_cube = proposal.target_cube
            target_kind = self.get_bg_cube(target_cube).kind
            target_position = self.get_bg_cube(target_cube).position

            if target_cube != self.get_zx_node(target).realising_cube:
                raise Exception(f"Cube #{target_cube} is not realising source {target}.")

            # Check that the final step taken lies in the reach of the target cube
            step_taken = target_position - previous_position

            if Spacetime.ORIGIN.get_manhattan_distance(step_taken) != 1:
                console.debug(f"> Consecutive cubes are not adjacent [{previous_position}-{target_position}]")
                return False

            target_reach = target_kind.get_reach()
            if not Spacetime.contains(previous_reach, step_taken) or not Spacetime.contains(target_reach, step_taken):
                console.debug(f"> Reach of target cube does not contain final step : {target_reach} w/ {step_taken} {Spacetime.contains(target_reach, step_taken)}")
                return False

            # Check that the current pipe has a type consistent with what is allowed
            current_pipe_type = proposal.pipes[-1]
            inferred = BlockGraphHelper.infer_pipe_type(previous_kind, target_kind)
            if current_pipe_type not in inferred:
                console.debug(f"> Final pipe type is not allowed between {previous_kind} and {target_kind} [{current_pipe_type} not in {inferred}].")
                return False

            if current_pipe_type == EdgeType.HADAMARD:
                is_hadamard_path = not is_hadamard_path

        edge_type = self.get_zx_edge(source, target).type

        if is_hadamard_path != (edge_type == EdgeType.HADAMARD):
            console.debug(f"> Proposed path is Hadamard-inconsistent with its purported edge [{edge_type}].")
            return False
        else:
            return True

    def log_summary(self, nodes: bool = False, edges: bool = False, layers: bool = False, qubits: bool = False, cubes: bool = False, pipes: bool = False):
        if nodes:
            for node_type in [NodeType.O, NodeType.X, NodeType.Y, NodeType.Z]:
                content = ""
                count = 0
                for node in self.get_nodes(node_type=node_type):
                    node_type = self.get_zx_node(node).type
                    content += f"{node} "
                    count += 1
                console.info(f"Nodes {node_type.name} [{count}]: {content}")

        if edges:
            content = ""
            count = 0
            for edge in self.edges:
                content += f"{edge} "
                count += 1
            console.info(f"Edges  [{count}]: {content}")

        if layers:
            for layer in self.get_layers():
                console.info(f"Layer {layer}  : {list(self.get_nodes(layer = layer))}")

        if qubits:
            for qubit in self.get_qubits():
                console.info(f"Qubit {qubit}  : {list(self.get_nodes(qubit = qubit))}")

        if cubes:
            for cube in self.get_cubes():
                realised_node = self.get_bg_cube(cube).realised_node
                console.info(f"Cube {cube}  : {self.get_bg_cube(cube).kind}@{self.get_bg_cube(cube).position} {realised_node}")

        if pipes:
            for pipe in self.get_pipes():
                console.info(f"Pipe {pipe}  : {self.get_bg_pipe(*pipe).type}")

    def print_summary(self):
        for node_type in [NodeType.O, NodeType.X, NodeType.Y, NodeType.Z]:
            content = ""
            for node in self.get_nodes(node_type=node_type):
                node_type = self.get_zx_node(node).type
                content += f"{node} "
            print(f"Nodes {node_type.name}: {content}")

        content = ""
        for edge in self.edges:
            content += f"{edge} "
        print(f"Edges  : {content}")

        for layer in self.get_layers():
            print(f"Layer {layer}  : {list(self.get_nodes(layer = layer))}")

        for qubit in self.get_qubits():
            print(f"Qubit {qubit}  : {list(self.get_nodes(qubit = qubit))}")

        for layer in self.get_layers():
            print(f"Layer {layer}  : {list(self.get_nodes(layer = layer))}")

        for qubit in self.get_qubits():
            print(f"Qubit {qubit}  : {list(self.get_nodes(qubit = qubit))}")

        for cube in self.get_cubes():
            realised_node = self.get_bg_cube(cube).realised_node
            print(f"Cube {cube}  : {self.get_bg_cube(cube).kind}@{self.get_bg_cube(cube).position} {realised_node}")

        for pipe in self.get_pipes():
            print(f"Pipe {pipe}  : {self.get_bg_pipe(*pipe).type}")

    def __identify_cube_at_position(self, position: Coordinates) -> int:
        for cube in self.get_cubes():
            if self.get_bg_cube(cube).position == position:
                return cube

        return -1