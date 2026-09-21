import unittest

from BPTK_Py import Model
from BPTK_Py.sdsimulation import SdSimulation
import BPTK_Py.logger.logger as logmod


class Test_SdSimulation(unittest.TestCase):
    """The scenario settings a model never reads."""

    def _clear_logfile(self):
        with open(logmod.logfile, "w", encoding="UTF-8") as file:
            pass

    def _logfile_content(self):
        with open(logmod.logfile, "r", encoding="UTF-8") as file:
            return file.read()

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


if __name__ == "__main__":
    unittest.main()
