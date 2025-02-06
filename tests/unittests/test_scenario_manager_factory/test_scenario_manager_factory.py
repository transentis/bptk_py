import unittest
from unittest.mock import patch, mock_open
from BPTK_Py.scenariomanager.scenario_manager_factory import ScenarioManagerFactory
import os, json
import BPTK_Py.logger.logger as logmod


class TestScenarioManagerFactory(unittest.TestCase):
    def setUp(self):
        pass

    def test_readScenario_invalid(self):
        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_scenario_manager_factory","scenarios")
        self.assertIsNone(sm._ScenarioManagerFactory__readScenario(filename=testDir))

        testFile1 = os.path.join(testDir,"invalidFileName")

        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()        

        self.assertIsNone(sm._ScenarioManagerFactory__readScenario(filename=testFile1))

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn(f"[ERROR] No parser available for file {testFile1}. Skipping!", content)  

    def test_get_scenarios(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_scenario_manager_factory","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)        

        self.assertEqual(sm.get_scenarios(scenario_managers=["smPortfolio1","smPortfolio2"], scenarios=["scenarioHighInterest","scenarioHighInitialValue"])["smPortfolio1_scenarioHighInterest"].name, "scenarioHighInterest")
        self.assertEqual(sm.get_scenarios(scenario_managers=["smPortfolio1","smPortfolio2"], scenarios=["scenarioHighInterest","scenarioHighInitialValue"])["smPortfolio2_scenarioHighInitialValue"].name, "scenarioHighInitialValue")

        self.assertEqual(sm.get_scenarios(scenario_managers=["smPortfolio1"], scenarios=["scenarioHighInterest"])["scenarioHighInterest"].name, "scenarioHighInterest")        

        self.assertEqual(sm.get_scenarios(scenario_managers=["smPortfolio1"], scenarios=["scenarioHighInitialValue"]),{})          


if __name__ == '__main__':
    unittest.main()   