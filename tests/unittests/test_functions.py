import math
import unittest

import numpy as np

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
from BPTK_Py.sddsl.element import Element
from BPTK_Py.sddsl.functions import pulse, trend, smooth, delay
from BPTK_Py.sddsl.operators import OperatorError, Trend, And, Ln, Log10, Floor, Ceil

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

class TestLnLog10FloorCeil(unittest.TestCase):
    """Tests for the ln, log10, floor, ceil SD DSL operators."""

    def _eval(self, equation, constant_val):
        """Helper: build a model with a constant and a converter using the equation, return converter value at t=1."""
        model = Model(starttime=1, stoptime=2, dt=1, name="test")
        c = model.constant("c")
        c.equation = constant_val
        out = model.converter("out")
        out.equation = equation(c)
        return out(1)

    def test_ln_of_e(self):
        result = self._eval(sd.ln, math.e)
        self.assertAlmostEqual(result, 1.0, places=10)

    def test_ln_of_1(self):
        result = self._eval(sd.ln, 1.0)
        self.assertAlmostEqual(result, 0.0, places=10)

    def test_ln_of_scalar(self):
        """ln should work with a scalar constant."""
        model = Model(starttime=1, stoptime=2, dt=1, name="test")
        c = model.constant("c")
        c.equation = 10.0
        out = model.converter("out")
        out.equation = sd.ln(c)
        self.assertAlmostEqual(out(1), math.log(10.0), places=10)

    def test_log10_of_100(self):
        result = self._eval(sd.log10, 100.0)
        self.assertAlmostEqual(result, 2.0, places=10)

    def test_log10_of_1(self):
        result = self._eval(sd.log10, 1.0)
        self.assertAlmostEqual(result, 0.0, places=10)

    def test_log10_of_1000(self):
        result = self._eval(sd.log10, 1000.0)
        self.assertAlmostEqual(result, 3.0, places=10)

    def test_floor_positive(self):
        result = self._eval(sd.floor, 3.7)
        self.assertAlmostEqual(result, 3.0, places=10)

    def test_floor_negative(self):
        result = self._eval(sd.floor, -2.3)
        self.assertAlmostEqual(result, -3.0, places=10)

    def test_floor_integer(self):
        result = self._eval(sd.floor, 5.0)
        self.assertAlmostEqual(result, 5.0, places=10)

    def test_ceil_positive(self):
        result = self._eval(sd.ceil, 3.2)
        self.assertAlmostEqual(result, 4.0, places=10)

    def test_ceil_negative(self):
        result = self._eval(sd.ceil, -2.7)
        self.assertAlmostEqual(result, -2.0, places=10)

    def test_ceil_integer(self):
        result = self._eval(sd.ceil, 5.0)
        self.assertAlmostEqual(result, 5.0, places=10)

    def test_ln_of_element_reference(self):
        """ln of another converter (not just a constant)."""
        model = Model(starttime=1, stoptime=5, dt=1, name="test")
        inp = model.converter("inp")
        inp.equation = sd.time()
        out = model.converter("out")
        out.equation = sd.ln(inp)
        for t in [1.0, 2.0, 3.0, 4.0, 5.0]:
            self.assertAlmostEqual(out(t), math.log(t), places=10)

    def test_composition_floor_of_ln(self):
        """floor(ln(x)) — composing two new operators."""
        model = Model(starttime=1, stoptime=2, dt=1, name="test")
        c = model.constant("c")
        c.equation = 10.0
        out = model.converter("out")
        out.equation = sd.floor(sd.ln(c))
        # ln(10) ≈ 2.302, floor → 2.0
        self.assertAlmostEqual(out(1), 2.0, places=10)

    def test_operator_classes_exist(self):
        """Verify operator classes can be instantiated directly."""
        self.assertIsInstance(Ln(1.0), Ln)
        self.assertIsInstance(Log10(1.0), Log10)
        self.assertIsInstance(Floor(1.0), Floor)
        self.assertIsInstance(Ceil(1.0), Ceil)


if __name__ == '__main__':
    unittest.main()