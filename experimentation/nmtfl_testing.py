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
import random

import pyzx as zx

from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.formats.pyzx import PYZX
from qelebrimbor.vedo.vzx_viewer import VolumetricZxGraphViewer

SEED = 42
QUBITS = 4
LAYERS = 10

logging.basicConfig(level=logging.INFO)
random.seed(SEED)

if __name__ == "__main__":
    pyzx_input = zx.generate.cnots(qubits=QUBITS, depth=LAYERS)
    zx.draw(pyzx_input, labels=True)
    zx.full_reduce(pyzx_input)
    vzx = PYZX.from_pyzx_graph(pyzx_input)

    CycleAnalyser.analyse(vzx)

    viewer = VolumetricZxGraphViewer(vzx, label=f"random-s{SEED}-q{QUBITS}-d{LAYERS}")
    viewer.display()
