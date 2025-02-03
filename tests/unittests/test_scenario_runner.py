import unittest
import pandas as pd
import sys, io

from BPTK_Py.scenariorunners.scenario_runner import ScenarioRunner

class TestScenarioRunner(unittest.TestCase):
    def setUp(self):
        pass

    def testScenarioRunner_run_scenario(self):
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

    def testScenarioRunner_run_scenario_step(self):
        #Redirect the console output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        scenarioRunner = ScenarioRunner(scenario_manager_factory="testScenarioManagerFactory")

        self.assertIsNone(scenarioRunner.run_scenario_step(step=1, settings="testSettings", scenario_manager="testScenarioManager", scenarios="testScenario", equations="testEqation", agents="testAgents"))

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        self.assertIn("IMPLEMENT THIS METHOD IN A SUBCLASS", output) 

    def testScenarioRunner_train_scenario(self):
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

if __name__ == '__main__':
    unittest.main()   
