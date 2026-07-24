import unittest

from BPTK_Py.sdcompiler.plugins.replaceDimensionNames import resolve


class TestReplaceDimensionNames(unittest.TestCase):
    def setUp(self):
        self.dimensions = {"countries": {"labels": ["germany", "france"]}}

    def test_dimension_dot_label_becomes_a_label(self):
        """A `<dimension>.<label>` reference is rewritten into a bare label node."""
        result = resolve({"name": "countries.germany", "type": "identifier"},
                         entity={}, dimensions=self.dimensions)
        self.assertEqual(result, {"name": "germany", "type": "label"})

    def test_size_of_dimension_resolves_to_label_count(self):
        """SIZE(<dimension>) is replaced by the number of labels in that dimension."""
        result = resolve(
            {"name": "size", "type": "call",
             "args": [{"name": "countries", "type": "identifier"}]},
            entity={}, dimensions=self.dimensions)
        self.assertEqual(result, 2)


if __name__ == '__main__':
    unittest.main()
