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
import sys
from typing import cast

import benchmark
import networkx as nx

from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.formats.preprocessing.full_reduce import FullReduce
from qelebrimbor.formats.pyzx import PYZX

logging.basicConfig(level=logging.INFO)

TIMEOUT = 10
if __name__ == "__main__":
    dataset = benchmark.Dataset.SMALL
    hadamards = False
    print(f"Benchmarking dataset {dataset}")

    dataset_directory = benchmark.get_dataset_directory(dataset, hadamards)
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
            print(f"> {input_path.ljust(longest_file_name, ' ')} :", end=" ", flush=True)

            try:
                result = subprocess.run(
                    [sys.executable, "-m", "qb", "-cs", f"{dataset_directory}/{input_path}"],
                    timeout=TIMEOUT,
                    text=True,
                )

            except KeyboardInterrupt:
                print("Benchmarking interrupted by user.")
                break

            except subprocess.CalledProcessError as e:
                # This catches the crash and prevents the main script from stopping
                print(f"FAILURE (exit:{e.returncode})")

            except subprocess.TimeoutExpired:
                print(f"ABORTED RUN [longer than {TIMEOUT} seconds].")
                continue
