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

from qelebrimbor.core.reach import Reach
from qelebrimbor.helpers.spacetime import Step


class TestColorlessRing(unittest.TestCase):
    def test_reach_x_y_xy(self):
        self.assertEqual(Reach.from_steps(Step.XP, Step.YP), {Reach.XY})

    def test_reach_xp_ym_xy(self):
        self.assertEqual(Reach.from_steps(Step.XP, Step.YM), {Reach.XY})

    def test_reach_x_z_xz(self):
        self.assertEqual(Reach.from_steps(Step.XP, Step.ZP), {Reach.XZ})

    def test_reach_z_x_xz(self):
        self.assertEqual(Reach.from_steps(Step.ZP, Step.XP), {Reach.XZ})

    def test_reach_x_x_nyz(self):
        self.assertEqual(Reach.from_steps(Step.XP, Step.XP), {Reach.XY, Reach.XZ})

    def test_reach_z_z_nxy(self):
        self.assertEqual(Reach.from_steps(Step.ZP, Step.ZM), {Reach.XZ, Reach.YZ})