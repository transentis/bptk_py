import unittest

from BPTK_Py.sdcompiler.plugins.expandArrays import cartesian_product, arrayed_identifiers, alter_identifier

class TestExpandArrays(unittest.TestCase):
    def setUp(self):
        pass

    def test_cartestian_procuct(self):
        self.assertEqual(cartesian_product([[0,1,2]]),[0,1,2])
        self.assertEqual(cartesian_product([[0,1],[1,2]]),[(0,1),(0,2),(1,1),(1,2)])
        self.assertEqual(cartesian_product([[0,1],[1,2],[2,3]]),[(0,1,2),(0,1,3),(0,2,2),(0,2,3),(1,1,2),(1,1,3),(1,2,2),(1,2,3)])        

    def test_arrayed_identifiers(self):
        self.assertEqual(arrayed_identifiers(expression=1.0,dimension=1,entity={},dimensions={}),1.0)
        self.assertEqual(arrayed_identifiers(expression="test",dimension=1,entity={},dimensions={}),"test")
        self.assertEqual(arrayed_identifiers(expression=1,dimension=1,entity={},dimensions={}),1)

        self.assertEqual(arrayed_identifiers(expression=[1.0,"test",1],dimension=1,entity={},dimensions={}),[1.0,"test",1])

        expression = {
            "type": "function",
            "name": "f",
            "args": [
                {"type": "identifier", "name": "x"},
                {"type": "identifier", "name": "y"},
                {"type": "identifier", "name": "z"},
                {"type": "identifier", "name": "w"}
            ]
        }
        dimension=2
        entity = {"dimensions": [1, 2]}
        dimensions = {
            1: {"variables": [{"name": "x"}, {"name": "y"}]},
            2: {"variables": [{"name": "y"}, {"name": "z"}]}
        }

        self.assertEqual(arrayed_identifiers(expression=expression,dimension=dimension,entity=entity,dimensions=dimensions),{'type': 'function', 'name': 'f', 'args': [{'type': 'identifier', 'name': 'x'}, {'type': 'identifier', 'name': 'y[2]'}, {'type': 'identifier', 'name': 'z'}, {'type': 'identifier', 'name': 'w'}]})

    def test_alter_identifier(self):
        IR = {
            "dimensions": {
                "dimension1": {
                    "variables": [
                        {"model": "model1", "name": "name1"},
                        {"model": "model1", "name": "name2"}
                    ]
                },
                "dimension2": {
                    "variables": [
                        {"model": "model1", "name": "name1"},
                        {"model": "model2", "name": "name3"}
                    ]
                }
            }
        }
        entity = {
            "dimensions": ["dimension1", "dimension2"],
            "labels": ["label1", "label2"]
        }
        expression = {
            "type": "identifier",
            "name": "name1"
        }

        self.assertEqual(alter_identifier(IR=IR, entity=entity, expression=1.0,model_name="model1"),entity)
        self.assertEqual(alter_identifier(IR=IR, entity=entity, expression="test",model_name="model1"),entity)

    def test_alter_identifier_rewrites_a_dimension_variable_in_place(self):
        """An identifier naming a dimension variable becomes an array reference.

        The function returns nothing for this case - it mutates the expression it was
        handed - and it collects one label per dimension the name appears in, in the
        order of the entity's own dimensions.
        """
        IR, entity, expression = self._alter_identifier_fixture()

        self.assertIsNone(alter_identifier(IR=IR, entity=entity, expression=expression,
                                           model_name="model1"))
        self.assertEqual(expression["type"], "array")
        self.assertEqual(expression["name"], "name1")
        self.assertEqual([arg["name"] for arg in expression["args"]], ["label1", "label2"])

    def test_alter_identifier_walks_a_list_and_returns_nothing(self):
        """A list of expressions is walked for its side effect, not for a result."""
        IR, entity, expression = self._alter_identifier_fixture()
        other = {"type": "identifier", "name": "name2"}

        self.assertIsNone(alter_identifier(IR=IR, entity=entity,
                                           expression=[expression, other],
                                           model_name="model1"))
        # The first name sits in both dimensions, the second only in the first.
        self.assertEqual([arg["name"] for arg in expression["args"]], ["label1", "label2"])
        self.assertEqual([arg["name"] for arg in other["args"]], ["label1"])

    @staticmethod
    def _alter_identifier_fixture():
        IR = {
            "dimensions": {
                "dimension1": {
                    "variables": [
                        {"model": "model1", "name": "name1"},
                        {"model": "model1", "name": "name2"}
                    ]
                },
                "dimension2": {
                    "variables": [
                        {"model": "model1", "name": "name1"},
                        {"model": "model2", "name": "name3"}
                    ]
                }
            }
        }
        entity = {
            "dimensions": ["dimension1", "dimension2"],
            "labels": ["label1", "label2"]
        }
        return IR, entity, {"type": "identifier", "name": "name1"}

    def test_cartesian_product_of_one_combination_returns_that_combination(self):
        """One label per dimension yields a single tuple, which is unwrapped.

        The two-or-more case returns a list of tuples; this one returns the tuple
        itself, and the caller relies on that to index a single cell.
        """
        self.assertEqual(cartesian_product([["A"], ["X"]]), ("A", "X"))
        self.assertEqual(cartesian_product([["A"], ["X"], ["1"]]), ("A", "X", "1"))


if __name__ == '__main__':
    unittest.main()           