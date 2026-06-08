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

import matplotlib.pyplot as plt
import pandas
import seaborn

logging.basicConfig(level=logging.INFO)
# Silence matplotlib INFO reporting
logging.getLogger("matplotlib").setLevel(logging.WARNING)

parser = ArgumentParser(
    prog="qb",
    description="A tool to construct a Volumetric ZX-graph (a.k.a. BlockGraph) from an input ZX-graph. Currently accepted files are *.json containing a PyZX graph in JSON format.",  # noqa: E501
)
parser.add_argument("filepath", help="path to the file containing the results of a benchmark run to display.")

if __name__ == "__main__":
    arguments = parser.parse_args()

    data = pandas.read_csv(arguments.filepath)
    data.info()

    available = data[data["status"] == "COMPLETE"]

    seaborn.boxplot(data=available, x=available["layers"].astype(str), y="iir")
    plt.title("Internal Inflation Rate [4 qubits]")
    plt.ylabel("Inflation (+%)")
    plt.show()

    seaborn.boxplot(data=available, x=available["layers"].astype(str), y="run")
    plt.title("Runtime [4 qubits]")
    plt.ylabel("Time (s)")
    plt.show()
