import unittest

from BPTK_Py import Model
from BPTK_Py.sddsl.element import ElementError
from BPTK_Py.sddsl.constant import Constant

class TestConstant(unittest.TestCase):
    def setUp(self):
        pass

    def testConstant_add_arr_empty(self):
        model = Model()
        constant = Constant(model=model,name="testConstant") 

        return_value = str(constant.add_arr_empty(name="testNameConstant"))
        expected_value = str(constant.model.constant(constant.name + "[" + "testNameConstant" + "]"))

        self.assertEqual(return_value,expected_value)

    def testConstant_equation_error(self):
        model = Model()
        constant = Constant(model=model,name="testConstant") 

        with self.assertRaises(ElementError) as context:
            constant.equation = "string"

if __name__ == '__main__':
    unittest.main()    