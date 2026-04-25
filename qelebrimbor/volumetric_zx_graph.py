from collections import defaultdict, deque
from enum import Enum
from typing import Iterable
from itertools import chain

import pyzx
import networkx as nx
from ast import literal_eval as make_tuple

from networkx import neighbors

from qelebrimbor.common.coordinates import Coordinates

from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.helpers.blockgraph import BlockGraphHelper

from qelebrimbor.common.components import ZxNode, ZxEdge, BgCube, BgPipe
from qelebrimbor.common.attributes_zx import NodeId, NodeType, EdgeId, EdgeType, QubitId, LayerId
from qelebrimbor.common.attributes_bg import CubeId, CubeKind, PipeId
from qelebrimbor.common.paths import PathSpecification

import logging

from qelebrimbor.utilities.nmtfl_constraint import NoMoreThanFourLegsConstraint

console = logging.getLogger(__name__)
console.setLevel(logging.INFO)

class LayerTransition(Enum):
    EVERY = 0
    LOWER = 1
    INTRA = 2
    UPPER = 3
    OUTER = 4

    def matches(self, source_layer: LayerId, target_layer: LayerId):
        if self == LayerTransition.EVERY:
            return True
        elif self == LayerTransition.LOWER:
            return target_layer < source_layer
        elif self == LayerTransition.INTRA:
            return source_layer == target_layer
        elif self == LayerTransition.UPPER:
            return source_layer < target_layer
        else: # self == LayerTransition.OUTER
            return False

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
            for node, node_type in nodes:
                zx_node = ZxNode(id = node, type = node_type)
                self.add_node(zx_node.id)
                self.nodes[zx_node.id][VolumetricZxGraph.KEY_ZX_NODE] = zx_node

        if edges is not None:
            for edge, edge_type in edges:
                zx_source = self.get_zx_node(min(edge))
                zx_target = self.get_zx_node(max(edge))
                zx_edge = ZxEdge(source = zx_source, target = zx_target, type = edge_type)
                self.add_edge(zx_source.id, zx_target.id)
                self.edges[zx_source.id, zx_target.id][VolumetricZxGraph.KEY_ZX_EDGE] = zx_edge

        # TODO: split any spider with more than 4 edges (cfr. graph_manager.py; prep_3d_g)
        # TODO: does the choice of how to split such spiders affect the minimal achievable volume ?
        NoMoreThanFourLegsConstraint.enforce(self)

        self.__next_cube_id = self.number_of_nodes()

    @staticmethod
    def from_pyzx_graph(zx_graph: pyzx.graph.base.BaseGraph):
        converted_node_ids: dict[NodeId, NodeId] = dict()
        nodes: list[tuple[NodeId, NodeType]] = []
        for original_id in zx_graph.vertices():
            node_id = len(converted_node_ids)
            converted_node_ids[original_id] = node_id
            nodes.append((node_id, NodeType.convert_from_pyzx(zx_graph.type(original_id))))

        edges: list[tuple[EdgeId, EdgeType]] = []
        for edge in zx_graph.edges():
            source = converted_node_ids[min(edge)]
            target = converted_node_ids[max(edge)]
            edges.append(( (source,target) , EdgeType.convert_from_pyzx(zx_graph.edge_type(edge))))

        vzx = VolumetricZxGraph(nodes, edges)

        # Add qubit and layer information
        for original_id, node_id in converted_node_ids.items():
            node_qubit = int(zx_graph.qubit(original_id))
            node_layer = int(zx_graph.row(original_id))

            zx_node: ZxNode = vzx.nodes[node_id][VolumetricZxGraph.KEY_ZX_NODE]
            zx_node.qubit = node_qubit
            zx_node.layer = node_layer

            if node_qubit != -1:
                vzx.__zx_qubits[node_qubit].append(node_id)

            if node_layer != -1:
                vzx.__zx_layers[node_layer].append(node_id)

        return vzx

    def to_pyzx_graph(self, planar_scale: int = 8, filepath: str = None):
        pyzx_graph = pyzx.Graph()
        layout: dict[BgCube, tuple[float, float]] = dict()

        layer_qubit_information_missing = len(self.get_zx_qubits()) == 0 or len(self.get_zx_layers()) == 0
        # A PyZX graph obtained from a circuit has edges whose endpoints EITHER have the same layer OR the same qubit
        non_circuit_pyzx_graph = any(
            edge.source.layer != edge.target.layer and edge.source.qubit != edge.target.qubit
            for edge in self.get_zx_edges()
        )

        if layer_qubit_information_missing or non_circuit_pyzx_graph:
            for cube_id, coordinates in nx.planar_layout(self.__bg_graph, scale = planar_scale).items():
                layout[self.get_bg_cube(cube_id)] = coordinates[0], coordinates[1]
        else:
            # Compute the coordinates of the layers taking into account the extra nodes added to realise edges
            layer_coordinates: dict[LayerId, float] = defaultdict(int)
            current_coordinate = -1.0
            for layer in self.get_zx_layers():
                minimal_coordinate = current_coordinate + 1.0
                for edge in self.get_zx_edges(layered = (layer, LayerTransition.LOWER)):
                    previous = edge.source if edge.source.layer < edge.target.layer else edge.target
                    minimal_coordinate = max(minimal_coordinate, layer_coordinates[previous.layer] + edge.number_of_pipes)
                    console.debug(f"> {edge} [{edge.source.realising_cube}/{edge.target.realising_cube}] yields {minimal_coordinate}")
                current_coordinate = minimal_coordinate
                layer_coordinates[layer] = current_coordinate
                console.debug(f"Layer {layer} : {current_coordinate}")

            # Compute the coordinates of the qubits taking into account the extra nodes added to realise edges
            qubit_coordinates: dict[QubitId, float] = defaultdict(int)
            current_coordinate = -1.0
            for qubit in self.get_zx_qubits():
                minimal_coordinate = current_coordinate + 1.0
                for node in self.get_zx_nodes(qubit = qubit):
                    for neighbor in self.get_zx_neighbors(node, transition = LayerTransition.INTRA):
                        edge = self.get_zx_edge(node.id, neighbor.id)
                        previous = node if node.qubit < neighbor.qubit else neighbor
                        minimal_coordinate = max(minimal_coordinate, qubit_coordinates[previous.qubit] + edge.number_of_pipes)
                current_coordinate = minimal_coordinate
                qubit_coordinates[qubit] = current_coordinate
                console.debug(f"Qubit {qubit} : {current_coordinate}")

            # Compute the placement of the nodes of the input ZX-graph
            for node in filter(lambda nd: nd.is_realised(), self.get_zx_nodes()):
                layout[node.realising_cube] = layer_coordinates[node.layer] , qubit_coordinates[node.qubit]
                console.debug(f"Layout {node.realising_cube} : {layout[node.realising_cube]}")

            # Compute the placement of the extra nodes added to realise the edges of the input ZX-graph
            for edge in filter(lambda ed: ed.is_realised(), self.get_zx_edges()):
                if edge.source.layer == edge.target.layer:
                    start: QubitId = min(edge.source.qubit, edge.target.qubit)
                    final: QubitId = max(edge.source.qubit, edge.target.qubit)
                    offset = qubit_coordinates[start]
                    step = abs(qubit_coordinates[final] - qubit_coordinates[start]) / float(edge.number_of_pipes)
                    excess_cubes = edge.excess_cubes if edge.source.qubit < edge.target.qubit else reversed(edge.excess_cubes)
                else: # edge.source.qubit == edge.target.qubit
                    start: LayerId = min(edge.source.layer, edge.target.layer)
                    final: LayerId = max(edge.source.layer, edge.target.layer)
                    offset = layer_coordinates[start]
                    step = abs(layer_coordinates[final] - layer_coordinates[start]) / float(edge.number_of_pipes)
                    excess_cubes = edge.excess_cubes if edge.source.layer > edge.target.layer else reversed(edge.excess_cubes)

                for cube in excess_cubes:
                    offset += step
                    if edge.source.layer == edge.target.layer:
                        layout[cube] = layer_coordinates[edge.source.layer], offset
                    else: # edge.source.qubit == edge.target.qubit
                        layout[cube] = offset, qubit_coordinates[edge.source.qubit]
                    console.debug(f"Layout [E] {cube} : {layout[cube]}")

        for cube in self.get_bg_cubes():
            x, y = layout[cube] if cube in layout else (-1,-1)
            pyzx_graph.add_vertex(
                index = cube.id, ty = NodeType.convert_into_pyzx(cube.kind.get_type()), row = x, qubit = y
            )
        for pipe in self.get_bg_pipes():
            pyzx_graph.add_edge((pipe.source.id, pipe.target.id), EdgeType.convert_into_pyzx(pipe.type))

        pyzx.draw(pyzx_graph, labels = True)

        if filepath is not None:
            with open(filepath, 'w') as file:
                file.write(pyzx_graph.to_json())

        return pyzx_graph

    def get_zx_nodes(self, node_type: NodeType | None = None, qubit: QubitId | None = None, layer: LayerId | None = None):
        return filter(
            lambda node: (node_type is None or node.type == node_type) and
                         (qubit is None or node.qubit == qubit) and
                         (layer is None or node.layer == layer),
            map(lambda nd: self.get_zx_node(nd), self.nodes)
        )

    def get_zx_edges(self, edge_type: EdgeType | None = None, layered: tuple[LayerId, LayerTransition] | None = None):
        if layered is None:
            edges = map(lambda edge: self.get_zx_edge(*edge), self.edges)
        else:
            layer, transition = layered
            if len(self.__zx_layers) == 0:
                console.warning(f"Requesting layered edges but VolumetricZxGraph does not contain layer information.")
            edges = chain.from_iterable(map(
                lambda zxn: map(
                    lambda neighbor : self.get_zx_edge(zxn.id, neighbor.id),
                    filter(
                        lambda nb: transition != LayerTransition.INTRA or zxn.id < nb.id,
                        self.get_zx_neighbors(zxn, transition = transition)
                    )
                ),
                self.get_zx_nodes(layer = layer)
            ))

        return filter(lambda edge: edge_type is None or edge.type == edge_type, edges)

    def get_zx_neighbors(
            self, node: ZxNode, edge_type: EdgeType | None = None, transition: LayerTransition = LayerTransition.EVERY
    ) -> Iterable[ZxNode]:
        return filter(
            lambda neighbor: transition.matches(node.layer, neighbor.layer) and
                             (edge_type is None or self.get_zx_edge(node.id, neighbor.id).type == edge_type),
            map(self.get_zx_node, self.neighbors(node.id))
        )

    def get_zx_degree(self, node_id: NodeId) -> int:
        return int(self.degree[node_id])

    def get_zx_node(self, node_id: NodeId) -> ZxNode:
        return self.nodes[node_id][VolumetricZxGraph.KEY_ZX_NODE]

    def get_zx_edge(self, source_id: NodeId, target_id: NodeId) -> ZxEdge:
        return self.edges[source_id, target_id][VolumetricZxGraph.KEY_ZX_EDGE]

    def get_zx_qubits(self):
        return self.__zx_qubits.keys()

    def get_zx_layers(self):
        return self.__zx_layers.keys()

    def volume(self) -> int:
        return sum(1 for cube in self.get_bg_cubes() if cube.kind not in [ CubeKind.OOO, CubeKind.YYY ])

    def number_of_cubes(self, kind: CubeKind | None = None) -> int:
        return sum(1 for _ in self.get_bg_cubes(kind = kind))

    def number_of_pipes(self, pipe_type: EdgeType | None = None) -> int:
        return sum(1 for _ in self.get_bg_pipes(pipe_type = pipe_type))

    def get_bg_cubes(self, kind: CubeKind | None = None):
        return map(lambda cb: self.get_bg_cube(cb),
            filter(
                lambda cb: (kind is None or self.get_bg_cube(cb).kind == kind), self.__bg_graph.nodes()
            )
        )

    def get_bg_pipes(self, pipe_type: EdgeType | None = None):
        return map(lambda pp: self.get_bg_pipe(*pp),
            filter(
                lambda pp: (pipe_type is None or self.get_bg_pipe(*pp).type == pipe_type),
                self.__bg_graph.edges()
            )
        )

    def get_bg_cube(self, cube_id: CubeId) -> BgCube:
        return self.__bg_graph.nodes[cube_id][VolumetricZxGraph.KEY_BG_CUBE]

    def get_bg_pipe(self, source_id: CubeId, target_id: CubeId) -> BgPipe:
        return self.__bg_graph.edges[source_id, target_id][VolumetricZxGraph.KEY_BG_PIPE]

    def get_bg_neighbours(self, cube: BgCube, pipe_type: EdgeType | None = None) -> Iterable[BgCube]:
        return filter(
            lambda nb : (pipe_type is None or self.get_bg_pipe(cube.id, nb.id).type == pipe_type),
            map(self.get_bg_cube, self.__bg_graph.neighbors(cube.id))
        )

    def get_bg_degree(self, cube_id: CubeId) -> int:
        return int(self.__bg_graph.degree[cube_id])

    def get_equivalent_bg_cubes(self, cube: BgCube) -> tuple[Iterable[BgCube], Iterable[BgPipe]]:
        equivalent_cubes: set[BgCube] = { cube }
        connecting_pipes: set[BgPipe] = set()

        queue: deque[BgCube] = deque([ cube ])
        while queue:
            current = queue.popleft()
            for neighbor in self.get_bg_neighbours(current):
                if neighbor.kind != cube.kind:
                    continue

                source, target = current.id, neighbor.id
                if source > target:
                    source, target = target, source
                connecting_pipes.add( self.get_bg_pipe(source, target) )

                if neighbor not in equivalent_cubes:
                    equivalent_cubes.add(neighbor)
                    queue.append(neighbor)

        return equivalent_cubes, connecting_pipes

    def is_zx_node_realised(self, node: NodeId) -> bool:
        return self.get_zx_node(node).realising_cube is not None

    def realise_zx_node(self, node: ZxNode, cube: BgCube) -> CubeId:
        """Realise the node as a cube of the given kind placed at the given coordinates."""
        if cube.kind not in CubeKind.suitable_kinds(node.type):
            raise Exception(f"Proposed cube {cube} is not compatible with {node.type}")

        if not self.has_node(node.id):
            raise Exception(f"Node {node} not found in the ZX-graph.")

        cube_id = self.place_cube(cube)
        self.__bg_graph.nodes[cube_id][VolumetricZxGraph.KEY_BG_CUBE].realised_node = node
        self.nodes[node.id][VolumetricZxGraph.KEY_ZX_NODE].realising_cube = cube

        console.info(f"Realising node {node} as cube {cube}")

        return cube_id

    def realise_zx_edge(self, source: NodeId, target: NodeId, proposal: PathSpecification):
        if not self.get_zx_node(source).is_realised():
            raise Exception(f"{source} is not realised; cannot connect with a path.")

        if not self.get_zx_node(target).is_realised():
            raise Exception(f"{target} is not realised; cannot connect with a path.")

        if not self.has_edge(source, target):
            raise Exception(f"No edge {source}-{target} found in the ZX-graph.")

        zx_edge = self.get_zx_edge(source, target)
        if zx_edge.is_realised():
            raise Exception(f"{source}-{target} is already realized by a path.")

        # Reject path if it is invalid.
        if not self.is_path_valid(zx_edge, proposal):
            raise Exception(f"Proposed path to realise edge {zx_edge} is invalid.")

        pipe_ids = self.connect_path(proposal)

        # Associate the path as a realisation of the edge
        zx_edge.realisation = pipe_ids

        console.info(f"Realising edge {zx_edge} with pipes : {pipe_ids}")

    def place_cube(self, cube: BgCube) -> CubeId:
        if cube.position in self.occupied:
            raise Exception(f"Proposed position for {cube} is already occupied by another cube.")

        cube.id = self.__next_cube_id
        self.__next_cube_id += 1

        self.__bg_graph.add_node(cube.id)
        self.__bg_graph.nodes[cube.id][VolumetricZxGraph.KEY_BG_CUBE] = cube

        self.occupied.add(cube.position)

        return cube.id

    def connect_path(self, proposal: PathSpecification) -> list[BgPipe]:
        source_cube = proposal.source_cube
        target_cube = proposal.target_cube
        # Representation of the path that will go into edge_realisations
        pipe_ids: list[BgPipe] = []

        # Add all the extra cubes and pipes of the path to the BlockGraph
        previous_cube: BgCube = source_cube

        for index in range(len(proposal.extras)):
            extra_cube = proposal.extras[index]
            extra_pipe_type = proposal.pipes[index]

            # Place the current cube and connect it to the previous cube.
            extra_cube_id = self.place_cube(extra_cube)
            self.connect_pipe(previous_cube, extra_cube, extra_pipe_type)

            # Extend the sequence of extra node ids
            pipe = BgPipe(source = previous_cube, target = extra_cube, type = extra_pipe_type)
            pipe_ids.append( pipe )

            # Prepare for the next iteration
            previous_cube = extra_cube

        # Make the final connection
        final_pipe_type = proposal.pipes[-1]
        self.connect_pipe(previous_cube, target_cube, final_pipe_type)

        pipe = BgPipe(source = previous_cube, target = target_cube, type = final_pipe_type)
        pipe_ids.append( pipe )

        return pipe_ids

    def connect_pipe(self, source: BgCube, target: BgCube, pipe_type : EdgeType):
        if not self.__bg_graph.has_node(source.id):
            raise Exception(f"Cube {source} not found in the BG-graph.")

        if not self.__bg_graph.has_node(target.id):
            raise Exception(f"Cube {target} not found in the BG-graph.")

        if self.__bg_graph.has_edge(source.id, target.id):
            raise Exception(f"Cubes {source} and {target} are already connected by a pipe.")

        if not pipe_type in BlockGraphHelper.infer_pipe_type(source.kind, target.kind):
            raise Exception(f"Pipe type {pipe_type} is incompatible with source and target kinds [{source.kind}-{target.kind}].")

        # TODO: validate with respect to inferred pipe type between source and target cubes

        if source.position.get_manhattan_distance(target.position) != 1:
            raise Exception(f"Cubes {source} and {target} are not at adjacent positions.")

        self.__bg_graph.add_edge(source.id, target.id)
        bg_pipe = BgPipe(source, target, pipe_type)
        self.__bg_graph.edges[source.id, target.id][VolumetricZxGraph.KEY_BG_PIPE] = bg_pipe

    # TODO: figure the rules for this as it gets complicated quickly ...
    def is_realising_cube(self, node: ZxNode, cube: BgCube):
        if cube.realised_node == node:
            return True

        visited: set[BgCube] = { cube }
        queue: deque[BgCube] = deque([cube])
        while queue:
            current = queue.popleft()
            for neighbor in self.get_bg_neighbours(current, pipe_type = EdgeType.IDENTITY):
                if neighbor.kind.get_type() == cube.kind.get_type():
                    if neighbor.realised_node == node:
                        return True

                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
                elif self.get_bg_degree(neighbor.id) == 2:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

        console.info(f"Neigborhood visited to find alternative : {visited}")

        return False

    def is_path_valid(self, edge: ZxEdge, proposal: PathSpecification) -> bool:
        is_hadamard_path = False

        start = proposal.source_cube
        final = proposal.target_cube

        if not (self.is_realising_cube(edge.source, start) or self.is_realising_cube(edge.target, start)):
            raise Exception(f"Start cube {start} is not realising either endpoint of edge {edge} [proposal={proposal}].")

        if not (self.is_realising_cube(edge.source, final) or self.is_realising_cube(edge.target, final)):
            raise Exception(f"Final cube {final} is not realising either endpoint of edge {edge} [proposal={proposal}].")

        console.debug(f"Validating path proposal for {edge} : {proposal}.")

        previous: BgCube = start
        previous_reach = start.kind.get_reach()

        extra_positions = set()

        for index in range(len(proposal.extras)):
            current: BgCube = proposal.extras[index]
            current_reach = current.kind.get_reach()

            # Check that the cube type is either X or Z (Y and boundaries must be leaves)
            if current.kind in [ CubeKind.OOO, CubeKind.YYY ]:
                console.warning(f"> CubeKind.OOO and CubeKind.YYY can only appear at the ends of a path : {current}.")
                return False

            # Check that the current_position is not already occupied
            if current.position in self.occupied:
                console.warning(f"> Current position is already occupied : {current}")
                return False

            # Check that the current_position is not already occupied by an extra cube
            if current.position in extra_positions:
                console.warning(f"> Current position is already in path : {current}")
                return False
            extra_positions.add(current.position)

            # Check that the step taken lies in both reaches of successive cubes
            step_taken = current.position - previous.position
            if SpacetimeHelper.ORIGIN.get_manhattan_distance(step_taken) != 1:
                console.warning(f"> Consecutive cubes are not adjacent [{previous}-{current}]")
                return False

            if not SpacetimeHelper.contains(previous_reach, step_taken) or not SpacetimeHelper.contains(current_reach, step_taken):
                console.warning(f"> Reaches do not contain step [{step_taken}]: {previous} {current}")
                return False

            # Check that the current pipe has a type consistent with what is allowed
            current_pipe_type = proposal.pipes[index]
            inferred = BlockGraphHelper.infer_pipe_type(previous.kind, current.kind)
            if not current_pipe_type in inferred:
                console.warning(f"> Pipe type is not allowed between {previous} and {current} [{current_pipe_type} not in {inferred}].")
                return False

            if current_pipe_type == EdgeType.HADAMARD:
                is_hadamard_path = not is_hadamard_path

            previous = current
            previous_reach = current_reach

        # Check that the final step taken lies in the reach of the target cube
        step_taken = final.position - previous.position

        if SpacetimeHelper.ORIGIN.get_manhattan_distance(step_taken) != 1:
            console.warning(f"> Consecutive cubes are not adjacent [{previous.position}-{final.position}]")
            return False

        final_reach = final.kind.get_reach()
        if not SpacetimeHelper.contains(previous_reach, step_taken) or not SpacetimeHelper.contains(final_reach, step_taken):
            console.warning(f"> Reaches do not contain step [{step_taken}]: {previous} {final}")
            return False

        # Check that the current pipe has a type consistent with what is allowed
        current_pipe_type = proposal.pipes[-1]
        inferred = BlockGraphHelper.infer_pipe_type(previous.kind, final.kind)
        if current_pipe_type not in inferred:
            console.warning(f"> Pipe type is not allowed between {previous} and {final} [{current_pipe_type} not in {inferred}].")
            return False

        if current_pipe_type == EdgeType.HADAMARD:
            is_hadamard_path = not is_hadamard_path

        if is_hadamard_path != (edge.type == EdgeType.HADAMARD):
            console.debug(f"> Proposed path is Hadamard-inconsistent with its purported edge {edge}.")
            return False
        else:
            return True

    def log_summary(self, nodes: bool = True, edges: bool = True, layers: bool = True, qubits: bool = True, cubes: bool = True, pipes: bool = True):
        if nodes:
            for node_type in [NodeType.O, NodeType.X, NodeType.Y, NodeType.Z]:
                content = ""
                count = 0
                for node in self.get_zx_nodes(node_type = node_type):
                    content += f"{node.id} "
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
            for layer in self.get_zx_layers():
                console.info(f"Layer {layer}  : {list(map(lambda zn: zn.id, self.get_zx_nodes(layer = layer)))}")

        if qubits:
            for qubit in self.get_zx_qubits():
                console.info(f"Qubit {qubit}  : {list(map(lambda zn: zn.id, self.get_zx_nodes(qubit = qubit)))}")

        if cubes:
            for cube in self.get_bg_cubes():
                console.info(f"Cube {cube.id}  : {cube.kind}@{cube.position} {cube.realised_node}")

        if pipes:
            for pipe in self.get_bg_pipes():
                console.info(f"Pipe {pipe.source}-{pipe.target}  : {pipe.type}")

    def print_summary(self):
        for node_type in [NodeType.O, NodeType.X, NodeType.Y, NodeType.Z]:
            content = ""
            for node in self.get_zx_nodes(node_type=node_type):
                content += f"{node.id} "
            print(f"Nodes {node_type.name}: {content}")

        content = ""
        for edge in self.edges:
            content += f"{edge} "
        print(f"Edges  : {content}")

        for layer in self.get_zx_layers():
            print(f"Layer {layer}  : {list(map(lambda zn: zn.id, self.get_zx_nodes(layer = layer)))}")

        for qubit in self.get_zx_qubits():
            print(f"Qubit {qubit}  : {list(map(lambda zn: zn.id, self.get_zx_nodes(qubit = qubit)))}")

        for cube in self.get_bg_cubes():
            realised_node = self.get_bg_cube(cube).realised_node
            print(f"Cube #{cube.id}  : {cube.kind}@{self.get_bg_cube(cube).position} {realised_node}")

        for pipe in self.get_bg_pipes():
            print(f"Pipe {pipe.source}-{pipe.target} : {pipe.type.name}")

    def log_report(self):
        number_of_spiders = sum(1 for node in self.get_zx_nodes() if node.type in { NodeType.X , NodeType.Z })
        number_of_realised_spiders = sum(1 for node in self.get_zx_nodes() if node.type in { NodeType.X, NodeType.Z } and node.is_realised())
        console.info(f"Realised spiders : {number_of_realised_spiders} of {number_of_spiders}")
        number_of_boundaries = sum(1 for _ in self.get_zx_nodes(node_type = NodeType.O))
        number_of_realised_boundaries = sum(1 for node in self.get_zx_nodes(node_type = NodeType.O) if node.is_realised())
        console.info(f"Realised boundaries : {number_of_realised_boundaries} of {number_of_boundaries}")
        console.info(f"Overall volume : {self.volume()}")

        excess_volume: dict[ZxEdge, int] = dict()
        for edge in self.get_zx_edges():
            if edge.is_realised():
                count = sum(1 for _ in edge.realisation) - 1
                if count > 0:
                    excess_volume[ edge ] = count

        console.info(f"Excess volume : +{sum(excess_volume.values())}")
        for edge, volume in excess_volume.items():
            console.info(f"> Edge {edge} : +{volume}")

    @staticmethod
    def from_file(filepath: str):
        with open(filepath, 'r') as file:
            # Instantiate the VolumetricZxGraph
            vzx = VolumetricZxGraph()

            # Read the blockgraph header
            header = file.readline()
            if header not in [ "VOLUMETRIC-ZX-GRAPH 0.0.1\n", "BLOCKGRAPH 0.1.0;\n" ] :
                raise Exception(f"Invalid file format. Header <VOLUMETRIC-ZX-GRAPH 0.0.1> not found [got={header}].")

            # Read the empty line between the blockgraph header and the cubes header
            file.readline()

            # Read the nodes header
            header = file.readline()
            if header != "NODES: index;type;qubit;layer;realising_cube\n":
                raise Exception(f"Invalid file format. Header for NODES not found [got={header}].")

            zx_node_bg_cube: dict[CubeId, ZxNode] = dict()

            # Read all the lines describing nodes
            current_line = file.readline()
            while current_line and current_line != "\n":
                if current_line != "":
                    node_id, node_type, qubit, layer, realising_cube = current_line.split(';')
                    node = int(node_id)
                    vzx.add_node(node)
                    zx_node = ZxNode(id = node, type = NodeType[node_type], qubit = int(qubit), layer = int(layer))
                    zx_node_bg_cube[int(realising_cube)] = zx_node
                    vzx.nodes[node][VolumetricZxGraph.KEY_ZX_NODE] = zx_node
                    if int(qubit) != -1:
                        vzx.__zx_qubits[int(qubit)].append(node)
                    if int(layer) != -1:
                        vzx.__zx_layers[int(layer)].append(node)
                current_line = file.readline()

            # Read the edges header
            header = file.readline()
            if header != "EDGES: source;target;type;realisation\n":
                raise Exception(f"Invalid file format. Header for EDGES not found [got={header}].")

            zx_edge_bg_pipe: dict[ZxEdge, list[PipeId]] = dict()

            # Read all the lines describing edges
            current_line = file.readline()
            while current_line and current_line != "\n":
                if current_line != "":
                    source_id, target_id, edge_type, realisation = current_line.split(';')
                    source = int(source_id)
                    target = int(target_id)
                    vzx.add_edge(source, target)
                    zx_edge = ZxEdge(source = source, target = target, type = EdgeType[edge_type])
                    zx_edge_bg_pipe[zx_edge] = [make_tuple(pair) for pair in realisation[1:-2].split(':')]
                    vzx.edges[source, target][VolumetricZxGraph.KEY_ZX_EDGE] = zx_edge
                current_line = file.readline()

            # Read the cubes header
            header = file.readline()
            if header != "CUBES: index;x;y;z;kind;label;\n":
                raise Exception(f"Invalid file format. Header for CUBES not found [got={header}].")

            # Read all the lines describing cubes
            current_line = file.readline()
            while current_line and current_line != "\n":
                if current_line != "":
                    cube_id, x, y, z, kind, realised_node, _ = current_line.split(';')
                    cube = int(cube_id)
                    vzx.__bg_graph.add_node(cube)
                    bg_cube = BgCube(
                        id = cube, kind = CubeKind[kind.upper()], position = Coordinates(int(x), int(y), int(z))
                    )
                    if cube in zx_node_bg_cube:
                        bg_cube.realised_node = zx_node_bg_cube[cube]
                    vzx.__bg_graph.nodes[cube][VolumetricZxGraph.KEY_BG_CUBE] = bg_cube
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
                    source = vzx.get_bg_cube(int(source_id))
                    target = vzx.get_bg_cube(int(target_id))
                    vzx.__bg_graph.add_edge(source.id, target.id)
                    vzx.__bg_graph.edges[source.id, target.id][VolumetricZxGraph.KEY_BG_PIPE] = BgPipe(
                        source, target, EdgeType[pipe_type[:-1]]
                    )
                current_line = file.readline()

            # Encode correspondence between ZX and BG
            for zx_node, bg_cube_id in zx_node_bg_cube.items():
                bg_cube = vzx.get_bg_cube(bg_cube_id)
                bg_cube.realised_node = zx_node
                zx_node.realising_cube = bg_cube

            for zx_edge, bg_pipe_ids in zx_edge_bg_pipe.items():
                zx_edge.realisation = list(map(lambda pp: vzx.get_bg_pipe(*pp), bg_pipe_ids))

            return vzx

    def into_file(self, filepath: str):
        with (open(filepath, 'w') as file):
            file.write(f"VOLUMETRIC-ZX-GRAPH 0.0.1\n")

            # Store node information
            file.write("\nNODES: index;type;qubit;layer;realising_cube\n")
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
                    f"{edge.source.id};{edge.target.id};{edge.type};[{':'.join(map(str, edge.realisation))}]\n"
                    for edge in self.get_zx_edges()
                ]
            )

            # Store cube information
            file.write("\nCUBES: index;x;y;z;kind\n")
            file.writelines(
                [
                    f"{cube.id};{';'.join(map(str, iter(cube.position)))};{cube.kind.name}\n"
                    for cube in self.get_bg_cubes()
                ]
            )

            # Store pipe information
            file.write("\nPIPES: source;target;type;\n")
            file.writelines(
                [
                    f"{pipe.source};{pipe.target};{pipe.type.name}\n"
                    for pipe in self.get_bg_pipes()
                ]
            )

    @staticmethod
    def from_topologiq_file(filepath: str):
        with open(filepath, 'r') as file:
            # Instantiate the VolumetricZxGraph
            vzx = VolumetricZxGraph()

            # Read the blockgraph header
            header = file.readline()
            if header != "BLOCKGRAPH 0.1.0;\n" :
                raise Exception(f"Invalid file format. Header <BLOCKGRAPH 0.1.0> not found [got={header}].")

            # Read the empty line between the blockgraph header and the cubes header
            file.readline()

            # Read the nodes header
            header = file.readline()
            if header != "NODES: index;type;qubit;layer;realising_cube\n":
                raise Exception(f"Invalid file format. Header for NODES not found [got={header}].")

            zx_node_bg_cube: dict[ZxNode, CubeId] = dict()

            # Read all the lines describing nodes
            current_line = file.readline()
            while current_line and current_line != "\n":
                if current_line != "":
                    node_id, node_type, qubit, layer, realising_cube = current_line.split(';')
                    node = int(node_id)
                    vzx.add_node(node)
                    zx_node = ZxNode(id = node, type = NodeType[node_type], qubit = int(qubit), layer = int(layer))
                    vzx.nodes[node][VolumetricZxGraph.KEY_ZX_NODE] = zx_node
                    zx_node_bg_cube[zx_node] = int(realising_cube)
                    if int(qubit) != -1:
                        vzx.__zx_qubits[int(qubit)].append(node)
                    if int(layer) != -1:
                        vzx.__zx_layers[int(layer)].append(node)
                current_line = file.readline()

            # Read the edges header
            header = file.readline()
            if header != "EDGES: source;target;type;realisation\n":
                raise Exception(f"Invalid file format. Header for EDGES not found [got={header}].")

            zx_edge_bg_pipe: dict[ZxEdge, list[PipeId]] = dict()

            # Read all the lines describing edges
            current_line = file.readline()
            while current_line and current_line != "\n":
                if current_line != "":
                    source_id, target_id, edge_type, realisation = current_line.split(';')
                    source = vzx.get_zx_node(int(source_id))
                    target = vzx.get_zx_node(int(target_id))
                    vzx.add_edge(source.id, target.id)
                    zx_edge = ZxEdge(source = source, target = target, type = EdgeType[edge_type])
                    vzx.edges[source.id, target.id][VolumetricZxGraph.KEY_ZX_EDGE] = zx_edge
                    zx_edge_bg_pipe[zx_edge] = [ make_tuple(pair) for pair in realisation[1:-2].split(':') ]
                current_line = file.readline()

            # Read the cubes header
            header = file.readline()
            if header != "CUBES: index;x;y;z;kind;label;\n":
                raise Exception(f"Invalid file format. Header for CUBES not found [got={header}].")

            # Read all the lines describing cubes
            current_line = file.readline()
            while current_line and current_line != "\n":
                if current_line != "":
                    cube_id, x, y, z, kind, realised_node, _ = current_line.split(';')
                    cube = int(cube_id)
                    vzx.__bg_graph.add_node(cube)
                    bg_cube = BgCube(
                        id = cube, kind = CubeKind[kind.upper()], position = Coordinates(int(x), int(y), int(z)) / 3.0
                    )
                    vzx.__bg_graph.nodes[cube][VolumetricZxGraph.KEY_BG_CUBE] = bg_cube
                current_line = file.readline()

            # Read the pipes header
            header = file.readline()
            if header != "PIPES: src;tgt;kind;\n":
                raise Exception(f"Invalid file format. Header for PIPES not found [got={header}].")

            # Read all the lines describing pipes
            current_line = file.readline()
            while current_line and current_line != "\n":
                if current_line != "":
                    source_id, target_id, pipe_kind, _ = current_line.split(';')
                    source = vzx.get_bg_cube(int(source_id))
                    target = vzx.get_bg_cube(int(target_id))
                    vzx.__bg_graph.add_edge(source.id, target.id)
                    vzx.__bg_graph.edges[source.id, target.id][VolumetricZxGraph.KEY_BG_PIPE] = BgPipe(
                        source, target, EdgeType.HADAMARD if 'h' in pipe_kind else EdgeType.IDENTITY
                    )
                current_line = file.readline()

            for zx_node, bg_cube_id in zx_node_bg_cube.items():
                bg_cube = vzx.get_bg_cube(bg_cube_id)
                bg_cube.realised_node = zx_node
                zx_node.realising_cube = bg_cube

            for zx_edge, bg_pipe_ids in zx_edge_bg_pipe.items():
                zx_edge.realisation = list(map(lambda pp: vzx.get_bg_pipe(*pp), bg_pipe_ids))

            return vzx