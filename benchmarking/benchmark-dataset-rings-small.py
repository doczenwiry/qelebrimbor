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

from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.formats.preprocessing.no_more_than_four_legs import NoMoreThanFourLegs
from qelebrimbor.formats.pyzx import PYZX

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print(f"Benchmarking dataset {benchmark.DATASET}")

    if not benchmark.dataset_detected():
        benchmark.generate_dataset()
    else:
        print(f"Existing dataset found in {benchmark.DATASET_DIRECTORY}.")

    dataset_filenames = benchmark.get_dataset_filenames()
    longest_file_name = max(map(len, dataset_filenames))

    for input_path in dataset_filenames:
        pyzx_input = PYZX.from_file(benchmark.DATASET_DIRECTORY + "/" + input_path)
        try:
            NoMoreThanFourLegs().process(pyzx_input)
        except KeyError as ke:
            print(f"> {input_path.ljust(longest_file_name, ' ')}")
            raise ke
        vzx = PYZX.from_pyzx_graph(pyzx_input)

        number_of_connected_components = nx.number_connected_components(cast(nx.Graph, vzx))
        if CycleAnalyser.has_cycles(vzx) and number_of_connected_components == 1:
            print(f"> {input_path.ljust(longest_file_name, ' ')} :", end=" ")

            try:
                result = subprocess.run(
                    [f"python ../qb.py -cs {benchmark.DATASET_DIRECTORY}/{input_path} 2> /dev/null"],
                    shell=True,
                    timeout=20,
                    capture_output=True,
                    text=True,
                )
                print(result.stdout, end="")
            except subprocess.TimeoutExpired:
                print("ABORTED RUN [longer than 20 seconds].")
                continue
