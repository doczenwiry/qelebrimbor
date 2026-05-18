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

import pyzx.graph.base

from qelebrimbor.analysis.cycles import CycleAnalyser
from qelebrimbor.formats.preprocessing.abstract import Preprocessor
from qelebrimbor.formats.pyzx import PYZX


class DefaultPreprocessor(Preprocessor):
    @staticmethod
    def process(input: pyzx.graph.base.BaseGraph) -> None:
        graph = PYZX.from_pyzx_graph(input)

        for cycle in CycleAnalyser.decompose(graph):
            # Go over the cycle and identify chains of fusable spiders.
            pass
