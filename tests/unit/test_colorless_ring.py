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
from qelebrimbor.helpers.spacetime import SpacetimeHelper, Step

logging.getLogger("qelebrimbor.core.colorless.ring").setLevel(logging.DEBUG)


class TestColorlessRing(TestCase):
    def test_ring(self):
        colorless = ColorlessRing().extend(Coordinates(0, 0, 0))
        print(f"Ring : {colorless}")
        self.assertEqual(str(colorless), "( 0, 0, 0) -- [OPEN]")

    def test_append(self):
        current = Coordinates(0, 0, 0)
        colorless = ColorlessRing().extend(current)
        for step in [SpacetimeHelper.YP, SpacetimeHelper.ZP, SpacetimeHelper.YM]:
            current += step
            colorless.append(current)
        print(f"Ring : {colorless}")
        self.assertEqual(
            str(colorless),
            "( 0, 0, 0) -- ( 0, 1, 0) -- ( 0, 1, 1) -- ( 0, 0, 1) -- ( 0, 0, 0)",
        )

    def test_extend(self):
        current = Coordinates(0, 0, 0)
        colorless = ColorlessRing().extend(current)
        extended = colorless.extend(SpacetimeHelper.YP)

        self.assertEqual(str(colorless), "( 0, 0, 0) -- [OPEN]")
        self.assertEqual(str(extended), "( 0, 0, 0) -- ( 0, 1, 0) -- [OPEN]")

    def test_moves(self):
        current = Coordinates(0, 0, 0)
        colorless = ColorlessRing().extend(current)
        for step in [Step.YP, Step.XP, Step.YM, Step.YM, Step.XM]:
            current += step.value
            colorless.append(current)
        print(f"Ring : {colorless}")
        print(f"Moves: {colorless.moves}")
