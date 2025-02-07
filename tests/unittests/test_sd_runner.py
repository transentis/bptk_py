import unittest

from BPTK_Py.scenariomanager.scenario_manager_factory import ScenarioManagerFactory
from BPTK_Py.scenariorunners.sd_runner import SdRunner
import BPTK_Py.logger.logger as logmod

class TestSdRunner(unittest.TestCase):
    def setUp(self):
        pass

    def test_run_scenario_step_invalid(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)
        sdRunner = SdRunner(scenario_manager_factory=sm)

        self.assertEqual(sdRunner.run_scenario_step(step=1, settings=[], scenario_manager="testManager", scenarios=["testScenario"], equations=[]),{})

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] No scenarios found for scenario manager \"testManager\" and scenarios \"testScenario\"", content)  

    def test_run_scenario_invalid(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)
        sdRunner = SdRunner(scenario_manager_factory=sm)

        self.assertIsNone(sdRunner.run_scenario(sd_results_dict={}, return_format="json", scenario_managers=["testManager"], scenarios=["testScenario"], equations=[]))

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] No scenario found for scenario_managers=[\'testManager\'] and scenario_names=[\'testScenario\']. Cancelling", content)  

    def test_run_scenarios_invalid(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)
        sdRunner = SdRunner(scenario_manager_factory=sm)

        self.assertEqual(sdRunner._run_scenarios(scenario_managers=["testManager"], scenarios=["testScenario"], equations=[]),{})

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] No scenarios found for scenario managers \"testManager\" and scenarios \"testScenario\"", content)  

if __name__ == '__main__':
    unittest.main()    