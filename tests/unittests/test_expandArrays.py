import unittest

from BPTK_Py.sdcompiler.plugins.expandArrays import cartesian_product, arrayed_identifiers, extract_labels, alter_identifier

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

    def test_extract_labels(self):
        dimensions = {
            0: ["A", "B", "C", "D", "E"],
            1: ["X", "Y", "Z"]
        }
        
        self.assertEqual(extract_labels({"type": "asterisk"}, dimensions, 0),['A', 'B', 'C', 'D', 'E'])
        #Probably not correct for "range"
        #1. rfind works for strings, not for lists
        #2. if "args" contains more than 2 entry, only the values between the first two are considered
        #self.assertEqual(extract_labels({"type": "range", "args": [{"name": "B"}, {"name": "D"}]}, dimensions, 0),['B', 'C', 'D'])  
        self.assertEqual(extract_labels({"type": "label", "name": "W"}, dimensions, 0),'W')
        self.assertEqual(extract_labels({"type": "identifier", "name": "W"}, dimensions, 0),{"type": "identifier", "name": "W"})

        self.assertRaises(Exception,extract_labels,{"type": "invalid", "name": "W"}, dimensions, 0)

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
        #probably not correct for lists
        #no return is defined -> None is returned
        #self.assertEqual(alter_identifier(IR=IR, entity=entity, expression=[1.0,"test"],model_name="model1"),[entity,entity])
        #probably not correct for lists
        #no return is defined -> None is returned        
        ##self.assertEqual(alter_identifier(IR=IR, entity=entity, expression=expression,model_name="model1"), )

if __name__ == '__main__':
    unittest.main()           