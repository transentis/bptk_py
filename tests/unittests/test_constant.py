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

    def testConstant_rejects_an_arrayed_equation(self):
        """A constant holds numbers, so neither an arrayed element nor an arrayed
        expression can be its equation - each would make a sub-constant hold an
        expression. Use `setup_vector` and its siblings for an arrayed constant, or a
        converter when the values follow from other elements.
        """
        model = Model()
        source = model.constant("source")
        source.setup_vector(2, [1.0, 2.0])

        for equation in (source, source * 2.0):
            with self.assertRaises(ElementError):
                model.constant("target").equation = equation


if __name__ == '__main__':
    unittest.main()    