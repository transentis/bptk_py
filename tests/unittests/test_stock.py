import unittest

from BPTK_Py import Model
from BPTK_Py.sddsl.element import ElementError
from BPTK_Py.sddsl.stock import Stock

class TestStockunittest(unittest.TestCase):
    def setUp(self):
        pass

    def testStock_add_arr_empty(self):
        model = Model()
        stock = Stock(model=model,name="testStock") 

        return_value = str(stock.add_arr_empty(name="testNameStock"))
        expected_value = str(stock.model.stock(stock.name + "[" + "testNameStock" + "]"))

        self.assertEqual(return_value,expected_value)

    def testStock_initial_value_error(self):
        model = Model()
        stock = Stock(model=model,name="testStock") 

        with self.assertRaises(ElementError) as context:
            stock.initial_value = "string"

    def testStock_build_function_string(self):
        model = Model()
        stock = Stock(model=model,name="testStock") 

        stock.initial_value=2.0

        stock.equation = 1                

        stock.build_function_string()

        self.assertEqual(stock._function_string,"lambda model, t : ( (2.0) if (t <= model.starttime) else (model.memoize('testStock',t-model.dt))+ model.dt*(1) )")

if __name__ == '__main__':
    unittest.main()    