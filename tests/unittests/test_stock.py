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

        message = str(context.exception)
        # The message names the stock, what it was given, and where a computed value goes.
        self.assertIn("testStock", message)
        self.assertIn("str", message)
        self.assertIn("converter", message)

    def testStock_initial_value_accepts_an_integer(self):
        """Every other assignment takes a whole number; this one used to refuse it."""
        model = Model()
        stock = Stock(model=model, name="testStock")

        stock.initial_value = 100

        self.assertEqual(stock.initial_value, 100)

    def testStock_initial_value_refuses_a_boolean(self):
        """A bool is an int in Python, and `True` as a starting level is a slip."""
        model = Model()
        stock = Stock(model=model, name="testStock")

        with self.assertRaises(ElementError):
            stock.initial_value = True

    def testStock_initial_value_accepts_an_expression(self):
        """An initial value is an expression, as it is in the JSON format and in XMILE."""
        model = Model(starttime=0, stoptime=3, dt=1, name="initial_expression")
        constant = model.constant("k")
        constant.equation = 10.0
        stock = model.stock("stock")

        stock.initial_value = constant * 2.0 + 5.0

        flow = model.flow("flow")
        flow.equation = 0.0
        stock.equation = flow
        self.assertEqual(model.evaluate_equation("stock", 0.0), 25.0)

    def testStock_build_function_string(self):
        model = Model()
        stock = Stock(model=model,name="testStock") 

        stock.initial_value=2.0

        stock.equation = 1                

        stock.build_function_string()

        self.assertEqual(stock._function_string,"lambda model, t : ( (2.0) if (t <= model.starttime) else (model.memoize('testStock',t-model.dt))+ model.dt*(1) )")

if __name__ == '__main__':
    unittest.main()    