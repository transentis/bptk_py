import unittest

from simulation_models.simulation_model import simulation_model
from BPTK_Py import Model
from BPTK_Py.sdsimulation.sd_simulation import SdSimulation
from unittest.mock import patch, MagicMock
import os, datetime
from tests.helpers.log_helpers import clear_log, read_log


class TestSdRunner(unittest.TestCase):
    def test_start_no_equations(self):
        #cleanup logfile
        clear_log()

        model = simulation_model()
        sdSimulation = SdSimulation(model=model, name="testSimulation")

        self.assertIsNone(sdSimulation.start())

        content = read_log()

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

    def test_start_evaluates_the_equations_in_order_in_the_calling_thread(self):
        """One thread per equation made a stochastic run depend on which thread drew
        first. The equations now run one after the other, where start() was called."""
        import threading
        from BPTK_Py import Model

        calls = []
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0, name="ordered")
        for name in ("first", "second"):
            model.add_equation(name, lambda t, name=name: calls.append(
                (name, t, threading.get_ident())) or 0.0)

        SdSimulation(model=model, name="testSimulation").start(equations=["first", "second"])

        self.assertEqual([(name, t) for name, t, _ in calls],
                         [("first", 0.0), ("first", 1.0), ("second", 0.0), ("second", 1.0)])
        self.assertEqual({ident for _, _, ident in calls}, {threading.get_ident()})

    def test_start_leaves_out_a_name_the_model_does_not_have(self):
        """Reporting it, with suggestions, is the caller's job."""
        sdSimulation = SdSimulation(model=simulation_model(), name="testSimulation")

        result = sdSimulation.start(output=["frame"], equations=["totalValue", "totalValu"])

        self.assertEqual(list(result.columns), ["totalValue"])

    def test_start_leaves_out_an_arrayed_element(self):
        """It has no values beside its cells; computing it answered a column of zeros."""
        from tests.helpers.arrayed_fixtures import build_workforce_model
        sdSimulation = SdSimulation(model=build_workforce_model(), name="testSimulation")

        result = sdSimulation.start(output=["frame"], equations=["headcount", "total_headcount"])

        self.assertEqual(list(result.columns), ["total_headcount"])

    def test_start_lets_a_key_error_inside_an_equation_through(self):
        """It used to be reported as a name that is not part of the model, and the
        equation's column quietly went missing."""
        model = simulation_model()
        model.equations["broken"] = lambda t: {}["missing"]
        sdSimulation = SdSimulation(model=model, name="testSimulation")

        with self.assertRaises(KeyError):
            sdSimulation.start(output=["frame"], equations=["broken"])

    @patch("pandas.DataFrame.to_csv")
    def test_start_writes_no_csv_unless_asked(self, mock_to_csv):
        model = simulation_model()

        SdSimulation(model=model, name="testSimulation").start(equations=["totalValue"])

        mock_to_csv.assert_not_called()


class TestSettingsTheModelNeverReads(unittest.TestCase):
    """The scenario settings a model never reads."""

    def _clear_logfile(self):
        clear_log()

    def _logfile_content(self):
        return read_log()

    def test_change_equation_warns_about_a_name_the_model_does_not_have(self):
        """A constant nothing reads used to be applied in silence.

        That is how a typo in a scenario definition - `Utilzation` where the model says
        `Utilization` - left two scenarios identical to the base case, with nothing in
        the log to say why. The warning names the near misses, because that is what a
        typo needs.
        """
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="typo")
        model.constant("Utilization").equation = 1.0
        simulation = SdSimulation(model=model, name="typo")

        self._clear_logfile()
        simulation.change_equation(name="Utilzation", value=2.0)
        content = self._logfile_content()

        self.assertIn("'Utilzation' is not an equation of this model", content)
        self.assertIn("did you mean 'Utilization'", content)

    def test_change_equation_stays_quiet_for_a_name_the_model_has(self):
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="clean")
        model.constant("Utilization").equation = 1.0
        simulation = SdSimulation(model=model, name="clean")

        self._clear_logfile()
        simulation.change_equation(name="Utilization", value=2.0)
        content = self._logfile_content()

        self.assertNotIn("is not an equation of this model", content)
        self.assertEqual(model.equations["Utilization"](0), 2.0)

    def test_change_points_stays_quiet_for_an_unknown_name(self):
        """A points set the scenario supplies and the model reads by name is normal.

        `sd.lookup(sd.time(), "hiringRate")` reads a name that only the scenario fills
        in, so an unknown name here is the ordinary case and must not warn - which is
        why the check sits on the constants and not here.
        """
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="points")
        simulation = SdSimulation(model=model, name="points")

        self._clear_logfile()
        simulation.change_points(name="hiringRate", value=[[0, 1], [1, 2]])
        content = self._logfile_content()

        self.assertNotIn("is not an equation of this model", content)
        self.assertEqual(model.points["hiringRate"], [[0, 1], [1, 2]])

    def test_a_constant_set_without_a_time_answers_the_same_at_every_time(self):
        """The whole-run path and a scenario's constants set no time and must not change."""
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="untimed")
        model.constant("orders").equation = 1.0
        simulation = SdSimulation(model=model, name="untimed")

        simulation.change_equation(name="orders", value=5.0)

        self.assertEqual(model.equations["orders"](0.0), 5.0)
        self.assertEqual(model.equations["orders"](3.0), 5.0)

    def test_a_constant_set_per_step_still_answers_for_the_step_it_was_set_at(self):
        """What a delay needs: asking about a past step gives the value in effect then.

        Without the time the equation is a `lambda t: value` that ignores `t`, so every
        lookback reads the value set last and the delay collapses to no lag at all.
        """
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="timed")
        model.constant("orders").equation = 1.0
        simulation = SdSimulation(model=model, name="timed")

        simulation.change_equation(name="orders", value=8.0, valid_from=0.0)
        simulation.change_equation(name="orders", value=20.0, valid_from=2.0)

        self.assertEqual(model.equations["orders"](0.0), 8.0)
        self.assertEqual(model.equations["orders"](1.0), 8.0)
        self.assertEqual(model.equations["orders"](2.0), 20.0)
        self.assertEqual(model.equations["orders"](3.0), 20.0)

    def test_a_time_before_the_first_override_keeps_the_models_own_equation(self):
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="before")
        model.constant("orders").equation = 1.0
        simulation = SdSimulation(model=model, name="before")

        simulation.change_equation(name="orders", value=20.0, valid_from=2.0)

        self.assertEqual(model.equations["orders"](1.0), 1.0)
        self.assertEqual(model.equations["orders"](2.0), 20.0)

    def test_setting_the_same_step_twice_corrects_it_rather_than_adding_to_it(self):
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="twice")
        model.constant("orders").equation = 1.0
        simulation = SdSimulation(model=model, name="twice")

        simulation.change_equation(name="orders", value=8.0, valid_from=1.0)
        simulation.change_equation(name="orders", value=9.0, valid_from=1.0)

        self.assertEqual(model.equations["orders"](1.0), 9.0)
        self.assertEqual(len(simulation._timed_constants["orders"]), 1)
