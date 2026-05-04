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

from collections import defaultdict, deque
from enum import Enum
from typing import Iterable
from itertools import chain

import networkx as nx

from qelebrimbor.common.coordinates import Coordinates

from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.helpers.blockgraph import BlockGraphHelper

from qelebrimbor.common.path import Path
from qelebrimbor.common.components import ZxNode, ZxEdge, BgCube, BgPipe
from qelebrimbor.common.attributes_zx import NodeId, NodeType, EdgeType, QubitId, LayerId
from qelebrimbor.common.attributes_bg import CubeId, CubeKind, PipeId
from qelebrimbor.spacetime.fabric import SpacetimeFabric

from qelebrimbor.utilities.nmtfl_constraint import NoMoreThanFourLegsConstraint

import logging
console = logging.getLogger(__name__)

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
        edges: Iterable[tuple[NodeId, NodeId, EdgeType]] | None = None,
        qubits: dict[NodeId, QubitId] | None = None,
        layers: dict[NodeId, LayerId] | None = None,
    ):
        # Separate ZX-graph and BG-graph
        super(VolumetricZxGraph, self).__init__()
        self.blockgraph: nx.Graph = nx.Graph()

        # Keeps track of which nodes appear on which qubit-line or layer of the ZX-graph
        self.__zx_qubits: dict[QubitId, list[NodeId]] = defaultdict(list)
        self.__zx_layers: dict[LayerId, list[NodeId]] = defaultdict(list)

        # Keeps track of the contents in spacetime
        self.spacetime: SpacetimeFabric = SpacetimeFabric()

        if nodes is not None:
            for node, node_type in nodes:
                qubit = qubits[node] if qubits and node in qubits else -1
                layer = layers[node] if layers and node in layers else -1
                zx_node = ZxNode(id = node, type = node_type, qubit = qubit, layer = layer)
                self.add_node(zx_node.id)
                self.nodes[zx_node.id][VolumetricZxGraph.KEY_ZX_NODE] = zx_node

                if zx_node.qubit != -1:
                    self.__zx_qubits[zx_node.qubit].append(node)

                if zx_node.layer != -1:
                    self.__zx_layers[zx_node.layer].append(node)

        if edges is not None:
            for endpoint0, endpoint1, edge_type in edges:
                zx_source = self.get_zx_node(min(endpoint0, endpoint1))
                zx_target = self.get_zx_node(max(endpoint0, endpoint1))
                zx_edge = ZxEdge(source = zx_source, target = zx_target, type = edge_type)
                self.add_edge(zx_source.id, zx_target.id)
                self.edges[zx_source.id, zx_target.id][VolumetricZxGraph.KEY_ZX_EDGE] = zx_edge

        # TODO: split any spider with more than 4 edges (cfr. graph_manager.py; prep_3d_g)
        # TODO: does the choice of how to split such spiders affect the minimal achievable volume ?
        NoMoreThanFourLegsConstraint.enforce(self)

        self.__next_cube_id = self.number_of_nodes()

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
                lambda cb: (kind is None or self.get_bg_cube(cb).kind == kind), self.blockgraph.nodes()
            )
        )

    def get_bg_pipes(self, pipe_type: EdgeType | None = None):
        return map(lambda pp: self.get_bg_pipe(*pp),
            filter(
                lambda pp: (pipe_type is None or self.get_bg_pipe(*pp).type == pipe_type),
                self.blockgraph.edges()
            )
        )

    def get_bg_cube(self, cube_id: CubeId) -> BgCube:
        return self.blockgraph.nodes[cube_id][VolumetricZxGraph.KEY_BG_CUBE]

    def get_bg_pipe(self, source_id: CubeId, target_id: CubeId) -> BgPipe:
        return self.blockgraph.edges[source_id, target_id][VolumetricZxGraph.KEY_BG_PIPE]

    def get_bg_neighbours(self, cube: BgCube, pipe_type: EdgeType | None = None) -> Iterable[BgCube]:
        return filter(
            lambda nb : (pipe_type is None or self.get_bg_pipe(cube.id, nb.id).type == pipe_type),
            map(self.get_bg_cube, self.blockgraph.neighbors(cube.id))
        )

    def get_bg_degree(self, cube_id: CubeId) -> int:
        return int(self.blockgraph.degree[cube_id])

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

    def realise_zx_node(self, node: ZxNode, cube: BgCube) -> CubeId:
        """Realise the node as a cube of the given kind placed at the given coordinates."""
        if cube.kind not in CubeKind.suitable_kinds(node.type):
            raise Exception(f"Proposed cube {cube} is not compatible with {node.type}")

        if not self.has_node(node.id):
            raise Exception(f"Node {node} not found in the ZX-graph.")

        cube_id = self.place_cube(cube)
        self.blockgraph.nodes[cube_id][VolumetricZxGraph.KEY_BG_CUBE].realised_node = node
        self.nodes[node.id][VolumetricZxGraph.KEY_ZX_NODE].realising_cube = cube

        console.debug(f"Realising node {node} as cube {cube}")

        return cube_id

    def realise_zx_edge(self, source: NodeId, target: NodeId, proposal: Path):
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

        console.debug(f"Realising edge {zx_edge} with pipes : {pipe_ids}")

    def place_cube(self, cube: BgCube) -> CubeId:
        if not self.spacetime.available(cube.position):
            raise Exception(f"Proposed position for {cube} is already occupied by another cube.")

        cube.id = self.__next_cube_id
        self.__next_cube_id += 1

        self.blockgraph.add_node(cube.id)
        self.blockgraph.nodes[cube.id][VolumetricZxGraph.KEY_BG_CUBE] = cube

        self.spacetime.claim(cube)

        return cube.id

    def connect_path(self, proposal: Path) -> list[BgPipe]:
        source_cube = proposal.start
        target_cube = proposal.final
        # Representation of the path that will go into edge_realisations
        pipe_ids: list[BgPipe] = []

        # Add all the extra cubes and pipes of the path to the BlockGraph
        previous_cube: BgCube = source_cube

        for index in range(len(proposal.extra_cubes)):
            extra_cube = proposal.extra_cubes[index]
            extra_pipe_type = proposal.pipes_types[index]

            # Place the current cube and connect it to the previous cube.
            extra_cube_id = self.place_cube(extra_cube)
            self.connect_pipe(previous_cube, extra_cube, extra_pipe_type)

            # Extend the sequence of extra node ids
            pipe = BgPipe(source = previous_cube, target = extra_cube, type = extra_pipe_type)
            pipe_ids.append( pipe )

            # Prepare for the next iteration
            previous_cube = extra_cube

        # Make the final connection
        final_pipe_type = proposal.pipes_types[-1]
        self.connect_pipe(previous_cube, target_cube, final_pipe_type)

        pipe = BgPipe(source = previous_cube, target = target_cube, type = final_pipe_type)
        pipe_ids.append( pipe )

        return pipe_ids

    def connect_pipe(self, source: BgCube, target: BgCube, pipe_type : EdgeType):
        if not self.blockgraph.has_node(source.id):
            raise Exception(f"Cube {source} not found in the BG-graph.")

        if not self.blockgraph.has_node(target.id):
            raise Exception(f"Cube {target} not found in the BG-graph.")

        if self.blockgraph.has_edge(source.id, target.id):
            raise Exception(f"Cubes {source} and {target} are already connected by a pipe.")

        if not pipe_type in BlockGraphHelper.infer_pipe_type(source.kind, target.kind):
            raise Exception(f"Pipe type {pipe_type} is incompatible with source and target kinds [{source.kind}-{target.kind}].")

        # TODO: validate with respect to inferred pipe type between source and target cubes

        if source.position.get_manhattan_distance(target.position) != 1:
            raise Exception(f"Cubes {source} and {target} are not at adjacent positions.")

        self.blockgraph.add_edge(source.id, target.id)
        bg_pipe = BgPipe(source, target, pipe_type)
        self.blockgraph.edges[source.id, target.id][VolumetricZxGraph.KEY_BG_PIPE] = bg_pipe

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

        console.debug(f"Neigborhood visited to find alternative : {visited}")

        return False

    def is_path_valid(self, edge: ZxEdge, proposal: Path) -> bool:
        is_hadamard_path = False

        start = proposal.start
        final = proposal.final

        if not (self.is_realising_cube(edge.source, start) or self.is_realising_cube(edge.target, start)):
            raise Exception(f"Start cube {start} is not realising either endpoint of edge {edge} [proposal={proposal}].")

        if not (self.is_realising_cube(edge.source, final) or self.is_realising_cube(edge.target, final)):
            raise Exception(f"Final cube {final} is not realising either endpoint of edge {edge} [proposal={proposal}].")

        console.debug(f"Validating path proposal for {edge} : {proposal}.")

        previous: BgCube = start
        previous_reach = start.kind.get_reach()

        extra_positions = set()

        for index in range(len(proposal.extra_cubes)):
            current: BgCube = proposal.extra_cubes[index]
            current_reach = current.kind.get_reach()

            # Check that the cube type is either X or Z (Y and boundaries must be leaves)
            if current.kind in [ CubeKind.OOO, CubeKind.YYY ]:
                console.warning(f"> CubeKind.OOO and CubeKind.YYY can only appear at the ends of a path : {current}.")
                return False

            # Check that the current_position is available in spacetime
            if not self.spacetime.available(current.position):
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
            current_pipe_type = proposal.pipes_types[index]
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
        current_pipe_type = proposal.pipes_types[-1]
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
        for node in self.get_zx_nodes():
            extra = f", Cube#{node.realising_cube.id}" if node.realising_cube else ""
            print(f"Node #{node.id} : {node.type} [Q{node.qubit}, L{node.layer}{extra}]")

        for edge in self.get_zx_edges():
            print(f"Edge #{edge.source.id}-#{edge.target.id} : {edge}")

        for cube in self.get_bg_cubes():
            extra = f"[zx:{cube.realised_node}]" if cube.realised_node else ""
            print(f"Cube #{cube.id} : {cube.kind}@{cube.position} {extra}")

        for pipe in self.get_bg_pipes():
            print(f"Pipe {pipe}")

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