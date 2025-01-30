import unittest

from BPTK_Py import Model
from BPTK_Py.sddsl.element import Element
from BPTK_Py.sddsl.functions import pulse, trend, smooth, delay
from BPTK_Py.sddsl.operators import OperatorError, Trend, And

class TestFunctions(unittest.TestCase):
    def setUp(self):
        pass

    def test_pulse_errors(self):
        model = Model()
        with self.assertRaisesRegex(OperatorError, "The volume must be a model element or a floating point value"):
            pulse(model, "stringVolume", 0.0, 0.0)
        with self.assertRaisesRegex(OperatorError, "The first pulse must be a floating point values or a constant"):
            pulse(model, 1.0, "strinFirstPulse", 0.0)
        with self.assertRaisesRegex(OperatorError, "The interval must be a floating point values or a constant"):
            pulse(model, 1.0, 0.0, "stringInterval")

    def test_trend(self):
        model = Model()

        trendOperator = trend(model=model, input_function= 1, averaging_time= 1, initial_value = 1.0)     
        self.assertIsInstance(trendOperator,Trend)  

        with self.assertRaisesRegex(OperatorError, "The initial value must be a floating point values or a constants"):
            trend(model=model, input_function= 1, averaging_time= 1, initial_value = "stringInitialValue")      

    def test_smooth_error(self):
        model = Model()

        with self.assertRaisesRegex(OperatorError, "The initial value must be a floating point values or a constants"):
            smooth(model=model, input_function= 1, averaging_time= 1, initial_value = "stringInitialValue")

    def test_delay_errors(self):        
        model = Model()
        inputFunction = Element(model=model,name="testElement",function_string=None)
        with self.assertRaisesRegex(OperatorError, "The input function must be a model element"):
            delay(model, "stringInputFunction", 0.0)
        with self.assertRaisesRegex(OperatorError, "The delay duration must be a model element or a floating point value"):
            delay(model, inputFunction, "stringDelayDuration")
        with self.assertRaisesRegex(OperatorError, "The initial value must be a floating point values or a constant"):
            delay(model, inputFunction, 0.0, "stringInitialValue")       

if __name__ == '__main__':
    unittest.main()    