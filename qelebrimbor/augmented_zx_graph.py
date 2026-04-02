from collections import defaultdict
from enum import Enum
from typing import Iterable

import pyzx as zx
import networkx as nx

from qelebrimbor.common.coordinates import Coordinates

from qelebrimbor.helpers.spacetime import Spacetime
from qelebrimbor.helpers.blockgraph import BlockGraphHelper

from qelebrimbor.common.components_zx import NodeId, NodeType, EdgeId, EdgeType
from qelebrimbor.common.components_bg import CubeId, CubeKind, PipeId
from qelebrimbor.common.paths import PathSpecification

from logging import getLogger
console = getLogger(__name__)

QubitId = int
LayerId = int

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
class AugmentedZxGraph(nx.Graph):
    KEY_ZX_NODE_TYPE     = 'zx_node_type'
    KEY_ZX_NODE_QUBIT    = 'zx_node_qubit'
    KEY_ZX_NODE_LAYER    = 'zx_node_layer'
    KEY_ZX_NODE_BG_CUBES = 'zx_node_bg_cube'
    KEY_ZX_EDGE_TYPE     = 'zx_edge_type'
    KEY_ZX_EDGE_BG_PATH  = 'zx_edge_bg_path'

    KEY_BG_CUBE_ZX_NODES = 'bg_cube_zx_node'
    KEY_BG_CUBE_KIND     = 'bg_cube_kind'
    KEY_BG_CUBE_POSITION = 'bg_cube_position'
    KEY_BG_PIPE_TYPE     = 'bg_pipe_type'

    # TODO: work around the assumption that the zx-nodes are numbered from 0..n-1
    def __init__(self,
        nodes: Iterable[tuple[NodeId, NodeType]] | None = None,
        edges: Iterable[tuple[tuple[NodeId, NodeId], EdgeType]] | None = None
    ):
        # Separate ZX-graph and BG-graph
        super(AugmentedZxGraph, self).__init__()
        self.__bg_graph: nx.Graph = nx.Graph()

        # Keeps track of which nodes appear on which qubit-line or layer of the ZX-graph
        self.__zx_qubits: dict[QubitId, list[NodeId]] = defaultdict(list)
        self.__zx_layers: dict[LayerId, list[NodeId]] = defaultdict(list)

        # Keeps track of the coordinates in 3D that are occupied by some cube
        self.occupied: set[Coordinates] = set()

        converted_node_ids: dict[NodeId, NodeId] = dict()
        if nodes is not None:
            for node, node_type in nodes:
                node_id = len(converted_node_ids)
                converted_node_ids[node] = node_id
                self.add_node(node_id)
                nx_node = self.nodes[node_id]
                nx_node[AugmentedZxGraph.KEY_ZX_NODE_TYPE] = node_type
                nx_node[AugmentedZxGraph.KEY_ZX_NODE_BG_CUBES] = set()

        if edges is not None:
            for edge, edge_type in edges:
                source = converted_node_ids[min(edge)]
                target = converted_node_ids[max(edge)]
                self.add_edge(source, target)
                self.get_edge_data(source, target)[AugmentedZxGraph.KEY_ZX_EDGE_TYPE] = edge_type
                self.get_edge_data(source, target)[AugmentedZxGraph.KEY_ZX_EDGE_BG_PATH] = []

        self.__next_cube_id = self.number_of_nodes()

        # TODO: split any spider with more than 4 edges (cfr. graph_manager.py; prep_3d_g)
        # TODO: does the choice of how to split such spiders affect the minimal achievable volume ?
        if self.number_of_nodes() > 0:
            _, max_degree = max(self.degree, key=lambda entry: entry[1])
            if max_degree > 4:
                raise NotImplementedError("Enforcement of no-more-than-four-legs condition not implemented.")

    @staticmethod
    def from_pyzx_graph(zx_graph: zx.graph.base.BaseGraph):
        converted_node_ids: dict[NodeId, NodeId] = dict()
        nodes: list[tuple[NodeId, NodeType]] = []
        for node in zx_graph.vertices():
            node_id = len(converted_node_ids)
            converted_node_ids[node] = node_id
            nodes.append( (node_id, NodeType.convert(zx_graph.type(node))) )

        edges: list[tuple[EdgeId, EdgeType]] = []
        for edge in zx_graph.edges():
            source = converted_node_ids[min(edge)]
            target = converted_node_ids[max(edge)]
            edges.append( ( (source,target) , EdgeType.convert(zx_graph.edge_type(edge))) )

        ang = AugmentedZxGraph(nodes, edges)

        # Add qubit and layer information
        for node, node_id in converted_node_ids.items():
            node_qubit = int(zx_graph.qubit(node))
            ang.nodes[node_id][AugmentedZxGraph.KEY_ZX_NODE_QUBIT] = node_qubit
            ang.__zx_qubits[node_qubit].append(node_id)

            node_layer = int(zx_graph.row(node))
            ang.nodes[node_id][AugmentedZxGraph.KEY_ZX_NODE_LAYER] = node_layer
            ang.__zx_layers[node_layer].append(node_id)

        return ang

    @staticmethod
    def __make_tuple(tpl: str):
        source, target = tpl.split('-')
        return int(source), int(target)

    @staticmethod
    def from_file(filepath: str):
        nodes: list[tuple[NodeId, NodeType]] = []
        edges: list[tuple[tuple[NodeId, NodeId], EdgeType]] = []
        with open(filepath, 'r') as file:
            # Read the zx-nodes
            header = file.readline().split(' ')
            if header[0] != "ZX-NODES:\n":
                raise Exception("Invalid file format. Header for ZX-NODES not found.")
            for node_type in [ NodeType.O, NodeType.X, NodeType.Y, NodeType.Z ]:
                current = file.readline().split(' ')
                if current[0] != f">{node_type}:":
                    raise Exception(f"Invalid file format. Header for {node_type} not found.")
                if len(current) > 1 and current[1] != '\n':
                    nodes.extend(map(lambda nd: (int(nd), node_type), current[1:]))

            # Read the zx-edges
            header = file.readline().split(' ')
            if header[0] != "ZX-EDGES:\n":
                raise Exception("Invalid file format. Header for ZX-EDGES not found.")
            for edge_type in [ EdgeType.IDENTITY, EdgeType.HADAMARD ]:
                current = file.readline().split(" ")
                if current[0] != f">{edge_type.name}:":
                    raise Exception(f"Invalid file format. Header for {edge_type} not found. [got {current[0]}]")
                if len(current) > 1 and current[1] != '\n':
                    edges.extend(map(lambda ed: (AugmentedZxGraph.__make_tuple(ed), edge_type), current[1:]))

            ang = AugmentedZxGraph(nodes, edges)

            # Read the zx-qubits
            header = file.readline().split(" ")
            if header[0] != "ZX-QUBITS:":
                raise Exception("Invalid file format. Header for ZX-QUBITS not found.")
            qubits = int(header[1])
            for qubit in range(qubits):
                current = file.readline().split(" ")
                if current[0] != f">{qubit}:":
                    raise Exception(f"Invalid file format. Header for qubit {qubit} not found. [got {current[0]}]")
                ang.__zx_qubits[qubit] = list(map(lambda nd: int(nd), current[1:]))
                for node in ang.__zx_qubits[qubit]:
                    ang.nodes[node][AugmentedZxGraph.KEY_ZX_NODE_QUBIT] = qubit

            # Read the zx-layers
            header = file.readline().split(" ")
            if header[0] != "ZX-LAYERS:":
                raise Exception("Invalid file format. Header for ZX-LAYERS not found.")
            layers = int(header[1])
            for layer in range(layers):
                current = file.readline().split(" ")
                if current[0] != f">{layer}:":
                    raise Exception(f"Invalid file format. Header for layer {layer} not found. [got {current[0]}]")
                ang.__zx_layers[layer] = list(map(lambda nd: int(nd), current[1:]))
                for node in ang.__zx_layers[layer]:
                    ang.nodes[node][AugmentedZxGraph.KEY_ZX_NODE_LAYER] = layer

            # Read bg-cubes
            header = file.readline().split(' ')
            if header[0] != "BG-CUBES:\n":
                raise Exception(f"Invalid file format. Header for BG-CUBES not found.")
            for cube_kind in [ CubeKind.OOO, CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZZX, CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ, CubeKind.YYY ]:
                current = file.readline().split(" ")
                if current[0] != f">{cube_kind.name}:":
                    raise Exception(f"Invalid file format. Header for {cube_kind} not found.")

                if len(current) <= 1 or current[1] == '\n':
                    continue

                for cb_spec in current[1:]:
                    cb_id, cb_position = cb_spec.split("@")

                    cube = int(cb_id)
                    position = Coordinates.from_string(cb_position)
                    ang.__bg_graph.add_node(cube)
                    ang.__bg_graph.nodes[cube][AugmentedZxGraph.KEY_BG_CUBE_KIND] = cube_kind
                    ang.__bg_graph.nodes[cube][AugmentedZxGraph.KEY_BG_CUBE_POSITION] = position
                    ang.__bg_graph.nodes[cube][AugmentedZxGraph.KEY_BG_CUBE_ZX_NODES] = set()

            # Read bg-pipes
            header = file.readline().split(' ')
            if header[0] != "BG-PIPES:\n":
                raise Exception("Invalid file format. Header for BG-PIPES not found.")
            for pipe_kind in [ EdgeType.IDENTITY, EdgeType.HADAMARD ]:
                current = file.readline().split(" ")
                if current[0] != f">{pipe_kind.name}:":
                    raise Exception(f"Invalid file format. Header for {pipe_kind} not found.")
                if len(current) > 1 and current[1] != '\n':
                    for pipe in current[1:]:
                        source_cube, target_cube = AugmentedZxGraph.__make_tuple(pipe)
                        ang.connect_pipe(source_cube, target_cube, pipe_kind)

            # Read zx-nodes-bg-cubes
            header = file.readline().split(' ')
            if header[0] != "ZX-NODES-BG-CUBES:\n":
                raise Exception("Invalid file format. Header for ZX-NODES-BG-CUBES not found.")
            for token in file.readline().split(' ')[1:]:
                nd_id, cb_id = token.split(':')
                node = int(nd_id)
                cube = int(cb_id)
                ang.nodes[node][AugmentedZxGraph.KEY_ZX_NODE_BG_CUBES].add(cube)
                ang.__bg_graph.nodes[cube][AugmentedZxGraph.KEY_BG_CUBE_ZX_NODES].add(node)

            # Read zx-edges-bg-pipes
            header = file.readline().split(' ')
            if header[0] != "ZX-EDGES-BG-PIPES:\n":
                raise Exception("Invalid file format. Header for ZX-EDGES-BG-PIPES not found.")

            count = ang.number_of_edges()
            for _ in range(count):
                current = file.readline().split(' ')
                edge = AugmentedZxGraph.__make_tuple(current[0][1:-1])
                ang.edges[edge][AugmentedZxGraph.KEY_ZX_EDGE_BG_PATH] = list(map(AugmentedZxGraph.__make_tuple, current[1:]))

            return ang

    def into_file(self, filepath: str):
        with (open(filepath, 'w') as file):
            # Dump zx-nodes
            file.write(f"ZX-NODES:\n")
            for node_type in [ NodeType.O, NodeType.X, NodeType.Y, NodeType.Z ]:
                content = map(str, self.get_nodes(node_type = node_type))
                file.write(f">{node_type}: {" ".join(content)}\n")
            # Dump zx-edges
            file.write(f"ZX-EDGES:\n")
            for edge_type in [ EdgeType.IDENTITY, EdgeType.HADAMARD ]:
                content = map(lambda edge: str(edge[0]) + '-' + str(edge[1]), self.get_edges(edge_type = edge_type))
                file.write(f">{edge_type.name}: {" ".join(content)}\n")
            # Dump zx-qubits
            file.write(f"ZX-QUBITS: {len(self.get_qubits())}\n")
            for qubit in self.get_qubits():
                content = map(str, self.get_nodes(qubit = qubit))
                file.write(f">{qubit}: {" ".join(content)}\n")
            # Dump zx-layers
            file.write(f"ZX-LAYERS: {len(self.get_layers())}\n")
            for layer in self.get_layers():
                content = map(str, self.get_nodes(layer=layer))
                file.write(f">{layer}: {" ".join(content)}\n")
            # Dump bg-cubes
            file.write(f"BG-CUBES:\n")
            for cube_kind in [ CubeKind.OOO, CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZZX, CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ, CubeKind.YYY ]:
                content = map(lambda cb : str(cb) + '@' + str(self.get_cube_position(cb)).replace(" ", ""), self.get_cubes(cube_kind = cube_kind))
                file.write(f">{cube_kind.name}: {" ".join(content)}\n")
            # Dump bg-pipes
            file.write(f"BG-PIPES:\n")
            for pipe_kind in [ EdgeType.IDENTITY, EdgeType.HADAMARD ]:
                content = map(lambda edge: str(edge[0]) + '-' + str(edge[1]), self.get_pipes(pipe_kind = pipe_kind))
                file.write(f">{pipe_kind.name}: {" ".join(content)}\n")
            # Dump zx-nodes-bg-cubes
            zx_nodes_bg_cubes = []
            for node in self.get_nodes():
                for cube in self.get_realising_cubes(node):
                    zx_nodes_bg_cubes.append(str(node) + ':' + str(cube))
            # content = map(lambda nd: str(nd) + ':' + str(self.get_realising_cubes(nd)), self.get_nodes())
            file.write(f"ZX-NODES-BG-CUBES:\n> {" ".join(zx_nodes_bg_cubes)}\n")
            # Dump zx-edges-bg-pipes
            content = map(
                lambda ed: '>' + str(ed[0]) + '-' + str(ed[1]) + ": " + " ".join(map(lambda pp: str(pp[0]) + '-' + str(pp[1]), self.get_edge_realisation(*ed))),
                self.get_edges()
            )
            file.write(f"ZX-EDGES-BG-PIPES:\n{"\n".join(content)}")

    def get_qubits(self):
        return self.__zx_qubits.keys()

    def get_qubit(self, node) -> QubitId:
        return self.nodes[node][AugmentedZxGraph.KEY_ZX_NODE_QUBIT]

    def get_nodes(self, node_type: NodeType | None = None, qubit: QubitId | None = None, layer: LayerId | None = None):
        return filter(
            lambda node : (node_type is None or self.get_node_type(node) == node_type) and
                          (qubit is None or self.get_qubit(node) == qubit) and
                          (layer is None or self.get_node_layer(node) == layer),
            self.nodes()
        )

    def get_layers(self):
        return self.__zx_layers.keys()

    def get_layer(self, layer) -> list[NodeId]:
        return self.__zx_layers[layer]

    def get_layer_density(self, layer: int) -> tuple[int,int]:
        layer_nodes = self.get_layer(layer)
        number_of_nodes = len(layer_nodes)
        number_of_edges = 0
        for node in layer_nodes:
            number_of_edges += sum(1 for _ in self.get_node_neighbours(node, transition = LayerTransitionType.INTRA))
        number_of_edges = number_of_edges // 2
        return number_of_nodes, number_of_edges

    def get_edges(self, edge_type: EdgeType | None = None):
        return filter(
            lambda eg: edge_type is None or self.get_edge_type(*eg) == edge_type,
            self.edges()
        )

    def get_layered_edges(self, layer: int, transition: LayerTransitionType = LayerTransitionType.EVERY):
        if transition == LayerTransitionType.LOWER:
            filtering = lambda edge : self.get_node_layer(edge[0]) <  layer == self.get_node_layer(edge[1])
        elif transition == LayerTransitionType.INTRA:
            filtering = lambda edge : self.get_node_layer(edge[0]) == layer == self.get_node_layer(edge[1])
        elif transition == LayerTransitionType.UPPER:
            filtering = lambda edge : self.get_node_layer(edge[0]) == layer <  self.get_node_layer(edge[1])
        elif transition == LayerTransitionType.OUTER:
            filtering = lambda edge : self.get_node_layer(edge[0]) <  layer <  self.get_node_layer(edge[1])
        else:
            filtering = lambda edge : True

        return filter(filtering, self.edges())

    def get_cubes(self, cube_kind: CubeKind | None = None):
        return filter(
            lambda cb: (cube_kind is None or self.get_cube_kind(cb) == cube_kind), self.__bg_graph.nodes()
        )

    def number_of_cubes(self) -> int:
        return self.__bg_graph.number_of_nodes()

    def get_pipes(self, pipe_kind: EdgeType | None = None):
        return filter(
            lambda pp: (pipe_kind is None or self.get_pipe_kind(*pp) == pipe_kind),
            self.__bg_graph.edges()
        )

    def number_of_pipes(self) -> int:
        return self.__bg_graph.number_of_edges()

    def get_node_neighbours(self, node: NodeId, transition: LayerTransitionType = LayerTransitionType.EVERY):
        if transition == LayerTransitionType.EVERY:
            filtering = lambda other : True
        elif transition == LayerTransitionType.LOWER:
            filtering = lambda other : self.get_node_layer(other) < self.get_node_layer(node)
        elif transition == LayerTransitionType.INTRA:
            filtering = lambda other : self.get_node_layer(other) == self.get_node_layer(node)
        elif transition == LayerTransitionType.UPPER:
            filtering = lambda other : self.get_node_layer(node) < self.get_node_layer(other)
        else: #transition == LayerTransitionType.OUTER
            raise Exception(f"Requesting OUTER transition type for node neighbours. Will always be empty.")

        return filter(filtering, self.neighbors(node))

    def get_cube_neighbours(self, cube: CubeId):
        return self.__bg_graph.neighbors(cube)

    def get_degree(self, node: NodeId) -> float:
        return self.degree[node]

    def is_boundary(self, node: NodeId) -> bool:
        return self.get_node_type(node) == NodeType.O

    def is_spider(self, node: NodeId) -> bool:
        return self.get_node_type(node) != NodeType.O

    def is_cube_placed(self, cube: CubeId) -> bool:
        return cube in self.__bg_graph

    def get_realising_cubes(self, node: NodeId) -> Iterable[CubeId]:
        return iter(self.nodes[node][AugmentedZxGraph.KEY_ZX_NODE_BG_CUBES])

    def get_realised_nodes(self, cube: CubeId) -> Iterable[NodeId]:
        zx_nodes = self.__bg_graph.nodes[cube].get(AugmentedZxGraph.KEY_BG_CUBE_ZX_NODES) or set()
        return iter(zx_nodes)

    def get_node_type(self, node: NodeId) -> NodeType:
        return self.nodes[node][AugmentedZxGraph.KEY_ZX_NODE_TYPE]

    def get_node_layer(self, node: int) -> int:
        return self.nodes[node][AugmentedZxGraph.KEY_ZX_NODE_LAYER]

    def get_cube_position(self, cube: CubeId) -> Coordinates:
        return self.__bg_graph.nodes[cube][AugmentedZxGraph.KEY_BG_CUBE_POSITION]

    def get_cube_kind(self, cube: CubeId) -> CubeKind:
        return self.__bg_graph.nodes[cube][AugmentedZxGraph.KEY_BG_CUBE_KIND]

    def get_pipe_kind(self, source_cube: CubeId, target_cube: CubeId) -> EdgeType :
        if not self.__bg_graph.has_edge(source_cube, target_cube):
            raise Exception(f"Block-graph doesn't contain a pipe between {source_cube} and {target_cube}.")

        pipe_kind = self.__bg_graph.get_edge_data(source_cube, target_cube).get(AugmentedZxGraph.KEY_BG_PIPE_TYPE)

        if pipe_kind is None:
            raise Exception(f"Pipe {source_cube}-{target_cube} has no associated kind.")

        return pipe_kind

    def get_edge_type(self, source: NodeId, target: NodeId) -> EdgeType:
        if not self.has_edge(source, target):
            raise Exception(f"ZX-graph doesn't contain an edge between {source} and {target}.")

        edge_type = self.get_edge_data(source, target).get(AugmentedZxGraph.KEY_ZX_EDGE_TYPE)

        if edge_type is None:
            raise Exception(f"Edge {source}-{target} has no associated type.")

        return edge_type

    def get_edge_realisation(self, source: NodeId, target: NodeId) -> list[PipeId]:
        if not self.has_edge(source, target):
            raise Exception(f"ZX-graph doesn't contain an edge between {source}-{target}.")

        edge_realisation = self.get_edge_data(source, target).get(AugmentedZxGraph.KEY_ZX_EDGE_BG_PATH)

        if edge_realisation is None:
            raise Exception(f"Edge {source}-{target} has no associated realisation.")

        return edge_realisation

    def is_node_realised(self, node: NodeId) -> bool:
        return len(self.nodes[node][AugmentedZxGraph.KEY_ZX_NODE_BG_CUBES]) > 0

    def realise_node(self, node: NodeId, kind: CubeKind, position: Coordinates) -> CubeId:
        """Realise the node as a cube of the given kind placed at the given coordinates."""
        if kind not in CubeKind.suitable_kinds(self.get_node_type(node)):
            raise Exception(f"Requested {kind} is not compatible with {self.get_node_type(node)}")

        if not self.has_node(node):
            raise Exception(f"Node #{node} not found in the ZX-graph.")

        cube = self.place_cube(kind, position)
        self.__bg_graph.nodes[cube][AugmentedZxGraph.KEY_BG_CUBE_ZX_NODES].add(node)
        self.nodes[node][AugmentedZxGraph.KEY_ZX_NODE_BG_CUBES].add(cube)

        console.info(f"Realising node #{node} [{self.get_node_type(node)}] as cube #{cube} [{kind}@{position}]")

        return cube

    def is_edge_realised(self, source: NodeId, target: NodeId) -> bool:
        return self.get_edge_data(source, target)[AugmentedZxGraph.KEY_ZX_EDGE_BG_PATH] is not None

    def realise_edge(self, source: NodeId, target: NodeId, proposal: PathSpecification):
        if not self.is_node_realised(source):
            raise Exception(f"{source} is not placed; cannot connect with a path.")

        if not self.is_node_realised(target):
            raise Exception(f"{target} is not placed; cannot connect with a path.")

        if not self.has_edge(source, target):
            raise Exception(f"No edge {source}-{target} found in the ZX-graph.")

        if self.is_edge_realised(source, target):
            raise Exception(f"{source}-{target} is already realized by a path.")

        source_cube = proposal.source_cube
        target_cube = proposal.target_cube

        # Reject path if it is invalid.
        if not self.is_path_valid(source, target, proposal):
            raise Exception(f"Proposed path to realise edge {source}-{target} is invalid.")

        if not proposal:
            sequence = "[]"
        else:
            sequence = ""
            for position, kind in proposal.extras:
                sequence += f"{kind}@{position}"
        console.info(f"Realising edge {source}-{target} [type={self.get_edge_type(source,target)}] with extra cubes : {sequence}")

        # Representation of the path that will go into edge_realisations
        pipe_ids = []

        # Add all the extra cubes and pipes of the path to the BlockGraph
        previous_cube: int = source_cube

        for index in range(len(proposal.extras)):
            current_kind, current_position = proposal.extras[index]
            current_pipe_type = proposal.pipes[index]

            # Place the current cube and connect it to the previous cube.
            current_cube = self.place_cube(current_kind, current_position)
            self.__bg_graph.nodes[current_cube][AugmentedZxGraph.KEY_BG_CUBE_ZX_NODES] = set()
            self.connect_pipe(previous_cube, current_cube, current_pipe_type)

            # Extend the sequence of extra node ids
            pipe = tuple(sorted((previous_cube, current_cube)))
            pipe_ids.append( pipe )

            # Prepare for the next iteration
            previous_cube = current_cube

        # Make the final connection
        if target_cube not in self.get_realising_cubes(target):
            raise Exception(f"Target cube is not realising target node.")

        final_pipe_type = proposal.pipes[-1]
        self.connect_pipe(previous_cube, target_cube, final_pipe_type)

        pipe = tuple(sorted((previous_cube, target_cube)))
        pipe_ids.append( pipe )

        # Associate the path as a realisation of the edge
        self.get_edge_data(source, target)[AugmentedZxGraph.KEY_ZX_EDGE_BG_PATH] = pipe_ids

        # Update realising cubes of source node.
        source_kind = self.get_cube_kind(source_cube)
        for _, final in pipe_ids:
            if self.get_cube_kind(final) != source_kind:
                break
            self.__bg_graph.nodes[source_cube][AugmentedZxGraph.KEY_ZX_NODE_BG_CUBES].add(final)
        # Update realising cubes of target node.
        target_kind = self.get_cube_kind(target_cube)
        for start, _ in reversed(pipe_ids):
            if self.get_cube_kind(start) != target_kind:
                break
            self.__bg_graph.nodes[target_cube][AugmentedZxGraph.KEY_ZX_NODE_BG_CUBES].add(start)

    def place_cube(self, kind: CubeKind, position: Coordinates) -> CubeId:
        if position in self.occupied:
            raise Exception(f"Proposed position for {kind}@{position} is already occupied by another cube.")

        cube = self.__next_cube_id
        self.__next_cube_id += 1

        self.__bg_graph.add_node(cube)

        self.__bg_graph.nodes[cube][AugmentedZxGraph.KEY_BG_CUBE_ZX_NODES] = set()
        self.__bg_graph.nodes[cube][AugmentedZxGraph.KEY_BG_CUBE_KIND] = kind
        self.__bg_graph.nodes[cube][AugmentedZxGraph.KEY_BG_CUBE_POSITION] = position

        self.occupied.add(position)

        return cube

    def connect_pipe(self, source_cube: CubeId, target_cube: CubeId, pipe_type : EdgeType):
        if not self.__bg_graph.has_node(source_cube):
            raise Exception(f"Cube #{source_cube} not found in the BG-graph.")

        if not self.__bg_graph.has_node(target_cube):
            raise Exception(f"Cube #{target_cube} not found in the BG-graph.")

        if self.__bg_graph.has_edge(source_cube, target_cube):
            raise Exception(f"Cubes #{source_cube} and #{target_cube} are already connected by a pipe.")

        source_kind = self.get_cube_kind(source_cube)
        target_kind = self.get_cube_kind(target_cube)
        if not pipe_type in BlockGraphHelper.infer_pipe_type(source_kind, target_kind):
            raise Exception(f"Pipe type {pipe_type} is incompatible with source and target kinds [{source_kind}-{target_kind}].")

        # TODO: validate with respect to inferred pipe type between source and target cubes

        source_position = self.get_cube_position(source_cube)
        target_position = self.get_cube_position(target_cube)
        if source_position.get_manhattan_distance(target_position) != 1:
            raise Exception(f"Cubes #{source_cube}@{source_position} and #{target_cube}@{target_position} are not at adjacent positions.")

        self.__bg_graph.add_edge(source_cube, target_cube)
        self.__bg_graph.get_edge_data(source_cube, target_cube)[AugmentedZxGraph.KEY_BG_PIPE_TYPE] = pipe_type

    def is_path_valid(self, source: NodeId, target: NodeId, proposal: PathSpecification) -> bool:
        is_hadamard_path = False

        source_cube = proposal.source_cube

        if source_cube not in self.get_realising_cubes(source):
            raise Exception(f"Cube #{source_cube} is not realising source {source}.")

        source_kind: CubeKind = self.get_cube_kind(source_cube)
        source_position: Coordinates = self.get_cube_position(source_cube)

        console.info(f"Checking path validity:")
        console.info(f"> Source cube #{source_cube} [{source_kind}@{source_position}]")
        console.info(f"> Extra cubes: {proposal.extras}")

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
            if not Spacetime.contains(previous_reach, step_taken) or not Spacetime.contains(current_reach, step_taken):
                console.debug(f"> Previous reach contains step : {Spacetime.contains(previous_reach, step_taken)}")
                console.debug(f"> Current reach contains step : {Spacetime.contains(current_reach, step_taken)}")
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

        if self.is_node_realised(target):
            target_cube = proposal.target_cube
            target_kind = self.get_cube_kind(target_cube)
            target_position = self.get_cube_position(target_cube)

            if target_cube not in self.get_realising_cubes(target):
                raise Exception(f"Cube #{target_cube} is not realising source {target}.")

            # Check that the final step taken lies in the reach of the target cube
            step_taken = target_position - previous_position
            target_reach = target_kind.get_reach()
            if not Spacetime.contains(target_reach, step_taken):
                console.debug(f"> Reach of target cube does not contain final step : {Spacetime.contains(target_reach, step_taken)}")
                return False

            # Check that the current pipe has a type consistent with what is allowed
            current_pipe_type = proposal.pipes[-1]
            inferred = BlockGraphHelper.infer_pipe_type(previous_kind, target_kind)
            if not current_pipe_type in inferred:
                console.debug(f"> Final pipe type is not allowed between {previous_kind} and {target_kind} [{current_pipe_type} not in {inferred}].")
                return False

            if current_pipe_type == EdgeType.HADAMARD:
                is_hadamard_path = not is_hadamard_path

        edge_type = self.get_edge_type(source, target)

        if is_hadamard_path != (edge_type == EdgeType.HADAMARD):
            console.debug(f"> Proposed path is Hadamard-inconsistent with its purported edge [{edge_type}].")
            return False
        else:
            return True

    def __identify_cube_at_position(self, position: Coordinates) -> int:
        for cube in self.get_cubes():
            if self.get_cube_position(cube) == position:
                return cube

        return -1