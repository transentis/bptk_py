import unittest

from BPTK_Py import Model
from BPTK_Py.sddsl.biflow import Biflow


class TestBiflow(unittest.TestCase):
    """The arrayed hooks, which a Biflow lacked for a long time.

    `Biflow` inherited `Element.add_arr_equation`, a no-op `pass`: an arrayed biflow
    reported success, registered nothing and raised nothing. Mirrors
    `tests/unittests/test_flow.py`, which is the pattern the fix follows.
    """

    def testBiflow_add_arr_equation(self):
        model = Model()
        biflow = Biflow(model=model, name="testBiflow")

        biflow.add_arr_equation(name="testNameBiflow", value="testEquation")

        self.assertEqual(
            biflow.model.biflows["testBiflow[testNameBiflow]"].equation, "testEquation")

    def testBiflow_add_arr_empty(self):
        model = Model()
        biflow = Biflow(model=model, name="testBiflow")

        return_value = biflow.add_arr_empty(name="testNameBiflow")

        self.assertIs(return_value, model.biflows["testBiflow[testNameBiflow]"])

    def testBiflow_get_arr_equation(self):
        model = Model()
        biflow1 = Biflow(model=model, name="testBiflow1")
        biflow2 = Biflow(model=model, name="testBiflow2")

        biflow1.add_arr_equation(name="testName1", value="testEquation1")
        biflow2.add_arr_equation(name="testName2", value="testEquation2")

        # assertIs, not assertEqual: `Element.__eq__` builds a ComparisonOperator,
        # which is always truthy, so assertEqual on two Elements asserts nothing.
        self.assertIs(biflow1.get_arr_equation(name="testName1"),
                      model.biflows["testBiflow1[testName1]"])
        self.assertIs(biflow2.get_arr_equation(name="testName2"),
                      model.biflows["testBiflow2[testName2]"])

    def testBiflow_setup_named_vector_registers_every_sub_element(self):
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0)
        biflow = model.biflow("net")

        biflow.setup_named_vector({"in": 0.0, "out": 0.0})

        self.assertTrue(biflow.arrayed)
        self.assertTrue(biflow.named_arrayed)
        for name in ("in", "out"):
            self.assertIn("net[" + name + "]", model.biflows)
            self.assertIsNotNone(biflow[name])


if __name__ == '__main__':
    unittest.main()
