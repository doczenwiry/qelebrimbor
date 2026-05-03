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

import unittest
from itertools import product

from qelebrimbor.helpers.spacetime import SpacetimeHelper
from qelebrimbor.spacetime.pathfinders.metric.color_shufflings import ColorShuffling

class TestColorShuffling(unittest.TestCase):
    def test_identity(self):
        identity = ColorShuffling('xyz')
        for elt in ColorShuffling.generate():
            self.assertEqual(elt, elt.extend(identity))
            self.assertEqual(elt, identity.extend(elt))

    def test_associativity(self):
        elements = ColorShuffling.generate()
        for elt1, elt2, elt3 in product(elements, repeat = 3):
            associative_l = elt1.extend(elt2).extend(elt3)
            associative_r = elt1.extend(elt2.extend(elt3))
            self.assertEqual(associative_l, associative_r, msg = f"({elt1} * {elt2}) * {elt3} != {elt1} * ({elt2} * {elt3}) / {elt1.extend(elt2)}")

    def test_other(self):
        step1 = ColorShuffling(ColorShuffling.convert(SpacetimeHelper.YP))
        step2 = ColorShuffling(ColorShuffling.convert(SpacetimeHelper.ZP))
        step3 = ColorShuffling(ColorShuffling.convert(SpacetimeHelper.XP))

        all = ColorShuffling.generate()
        print(f"Generated [{len(all)}]")
        for cs in all:
            print(f"> {cs}")

        print(f"Step 1 : {step1}")
        print(f"Step 2 : {step2}")
        print(f"Step 3 : {step3}")
        print(f"Step1-Step2  : {step1.extend(step2)}")
        print(f"Overall path : {step1.extend(step2).extend(step3)}")
