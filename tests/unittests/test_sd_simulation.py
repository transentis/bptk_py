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


if __name__ == "__main__":
    unittest.main()
