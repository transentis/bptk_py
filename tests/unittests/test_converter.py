import unittest

from BPTK_Py import Model
from BPTK_Py.sddsl.converter import Converter

class TestConverter(unittest.TestCase):
    def setUp(self):
        pass

    def testConverter_add_arr_empty(self):
        model = Model()
        converter = Converter(model=model,name="testConverter") 

        return_value = str(converter.add_arr_empty(name="testNameConverter"))
        expected_value = str(converter.model.converter(converter.name + "[" + "testNameConverter" + "]"))

        self.assertEqual(return_value,expected_value)

if __name__ == '__main__':
    unittest.main()    