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

from itertools import product
from unittest import TestCase

from qelebrimbor.core.metric.path_weight import PathWeight


class TestPathWeights(TestCase):
    def test_identity(self):
        identity = PathWeight()
        elements = PathWeight.generate(max_distance=2, include_identity=True)
        for elt in elements:
            self.assertEqual(elt, elt.extend(identity))
            self.assertEqual(elt, identity.extend(elt))

    def test_associativity(self):
        elements = PathWeight.generate(max_distance=2, include_identity=True)
        for elt1, elt2, elt3 in product(elements, repeat=3):
            associative_l = (elt1.extend(elt2)).extend(elt3)
            associative_r = elt1.extend(elt2.extend(elt3))
            self.assertEqual(
                associative_l,
                associative_r,
                msg=f"({elt1} * {elt2}) * {elt3} != {elt1} * ({elt2} * {elt3}) / {elt1.extend(elt2)}",
            )
