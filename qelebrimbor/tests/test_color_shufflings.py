import unittest
from itertools import product

from qelebrimbor.pathfinders.metric.color_shufflings import ColorShuffling

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