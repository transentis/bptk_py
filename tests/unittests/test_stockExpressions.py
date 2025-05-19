import unittest

from BPTK_Py.sdcompiler.plugins.stockExpressions import DimJoinedExpression, JoinedExpression

class TestStockExpressions(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_DimJoinedExpression(self):
        with self.assertRaises(TypeError):
            DimJoinedExpression(["A"], 123, "2")

        self.assertEqual(DimJoinedExpression("A", "+", "2"), {"name": "", "type": "nothing"})

        self.assertEqual(DimJoinedExpression([], "+", "2"), {"name": "", "type": "nothing"})

        self.assertEqual(DimJoinedExpression(["A"], "+", "2"), {"name": "A[2]", "type": "identifier"})

        expected = {
            "name": "-",
            "type": "operator",
            "args": [
                {"name": "A[2]", "type": "identifier"},
                {"name": "B[2]", "type": "identifier"}
            ]
        }
        self.assertEqual(DimJoinedExpression(["A", "B"], "-", "2"), expected)

        expected = {
            "name": "*",
            "type": "operator",
            "args": [
                {"name": "A[3]", "type": "identifier"},
                {
                    "name": "*",
                    "type": "operator",
                    "args": [
                        {"name": "B[3]", "type": "identifier"},
                        {"name": "C[3]", "type": "identifier"}
                    ]
                }
            ]
        }
        self.assertEqual(DimJoinedExpression(["A", "B", "C"], "*", "3"), expected)

        expected = {
            "name": "-",
            "type": "operator",
            "args": [
                {"name": "A[4]", "type": "identifier"},
                {
                    "name": "-",
                    "type": "operator",
                    "args": [
                        {"name": "B[4]", "type": "identifier"},
                        {
                            "name": "-",
                            "type": "operator",
                            "args": [
                                {"name": "C[4]", "type": "identifier"},
                                {"name": "D[4]", "type": "identifier"}
                            ]
                        }
                    ]
                }
            ]
        }
        self.assertEqual(DimJoinedExpression(["A", "B", "C", "D"], "-", "4"), expected)

    def test_JoinedExpression(self):
        with self.assertRaises(TypeError):
            JoinedExpression(["A"], 123)        

        self.assertEqual(JoinedExpression("A", "+"), {"name": "", "type": "nothing"})

        self.assertEqual(JoinedExpression([], "+"), {"name": "", "type": "nothing"})

        self.assertEqual(JoinedExpression(["A"], "+"), {"name": "A", "type": "identifier"})

        expected = {
            "name": "-",
            "type": "operator",
            "args": [
                {"name": "A", "type": "identifier"},
                {"name": "B", "type": "identifier"}
            ]
        }
        self.assertEqual(JoinedExpression(["A", "B"], "-"), expected)

        expected = {
            "name": "*",
            "type": "operator",
            "args": [
                {"name": "A", "type": "identifier"},
                {
                    "name": "*",
                    "type": "operator",
                    "args": [
                        {"name": "B", "type": "identifier"},
                        {"name": "C", "type": "identifier"}
                    ]
                }
            ]
        }
        self.assertEqual(JoinedExpression(["A", "B", "C"], "*"), expected)

        expected = {
            "name": "-",
            "type": "operator",
            "args": [
                {"name": "A", "type": "identifier"},
                {
                    "name": "-",
                    "type": "operator",
                    "args": [
                        {"name": "B", "type": "identifier"},
                        {
                            "name": "-",
                            "type": "operator",
                            "args": [
                                {"name": "C", "type": "identifier"},
                                {"name": "D", "type": "identifier"}
                            ]
                        }
                    ]
                }
            ]
        }
        self.assertEqual(JoinedExpression(["A", "B", "C", "D"], "-"), expected)


if __name__ == '__main__':
    unittest.main()    