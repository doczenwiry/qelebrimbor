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
    description="A tool to plot the results of benchmark runs.",  # noqa: E501
)
parser.add_argument("filepaths", nargs="+", help="path to the file containing results of a benchmark run to display.")

if __name__ == "__main__":
    arguments = parser.parse_args()

    dataframes: list[pandas.DataFrame] = list()
    for filepath in arguments.filepaths:
        components = filepath.split(".")[0].split("-")
        size, commit = components[3], components[4]
        comment = "-" + components[5] if len(components) == 6 else ""
        df = pandas.read_csv(filepath)
        df["source"] = size + "-" + commit[:8] + comment
        df.info()
        dataframes.append(df)

    data = pandas.concat(dataframes, ignore_index=True)

    available = data[data.groupby(["qubits", "layers", "seed"])["status"].transform(lambda s: (s == "COMPLETE").all())]
    available = available[
        available.groupby(["qubits", "layers", "seed"])["status"].transform("count") == len(arguments.filepaths)
    ]

    available.info()

    seaborn.set_theme(rc={"figure.constrained_layout.use": True})

    plot1 = seaborn.boxplot(data=available, x=available["layers"].astype(str), y="iir", hue="source")
    seaborn.move_legend(plot1, "upper left", bbox_to_anchor=(1, 1))
    plt.title("Internal Inflation Rate [4 qubits]")
    plt.ylabel("Inflation (+%)")
    plt.show()

    plot2 = seaborn.boxplot(data=available, x=available["layers"].astype(str), y="run", hue="source")
    seaborn.move_legend(plot2, "upper left", bbox_to_anchor=(1, 1))
    plt.title("Runtime [4 qubits]")
    plt.ylabel("Time (s)")
    plt.show()
