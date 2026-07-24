import unittest

from simulation_models.simulation_model import simulation_model
from BPTK_Py.sdsimulation.sd_simulation import SdSimulation
import BPTK_Py.logger.logger as logmod
from unittest.mock import patch, MagicMock
import os, datetime


class TestSdRunner(unittest.TestCase):
    def setUp(self):
        pass

    def test_start_no_equations(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        model = simulation_model()
        sdSimulation = SdSimulation(model=model, name="testSimulation")

        self.assertIsNone(sdSimulation.start())

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[WARN] testSimulation: No equation to simulate for given model! Check your scenario config of method parameters!", content)  

    @patch("os.makedirs") 
    @patch("os.path.exists", return_value=False) 
    @patch("pandas.DataFrame.to_csv")  
    def test_start_csv(self, mock_to_csv, mock_exists, mock_makedirs):
        model = simulation_model()
        sdSimulation = SdSimulation(model=model, name="testSimulation")

        sdSimulation.start(output=["csv"],equations=["totalValue"])

        mock_exists.assert_called_once_with("./results/") 
        mock_makedirs.assert_called_once_with("./results/")

        datestring = "{}_{}_{}".format(
            datetime.datetime.now().day,
            datetime.datetime.now().month,
            datetime.datetime.now().year
        )
        expected_filename = f"results/results_testSimulation_{datestring}.csv"
        mock_to_csv.assert_called_once_with(expected_filename)

    def test_change_equation(self):
        model = simulation_model()
        sdSimulation = SdSimulation(model=model, name="testSimulation")  

        sdSimulation.change_equation(name="totalValue",value=lambda t: 1000.0)

        self.assertEqual(sdSimulation.mod.equations["totalValue"](0),1000.0)
        self.assertEqual(sdSimulation.mod.equations["totalValue"](1),1000.0)
        self.assertEqual(sdSimulation.mod.equations["totalValue"](2),1000.0)

    def test_change_points(self):
        model = simulation_model()
        model.points = {"a": "1+1"}
        sdSimulation = SdSimulation(model=model, name="testSimulation")  

        sdSimulation.change_points(name="a", value="2+2")

        self.assertEqual(sdSimulation.mod.points["a"],4)

    def test_start_arrayed_equation_sums_result(self):
        """An arrayed equation (name contains "*") resolves to a list, which the
        simulation sums into a single value per timestep."""
        from BPTK_Py import Model

        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="arrayed")
        model.add_equation("vec[*]", lambda t: [1.0, 2.0, 3.0])

        sdSimulation = SdSimulation(model=model, name="testSimulation")
        df = sdSimulation.start(output=["frame"], equations=["vec[*]"])

        self.assertEqual(df["vec[*]"].to_dict(), {0.0: 6.0, 1.0: 6.0, 2.0: 6.0})

if __name__ == '__main__':
    unittest.main()