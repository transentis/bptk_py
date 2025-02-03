import unittest

from BPTK_Py.util.floating_point import precision_and_scale

class TestPrecisionAndScale(unittest.TestCase):
    def setUp(self):
        pass

    def testPrecisionAndScale(self):
        self.assertEqual(precision_and_scale(123456789.5678),(13, 4))
        self.assertEqual(precision_and_scale(1234567890.5678),(14, 4))
        self.assertEqual(precision_and_scale(12345678901.5678),(14, 3))
        self.assertEqual(precision_and_scale(123456789012.5678),(14, 2))
        self.assertEqual(precision_and_scale(1234567890123.5678),(14, 1))
        self.assertEqual(precision_and_scale(12345678901234.5678),(14, 0))
        self.assertEqual(precision_and_scale(123456789012345.5678),(15, 0))

        self.assertEqual(precision_and_scale(123),(3, 0))
        self.assertEqual(precision_and_scale(-1234),(4, 0))
        self.assertEqual(precision_and_scale(-12345.0),(5, 0))
        self.assertEqual(precision_and_scale(-123456.01),(8, 2))
        self.assertEqual(precision_and_scale(0),(1, 0))
        self.assertEqual(precision_and_scale(0.0),(1, 0))
        self.assertEqual(precision_and_scale(0.01),(3, 2))


if __name__ == '__main__':
    unittest.main()      