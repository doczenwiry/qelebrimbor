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
import subprocess
from typing import cast

import benchmark
import networkx as nx

from benchmarking.benchmark import Dataset, get_dataset_directory
from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.formats.preprocessing.full_reduce import FullReduce
from qelebrimbor.formats.pyzx import PYZX

logging.basicConfig(level=logging.INFO)

TIMEOUT = 10
if __name__ == "__main__":
    dataset = Dataset.SMALL
    hadamards = False
    print(f"Benchmarking dataset {dataset}")

    dataset_directory = get_dataset_directory(dataset, hadamards)
    if not benchmark.dataset_detected(dataset, hadamards):
        print(f"Generating dataset {dataset} in {dataset_directory}")
        benchmark.generate_dataset(dataset, hadamards)
    else:
        print(f"Existing dataset found in {dataset_directory}")

    dataset_filenames = benchmark.get_dataset_filenames(dataset)
    longest_file_name = max(map(len, dataset_filenames))

    for input_path in dataset_filenames:
        pyzx_input = PYZX.from_file(dataset_directory + "/" + input_path)
        try:
            FullReduce().process(pyzx_input)
        except KeyError as ke:
            print(f"> {input_path.ljust(longest_file_name, ' ')}")
            raise ke
        vzx = PYZX.from_pyzx_graph(pyzx_input)

        number_of_connected_components = nx.number_connected_components(cast(nx.Graph, vzx))
        if CycleAnalyser.has_cycles(vzx) and number_of_connected_components == 1:
            print(f"> {input_path.ljust(longest_file_name, ' ')} :", end=" ")

            try:
                result = subprocess.run(
                    [f"python ../qb.py -cs {dataset_directory}/{input_path} 2> /dev/null"],
                    shell=True,
                    timeout=TIMEOUT,
                    capture_output=True,
                    text=True,
                )
                print(result.stdout, end="")
            except subprocess.TimeoutExpired:
                print(f"ABORTED RUN [longer than {TIMEOUT} seconds].")
                continue
