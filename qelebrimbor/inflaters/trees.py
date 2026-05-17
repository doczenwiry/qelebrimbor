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

import logging

from qelebrimbor.core.bg.attributes import CubeId
from qelebrimbor.core.bg.path import Path
from qelebrimbor.core.components import BgCube, ZxNode
from qelebrimbor.core.volumetric_zx_graph import VolumetricZxGraph
from qelebrimbor.core.zx.tree import ZxTree
from qelebrimbor.helpers.blockgraph import BlockGraphHelper
from qelebrimbor.spacetime.connectivity.open_ports import OpenPortsTracker
from qelebrimbor.spacetime.placefinders.breadth_first_search import PlacefinderBFS

console = logging.getLogger(__name__)


class ZxGraphInflaterTrees:
    def __init__(self, graph: VolumetricZxGraph, iterative: bool = False):
        self.__graph = graph
        self.__connectivity = OpenPortsTracker(graph)
        self.__placefinder = PlacefinderBFS(graph, self.__connectivity)
        self.__iterative_processing = iterative

    def process(self, abort_on_failure: bool = False, abort_on_index: int = -1):
        roots: set[ZxNode] = set()
        for node in self.__graph.get_zx_nodes():
            if node.is_realised():
                if any(not neighbor.is_realised() for neighbor in self.__graph.get_zx_neighbors(node)):
                    roots.add(node)
        console.debug(f">> Roots identified : {roots}")
        trees: list[ZxTree] = list(map(lambda rt: ZxTree.extract(self.__graph, rt), roots))
        maximal_height: int = max(tree.height for tree in trees)

        print(f">> Trees identified : {len(trees)}")
        for tree in trees:
            print(f">>> Tree [h={tree.height}] : {tree}")

        processed = 0
        for level in range(maximal_height):
            self.__attempt_levels_realisation(trees, level)
            # break

        print(f">> Trees realised : {processed}/{len(trees)}")

    def __attempt_levels_realisation(self, trees: list[ZxTree], level: int) -> bool:
        print(f">> Attempting realisation of level [L={level}]")
        for tree in trees:
            current: ZxNode
            for current in tree.level(level):
                # console.debug(f">> Current : {current}")
                if not current.is_realised():
                    # Realise node based on preceding node's color and edge type to infer its CubeKind.
                    preceding_node = tree.preceding(current)
                    # console.debug(f">>> Preceding : {preceding_node}")
                    if not preceding_node.is_realised():
                        continue

                    if self.__graph.get_zx_degree(preceding_node.id) > 4:
                        continue

                    preceding_cube = preceding_node.realising_cube
                    ports = self.__graph.spacetime.available_ports(preceding_cube.position, preceding_cube.kind.reach)
                    edge = self.__graph.get_zx_edge(preceding_node.id, current.id)
                    try:
                        port = next(ports)
                        cube = BgCube(
                            kind=BlockGraphHelper.infer_cube_kind(preceding_cube, port, edge.type, current.type),
                            position=port,
                        )
                        cube_id: CubeId = self.__graph.realise_zx_node(current, cube=cube)
                        realising_cube = self.__graph.get_bg_cube(cube_id)
                        self.__graph.realise_zx_edge(
                            source=preceding_node.id,
                            target=current.id,
                            proposal=Path(start=preceding_cube).extend(cube=realising_cube, pipe_type=edge.type),
                        )
                    except StopIteration:
                        raise Exception(f"Realising cube of {preceding_node} has no ports available [si].")
                    pass

                current_degree = self.__graph.get_zx_degree(current.id)
                if current_degree > 4:
                    # Unfuse the realising cube into enough cubes to accommodate all the legs of the node.
                    excess_required = (current_degree - 4 + (current_degree % 2)) // 2
                    console.debug(f">>> Has degree {self.__graph.get_zx_degree(current.id)}")
                    console.debug(f">>> Need to be unfused into {excess_required + 1} cube(s).")
                    pass

        return True
