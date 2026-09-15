import unittest

from BPTK_Py.sdcompiler.plugins.complexFunctions import remove_nesting, FindComplexFunctions


class TestRemoveNesting(unittest.TestCase):
    def test_unwraps_single_element_containers(self):
        """remove_nesting unwraps single-element lists/tuples and wraps dicts; scalars are
        returned unchanged."""
        self.assertEqual(remove_nesting([{"a": 1}]), [{"a": 1}])   # single-element list
        self.assertEqual(remove_nesting(({"a": 1},)), [{"a": 1}])  # single-element tuple
        self.assertEqual(remove_nesting(5), 5)                     # scalar -> unchanged
        self.assertEqual(remove_nesting("x"), "x")


class TestFindComplexFunctions(unittest.TestCase):
    def test_scalar_equation_parsed_is_wrapped_in_list(self):
        """FindComplexFunctions normalises a bare float/str equation_parsed into a list."""
        IR = {
            "dimensions": {},
            "models": {
                "m": {
                    "entities": {
                        "aux": [
                            {"name": "s", "equation_parsed": "somestr", "dimensions": []},
                            {"name": "f", "equation_parsed": 5.0, "dimensions": []},
                        ]
                    }
                }
            },
        }
        result = FindComplexFunctions(IR)
        entities = result["models"]["m"]["entities"]["aux"]
        self.assertEqual(entities[0]["equation_parsed"], ["somestr"])
        self.assertEqual(entities[1]["equation_parsed"], [5.0])


class TestCartesianProduct(unittest.TestCase):
    def test_one_combination_is_returned_as_itself(self):
        """One label per dimension gives a single tuple rather than a list of one."""
        from BPTK_Py.sdcompiler.plugins.complexFunctions import cartesian_product

        self.assertEqual(cartesian_product([["A"], ["X"]]), ("A", "X"))


if __name__ == '__main__':
    unittest.main()
