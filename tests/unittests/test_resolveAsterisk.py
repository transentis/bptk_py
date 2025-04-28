import unittest

from BPTK_Py.sdcompiler.plugins.resolveAsterisk import remove_nesting

class TestRemoveAserisk(unittest.TestCase):
    def setUp(self):
        pass

    def test_remove_nesting(self):
        self.assertEqual(remove_nesting([[["A"]]]), "A")
        self.assertEqual(remove_nesting((((("B",)),))), "B")
        self.assertEqual(remove_nesting(["C", "D"]), ["C", "D"])
        self.assertEqual(remove_nesting(("E", "F")), ("E", "F"))
        self.assertEqual(remove_nesting([]), [])
        self.assertEqual(remove_nesting(()), ())
        self.assertEqual(remove_nesting({"name": "test"}), [{"name": "test"}])
        self.assertEqual(remove_nesting(42), 42)
        self.assertEqual(remove_nesting("SimpleString"), "SimpleString")
        self.assertEqual(remove_nesting(3.14), 3.14)
        self.assertEqual(remove_nesting([{"key": "value"}]), [{"key": "value"}])  
        self.assertEqual(remove_nesting(({"key": "value"},)), [{"key": "value"}])

if __name__ == '__main__':
    unittest.main()    