import unittest
from unittest.mock import mock_open, patch
from BPTK_Py.scenariomanager.scenario_manager_factory import ScenarioManagerFactory
import os, json
from BPTK_Py import Model
from  BPTK_Py.scenariomanager.scenario import SimulationScenario
import BPTK_Py.logger.logger as logmod


class TestScenarioManagerFactory(unittest.TestCase):
    def setUp(self):
        pass

    def test_readScenario_invalid(self):
        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")
        self.assertIsNone(sm._ScenarioManagerFactory__readScenario(filename=testDir))

        testFile = os.path.join(testDir,"invalidFileName")

        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()        

        self.assertIsNone(sm._ScenarioManagerFactory__readScenario(filename=testFile))

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn(f"[ERROR] No parser available for file {testFile}. Skipping!", content)  

    def test_reset_scenarios(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)
        self.assertEqual(sm.scenario_managers["smPortfolio1"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"],0.01)
        self.assertEqual(sm.scenario_managers["smPortfolio1"].scenarios["scenarioHighInterest"].dictionary["constants"]["interestRate"],0.1)
        self.assertEqual(sm.scenario_managers["smPortfolio2"].scenarios["scenarioHighInitialValue"].dictionary["constants"]["initialValue"],5000.0)

        sm.scenario_managers["smPortfolio1"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"] = 0.02        
        sm.scenario_managers["smPortfolio1"].scenarios["scenarioHighInterest"].dictionary["constants"]["interestRate"] = 0.2
        sm.scenario_managers["smPortfolio2"].scenarios["scenarioHighInitialValue"].dictionary["constants"]["initialValue"] = 10000.0

        sm.reset_scenario(scenario_manager="smPortfolio1", scenario="scenarioLowInterest")
        self.assertEqual(sm.scenario_managers["smPortfolio1"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"],0.01)
        #seems like all scenarios are resetted
        #self.assertEqual(sm.scenario_managers["smPortfolio1"].scenarios["scenarioHighInterest"].dictionary["constants"]["interestRate"],0.2)
        #self.assertEqual(sm.scenario_managers["smPortfolio2"].scenarios["scenarioHighInitialValue"].dictionary["constants"]["initialValue"],10000.0)

    def test_reset_all_scenarios(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)
        self.assertEqual(sm.scenario_managers["smPortfolio1"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"],0.01)
        self.assertEqual(sm.scenario_managers["smPortfolio1"].scenarios["scenarioHighInterest"].dictionary["constants"]["interestRate"],0.1)
        self.assertEqual(sm.scenario_managers["smPortfolio2"].scenarios["scenarioHighInitialValue"].dictionary["constants"]["initialValue"],5000.0)

        sm.reset_all_scenarios()
        
        self.assertEqual(sm.scenario_managers,{})      

    def test_get_scenarios(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)        

        self.assertEqual(sm.get_scenarios(scenario_managers=["smPortfolio1","smPortfolio2"], scenarios=["scenarioHighInterest","scenarioHighInitialValue"])["smPortfolio1_scenarioHighInterest"].name, "scenarioHighInterest")
        self.assertEqual(sm.get_scenarios(scenario_managers=["smPortfolio1","smPortfolio2"], scenarios=["scenarioHighInterest","scenarioHighInitialValue"])["smPortfolio2_scenarioHighInitialValue"].name, "scenarioHighInitialValue")

        self.assertEqual(sm.get_scenarios(scenario_managers=["smPortfolio1"], scenarios=["scenarioHighInterest"])["scenarioHighInterest"].name, "scenarioHighInterest")        

        self.assertEqual(sm.get_scenarios(scenario_managers=["smPortfolio1"], scenarios=["scenarioHighInitialValue"]),{})          


    def test_add_scenario_existing_manager(self):
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

        dictionary = {
            "constants": {
                "interestRate": 0.99
            }            
        }

        addScenario = SimulationScenario(dictionary=dictionary,name="addScenario", model=Model(), scenario_manager_name="smPortfolio1")    

        sm.add_scenario(scenario=addScenario,scenario_manager="smPortfolio1")  

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[WARN] Model Manager already existing. Not overwriting the model!", content)  
        self.assertEqual(sm.scenario_managers["smPortfolio1"].scenarios["addScenario"].get_property_value(name="interestRate"),0.99)    

    def test_add_scenario_not_existing_manager(self):
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

        dictionary = {
            "constants": {
                "interestRate": 0.99
            }            
        }

        currentDir = os.path.abspath(os.getcwd())
        modelFile = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","simulation_models","simulation_model")        

        addScenario = SimulationScenario(dictionary=dictionary,name="addScenario", model=Model(), scenario_manager_name="addManager")    

        sm.add_scenario(scenario=addScenario,scenario_manager="addManager", model=modelFile)  

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertNotIn("[WARN] Model Manager already existing. Not overwriting the model!", content)  
        self.assertEqual(sm.scenario_managers["addManager"].scenarios["addScenario"].get_property_value(name="interestRate"),0.99)   

    def test_create_scenario(self):
        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        test_filename = "test.json"
        test_data = {
            "constants": {
                "interestRate": 0.001
            }            
        }

        mock_file = mock_open()

        with patch("builtins.open", mock_file):
            sm.create_scenario(filename=test_filename, dictionary=test_data)

            mock_file.assert_called_once_with(test_filename, "w", encoding="utf-8")

            content = "".join(call.args[0] for call in mock_file().write.call_args_list)

            self.assertEqual(json.loads(content),test_data)

    def test_get_all_base_constants_invalid(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()     

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")
        testFile = os.path.join(testDir,"invalidFileName")

        self.assertIsNone(sm._ScenarioManagerFactory__get_all_base_constants(scenario_manager="smPortfolio1", filenames=[testFile]))

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn(f"[ERROR] No parser available for file {testFile}. Skipping!", content)  

    def test_get_all_base_constants_points(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()     

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")
        testFile = os.path.join(testDir,"invalidFileName")

        self.assertIsNone(sm._ScenarioManagerFactory__get_all_base_points(scenario_manager="smPortfolio1", filenames=[testFile]))

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn(f"[ERROR] No parser available for file {testFile}. Skipping!", content)  

if __name__ == '__main__':
    unittest.main()   