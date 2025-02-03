import unittest

from BPTK_Py import Model
from BPTK_Py.sddsl.stock import Stock
from BPTK_Py.sddsl.flow import Flow

class TestFlow(unittest.TestCase):
    def setUp(self):
        pass

    def testFlow_equation(self):
        model = Model()
        flow = Flow(model=model,name="testFlow") 

        self.assertIsNone(flow.equation)

        flow.equation = 1

        self.assertEqual(flow.equation,1)

    def testFlow_add_arr_equation(self):
        model = Model()
        flow = Flow(model=model,name="testFlow") 

        flow.add_arr_equation(name="testNameFlow", value="testEquation")

        self.assertEqual(flow.model.flows["testFlow[testNameFlow]"].equation,"testEquation")

    def testFlow_add_arr_empty(self):
        model = Model()
        flow = Flow(model=model,name="testFlow") 

        return_value = str(flow.add_arr_empty(name="testNameFlow"))
        expected_value = str(flow.model.constant(flow.name + "[" + "testNameFlow" + "]"))

        self.assertEqual(return_value,expected_value)

    def testFlow_get_arr_equation(self):
        model = Model()
        flow1 = Flow(model=model,name="testFlow1") 
        flow2 = Flow(model=model,name="testFlow2")

        flow1.add_arr_equation(name="testNameFlow1", value="testEquation1")
        flow2.add_arr_equation(name="testNameFlow2", value="testEquation2") 

        self.assertEqual(flow1.get_arr_equation(name="testNameFlow1"),flow1.model.flows["testFlow1[testNameFlow1]"])
        self.assertEqual(flow2.get_arr_equation(name="testNameFlow2"),flow1.model.flows["testFlow2[testNameFlow2]"])

if __name__ == '__main__':
    unittest.main()    