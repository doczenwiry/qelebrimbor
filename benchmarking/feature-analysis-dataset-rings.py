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
from argparse import ArgumentParser
from typing import cast

import networkx as nx
from benchmark import Benchmark, Dataset

from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.formats.preprocessing.bialgebra_reduction import BialgebraReduction
from qelebrimbor.formats.preprocessing.full_reduction import FullReduction
from qelebrimbor.formats.pyzx import PYZX

logging.basicConfig(level=logging.INFO)

parser = ArgumentParser(
    prog="feature-analysis-dataset-rings",
    description="A tool to analyse the features of a fixed dataset of randomly generated ZX-graphs.",
)
parser.add_argument(
    "-r",
    "--robust",
    action="store_true",
    help="analyse the robust version of the dataset.",
)

if __name__ == "__main__":
    arguments = parser.parse_args()

    dataset = Dataset.SMALL
    benchmark = Benchmark(dataset, robust=arguments.robust)
    print(f"Analysing features of dataset {dataset}")

    if not benchmark.dataset_detected():
        print(f"Generating dataset into {benchmark.directory}")
        benchmark.generate_dataset()
    else:
        print(f"Detected dataset in {benchmark.directory}.")

    longest_file_name = max(map(len, benchmark.filenames))

    for input_path in benchmark.filenames:
        try:
            pyzx_internal = PYZX.from_file(benchmark.directory + "/" + input_path)
            pyzx_internal = FullReduction.process(pyzx_internal)
            pyzx_internal = BialgebraReduction.process(pyzx_internal)
            vzx = PYZX.from_pyzx_graph(pyzx_internal)
        except KeyError as ke:
            print(f"> {input_path.ljust(longest_file_name, ' ')}")
            raise ke

        if CycleAnalyser.has_cycles(vzx):
            largest_cycle = str(len(max(CycleAnalyser.decompose(vzx, minimal=True), key=lambda c: c.length)))
        else:
            largest_cycle = "n/a"

        nxg = cast(nx.Graph, vzx)
        cyclomatic = nxg.number_of_edges() - nxg.number_of_nodes() + nx.number_connected_components(nxg)
        planar, _ = nx.check_planarity(nxg)
        details = f"CN:{cyclomatic}, LC:{largest_cycle}, PL:{planar}"
        print(f"Analysis of {input_path.ljust(longest_file_name, ' ')} : {details}")
