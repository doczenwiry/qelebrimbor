import unittest
from itertools import product, repeat

from qelebrimbor.pathfinders.metric.color_shufflings import ColorShuffling
from qelebrimbor.pathfinders.metric.path_weight import PathWeight

class TestPathWeights(unittest.TestCase):
    def test_identity(self):
        identity = PathWeight()
        elements = [ PathWeight(shuffle, 1) for shuffle in ColorShuffling.generate() ]
        for elt in elements:
            self.assertEqual(elt, elt * identity)
            self.assertEqual(elt, identity * elt)

    def test_associativity(self):
        elements = [ PathWeight(shuffle, 1) for shuffle in ColorShuffling.generate() ]
        for elt1, elt2, elt3 in product(elements, repeat = 3):
            associative_l = (elt1 * elt2) * elt3
            associative_r = elt1 * (elt2 * elt3)
            self.assertEqual(associative_l, associative_r, msg = f"({elt1} * {elt2}) * {elt3} != {elt1} * ({elt2} * {elt3}) / {elt1 * elt2}")