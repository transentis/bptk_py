import unittest

from BPTK_Py.scenariomanager.scenario_manager_factory import ScenarioManagerFactory
from BPTK_Py.scenariorunners.sd_runner import SdRunner
import BPTK_Py.logger.logger as logmod
import os

class TestSdRunner(unittest.TestCase):
    def setUp(self):
        pass

    def test_run_scenario_step(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)
        sdRunner = SdRunner(scenario_manager_factory=sm)

        settings = {
            "smPortfolio1": {
                "scenarioLowInterest": {
                    "points": {
                        "testBasePoints": [
                            [0.0,0.2],
                            [1.0,0.8]                        
                        ]
                    }    
                }
            }
        }

        self.assertEqual(sdRunner.run_scenario_step(step=0, settings=settings, scenario_manager="smPortfolio1", scenarios=["scenarioLowInterest"], equations=["totalValue"]),{'scenarioLowInterest': {'totalValue': {0.0: 1000.0}}})
        self.assertEqual(sdRunner.run_scenario_step(step=1, settings=settings, scenario_manager="smPortfolio1", scenarios=["scenarioLowInterest"], equations=["totalValue"]),{'scenarioLowInterest': {'totalValue': {1.0: 2010.0}}})
        self.assertEqual(sdRunner.run_scenario_step(step=2, settings=settings, scenario_manager="smPortfolio1", scenarios=["scenarioLowInterest"], equations=["totalValue"]),{'scenarioLowInterest': {'totalValue': {2.0: 3030.1}}})

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

    def test_run_scenario_did_you_mean(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)
        sdRunner = SdRunner(scenario_manager_factory=sm)

        self.assertEqual(sdRunner.run_scenario(sd_results_dict={},return_format="json", scenario_managers=["smPortfolio1"], scenarios=["scenarioLowInterest"], equations=["totalValu"]),{})        

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] No simulation model containing equation \"totalValu\". Did you maybe mean one of \"totalValue", content)  

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