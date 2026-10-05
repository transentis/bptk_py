import unittest
import pandas as pd
import sys, io

from BPTK_Py.scenariorunners.scenario_runner import ScenarioRunner

class TestScenarioRunner(unittest.TestCase):
    def test_run_scenario(self):
        #Redirect the console output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        scenarioRunner = ScenarioRunner(scenario_manager_factory="testScenarioManagerFactory")

        self.assertTrue(scenarioRunner.run_scenario(scenarios="testScenario", equations="testEquation", agents="testAgents").equals(pd.DataFrame()))

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        self.assertIn("IMPLEMENT THIS METHOD IN A SUBCLASS", output)  

    def test_train_scenario(self):
        #Redirect the console output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        scenarioRunner = ScenarioRunner(scenario_manager_factory="testScenarioManagerFactory")

        self.assertIsNone(scenarioRunner.train_scenario(scenarios="testScenario", agents="testAgents"))

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        self.assertIn("IMPLEMENT THIS METHOD IN A SUBCLASS", output)
