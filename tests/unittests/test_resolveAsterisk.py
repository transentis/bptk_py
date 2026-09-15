import unittest

from BPTK_Py.sdcompiler.plugins.resolveAsterisk import remove_nesting, resolve

class TestRemoveAserisk(unittest.TestCase):
    def setUp(self):
        self.IR = {
            "dimensions": {
                "Region": {"labels": ["EU", "US"]},
                "Product": {"labels": ["Car", "Bike"]}
            },
            "models": {
                "SalesModel": {
                    "entities": {
                        "dataset": [
                            {"name": "SalesData", "dimensions": ["Region", "Product"]}
                        ]
                    }
                }
            }
        }
        
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

    def test_resolve(self):
        self.assertEqual(resolve("simple_string", "SalesData", self.IR), "simple_string")
        self.assertEqual(resolve(3.1415, "SalesData", self.IR), 3.1415)
        self.assertEqual(resolve(["a", "b", "c"], "SalesData", self.IR), ["a", "b", "c"])
        self.assertEqual(resolve({"name": "X", "type": "identifier"}, "SalesData", self.IR), {"name": "X", "type": "identifier"})
        
        expr = {
            "name": "+",
            "type": "operator",
            "args": [
                {"name": "A", "type": "identifier"},
                {"name": "B", "type": "identifier"}
            ]
        }
        self.assertEqual(resolve(expr, "SalesData", self.IR), expr)
        
        expr = {
            "name": "SalesData",
            "type": "array",
            "args": ["*", "*"]
        }
        result = resolve(expr, "SalesData", self.IR)
        expected = [
            {
                "name": "SalesData",
                "type": "array",
                "args": [
                    {"name": "EU", "type": "label"},
                    {"name": "Car", "type": "label"}
                ]
            },
            {
                "name": "SalesData",
                "type": "array",
                "args": [
                    {"name": "EU", "type": "label"},
                    {"name": "Bike", "type": "label"}
                ]
            },
            {
                "name": "SalesData",
                "type": "array",
                "args": [
                    {"name": "US", "type": "label"},
                    {"name": "Car", "type": "label"}
                ]
            },
            {
                "name": "SalesData",
                "type": "array",
                "args": [
                    {"name": "US", "type": "label"},
                    {"name": "Bike", "type": "label"}
                ]
            }
        ]
        self.assertEqual(result, expected)

    def test_an_asterisk_beside_a_fixed_label(self):
        """`SalesData[*, Car]` spreads one dimension and keeps the other."""
        expression = {"name": "SalesData", "type": "array",
                      "args": ["*", [{"name": "Car", "type": "label"}]]}

        result = resolve(expression, "SalesData", self.IR)

        self.assertEqual([[arg["name"] for arg in ref["args"]] for ref in result],
                         [["EU", "Car"], ["US", "Car"]])

    def test_a_fixed_label_beside_an_asterisk(self):
        """`SalesData[EU, *]`, the same the other way round."""
        expression = {"name": "SalesData", "type": "array",
                      "args": [[{"name": "EU", "type": "label"}], "*"]}

        result = resolve(expression, "SalesData", self.IR)

        self.assertEqual([[arg["name"] for arg in ref["args"]] for ref in result],
                         [["EU", "Car"], ["EU", "Bike"]])

    def test_two_fixed_labels_are_left_alone(self):
        """With no asterisk there is nothing to spread, so the reference stays one."""
        expression = {"name": "SalesData", "type": "array",
                      "args": [[{"name": "EU", "type": "label"}],
                               [{"name": "Car", "type": "label"}]]}

        result = resolve(expression, "SalesData", self.IR)

        self.assertEqual(result["type"], "array")
        # Each index keeps the one-element list the parser produced; only the asterisk
        # path rebuilds the reference.
        self.assertEqual(result["args"], [[{"name": "EU", "type": "label"}],
                                          [{"name": "Car", "type": "label"}]])

    def test_an_expression_that_is_neither_a_dict_nor_a_list_comes_back_unchanged(self):
        self.assertEqual(resolve(7, "SalesData", self.IR), 7)


if __name__ == '__main__':
    unittest.main()    