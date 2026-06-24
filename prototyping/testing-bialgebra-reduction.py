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

import pyzx

from qelebrimbor.formats.preprocessing.bialgebra_reduction import BialgebraReduction
from qelebrimbor.formats.pyzx import PYZX

if __name__ == "__main__":
    # filename = "../assets/pyzx/steane/steane-code-qubits7.json"
    filename = "../benchmarking/datasets/small/identity/random-cnots-q4-d32-s2870846309.pyzx.json"
    with open(filename, "r") as file:
        graph = pyzx.Graph().from_json(file.read())
        pyzx.draw(graph, labels=True)
        pyzx.full_reduce(graph)
        pyzx.to_rg(graph)
        graph.pack_circuit_rows()
        pyzx.draw(graph, labels=True)
        PYZX.into_file(graph, "../prototyping/reduced.json")

        # > zs: [4, 46], xs: [13, 27]
        # > zs: [54, 81], xs: [19, 63]

        output = BialgebraReduction.process(graph)
        PYZX.into_file(output, "../prototyping/output.json")
        pyzx.draw(output, labels=True)
