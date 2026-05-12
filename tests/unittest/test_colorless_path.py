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

from qelebrimbor.core.coordinates import Coordinates
from qelebrimbor.core.colorless.path import ColorlessPath
from qelebrimbor.helpers.spacetime import SpacetimeHelper


class TestColorlessPath(unittest.TestCase):
    def test_path(self):
        colorless = ColorlessPath(start = Coordinates(0,0,0))
        print(f"Path : {colorless}")
        self.assertEqual(str(colorless), "( 0, 0, 0)")

    def test_append(self):
        colorless = ColorlessPath(start = Coordinates(0,0,0))
        colorless.append(SpacetimeHelper.YP)
        self.assertEqual(str(colorless), "( 0, 0, 0) -> ( 0, 1, 0)")

    def test_extend(self):
        colorless = ColorlessPath(start = Coordinates(0,0,0))
        extended = colorless.extend(SpacetimeHelper.YP)
        self.assertEqual(str(colorless), "( 0, 0, 0)")
        self.assertEqual(str(extended), "( 0, 0, 0) -> ( 0, 1, 0)")