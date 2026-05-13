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
from unittest import TestCase

from qelebrimbor.core.colorless.ring import ColorlessRing
from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.zx.attributes import EdgeType, NodeType
from qelebrimbor.core.zx.cycle import ZxCycle
from qelebrimbor.spacetime.colorblind.painter_cycle import PainterZxCycle

logging.basicConfig(level=logging.INFO)


class TestPainterZxCycle(TestCase):
    def test_painter_one(self):
        cycle = ZxCycle.make(
            node_types=[NodeType.X for _ in range(4)], edge_types=[EdgeType.IDENTITY for _ in range(4)]
        )
        colorless = ColorlessRing()
        for position in [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)]:
            colorless.append(Coordinates(*position))
        print(f"ColorlessRing: {colorless}")
        print(f"ZxCycle: {cycle}")

        print(f"Painted Ring : {PainterZxCycle.paint(colorless, cycle)}")
