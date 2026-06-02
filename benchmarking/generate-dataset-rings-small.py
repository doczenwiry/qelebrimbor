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

import benchmarking.benchmark as benchmark

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
