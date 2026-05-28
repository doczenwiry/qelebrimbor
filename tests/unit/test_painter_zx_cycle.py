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
# logging.getLogger("qelebrimbor.spacetime.colorblind.painter_cycle").setLevel(logging.DEBUG)

# qelebrimbor.core.zx.attributes.ZX_COLORING = True


class TestPainterZxCycle(TestCase):
    def test_painter_one(self):
        cycle = ZxCycle.make(
            node_types=[NodeType.X for _ in range(4)], edge_types=[EdgeType.IDENTITY for _ in range(4)]
        )
        print(f"ZxCycle: {cycle}")

        colorless = ColorlessRing()
        for position in [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)]:
            colorless.append(Coordinates(*position))
        print(f"ColorlessRing: {colorless}")

        expected = "N0:XZZ@( 0, 0, 0) --I-- N1:XZZ@( 0, 1, 0) --I-- N2:XZZ@( 0, 1, 1)"
        expected += " --I-- N3:XZZ@( 0, 0, 1) --I-- N0:XZZ@( 0, 0, 0)"
        print(f"Expected Ring : {expected}")
        computed = str(PainterZxCycle.paint(colorless, cycle))
        print(f"Computed Ring : {computed}")

        self.assertEqual(computed, expected)

    def test_painter_two(self):
        cycle = ZxCycle.make(
            node_types=[NodeType.X if node_id % 2 == 0 else NodeType.Z for node_id in range(6)],
            edge_types=[EdgeType.IDENTITY for _ in range(6)],
        )
        print(f"ZxCycle: {cycle}")

        colorless = ColorlessRing()
        for position in [(0, 0, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (1, 0, 0)]:
            colorless.append(Coordinates(*position))
        print(f"ColorlessRing: {colorless}")

        expected = "N0:ZZX@( 0, 0, 0) --I-- N1:ZXX@( 0, 1, 0) --I-- N2:ZXZ@( 0, 1, 1) --I-- N3:XXZ@( 1, 1, 1)"
        expected += " --I-- N4:XZZ@( 1, 0, 1) --I-- N5:XZX@( 1, 0, 0) --I-- N0:ZZX@( 0, 0, 0)"
        print(f"Expected Ring : {expected}")
        computed = str(PainterZxCycle.paint(colorless, cycle))
        print(f"Computed Ring : {computed}")

        self.assertEqual(computed, expected)

    def test_painter_three(self):
        cycle = ZxCycle.make(
            node_types=[NodeType.Z for node_id in range(6)],
            edge_types=[EdgeType.HADAMARD for _ in range(6)],
        )
        print(f"ZxCycle: {cycle}")

        colorless = ColorlessRing()
        for position in [(0, 0, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 0, 1), (1, 0, 0)]:
            colorless.append(Coordinates(*position))
        print(f"ColorlessRing: {colorless.steps}")

        rings = PainterZxCycle.all_painted(colorless, cycle)

        stringed = sorted(list(map(str, rings)))

        for ring in stringed:
            print(f"> Painted Ring : {ring}")

        ring = rings[-1]
        expected = "N0:XXZ@( 0, 0, 0) --H-- N1:ZXX@( 0, 1, 0) --H-- N2:XZX@( 0, 1, 1) --H-- N3:XXZ@( 1, 1, 1)"
        expected += " --H-- N4:ZXX@( 1, 0, 1) --H-- N5:XZX@( 1, 0, 0) --H-- N0:XXZ@( 0, 0, 0)"
        print(f"Expected Ring : {expected}")
        computed = str(ring)
        print(f"Computed Ring : {computed}")

        self.assertEqual(computed, expected)
