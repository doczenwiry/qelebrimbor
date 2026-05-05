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

from collections import defaultdict

import benchmark

from qelebrimbor.formats.pyzx import PYZX
from qelebrimbor.utilities.cycle_analyser import CycleAnalyser

import logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print(f"Benchmarking dataset {benchmark.DATASET}")

    if not benchmark.dataset_detected():
        print(f"Generating dataset into {benchmark.DATASET_DIRECTORY}")
        benchmark.generate_dataset()
    else:
        print(f"Detected dataset in {benchmark.DATASET_DIRECTORY}.")

    dataset_filepaths = benchmark.get_dataset_filepaths()
    longest_file_name = max(map(len, dataset_filepaths))

    for input_path in dataset_filepaths:
        vzx = PYZX.from_file(input_path)
        cycles = CycleAnalyser.decompose_nodes(vzx, minimal = True)
        result: dict[int, int] = defaultdict(int)
        for cycle in cycles:
            result[len(cycle)] += 1
        print(f"Cycle analysis {input_path.ljust(longest_file_name, ' ')} : {list(result.items())}")