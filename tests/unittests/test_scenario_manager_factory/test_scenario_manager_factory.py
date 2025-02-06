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

    @patch("builtins.open", new_callable=mock_open)
    def test_reset_scenarios(self, mock_open_func):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_scenario_manager_factory","scenarios")

        real_json_content = json.dumps({
            "type": "sd",
            "smPortfolio":{
                "model": "simulation_models/simulation_model",
                "base_constants": {
                    "initialValue": 1000.0,
                    "interestRate": 0.05,
                    "depositRate": 1000.0
                },
                "scenarios":{
                    "base": {                
                    },
                    "scenarioLowInterest": {
                        "constants": {
                            "interestRate": 0.01
                    }
                    },
                    "scenarioHighInterest": {
                        "constants": {
                            "interestRate": 0.1
                        }
                    },
                    "scenarioLowDeposit": {
                        "constants": {
                            "depositRate": 2500.0
                        }
                    },
                    "scenarioHighDeposit": {
                        "constants": {
                            "depositRate": 100.0
                        }
                    },
                    "scenarioHighInitialValue": {
                        "constants": {
                            "initialValue": 5000.0                
                        }
                    }         
                }
            }
        })

        mock_json_content = json.dumps({
            "type": "sd",
            "smPortfolio":{
                "model": "simulation_models/simulation_model",
                "base_constants": {
                    "initialValue": 1000.0,
                    "interestRate": 0.05,
                    "depositRate": 1000.0
                },
                "scenarios":{
                    "base": {                
                    },
                    "scenarioLowInterest": {
                        "constants": {
                            "interestRate": 0.02 #changed
                    }
                    },
                    "scenarioHighInterest": {
                        "constants": {
                            "interestRate": 0.2 #changed
                        }
                    },
                    "scenarioLowDeposit": {
                        "constants": {
                            "depositRate": 2500.0
                        }
                    },
                    "scenarioHighDeposit": {
                        "constants": {
                            "depositRate": 100.0
                        }
                    },
                    "scenarioHighInitialValue": {
                        "constants": {
                            "initialValue": 5000.0                
                        }
                    }         
                }
            }
        })

        mock_open_func.side_effect = [
            mock_open(read_data=real_json_content).return_value,  #called when setting up the model and model_dictionary
            mock_open(read_data=real_json_content).return_value,  #called when setting the base constants
            mock_open(read_data=real_json_content).return_value,  #called when setting the base points
            mock_open(read_data=mock_json_content).return_value,  
            mock_open(read_data=mock_json_content).return_value,  
            mock_open(read_data=mock_json_content).return_value,

        ]        

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)
        self.assertEqual(sm.scenario_managers["smPortfolio"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"],0.01)
        self.assertEqual(sm.scenario_managers["smPortfolio"].scenarios["scenarioHighInterest"].dictionary["constants"]["interestRate"],0.1)

        sm.reset_scenario(scenario_manager="smPortfolio", scenario="scenarioLowInterest")
        self.assertEqual(sm.scenario_managers["smPortfolio"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"],0.02)
        #seems like all scenarios are resetted
        #self.assertEqual(sm.scenario_managers["smPortfolio"].scenarios["scenarioHighInterest"].dictionary["constants"]["interestRate"],0.1)


    @patch("builtins.open", new_callable=mock_open)
    def test_reset_all_scenarios(self, mock_open_func):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_scenario_manager_factory","scenarios")

        real_json_content = json.dumps({
            "type": "sd",
            "smPortfolio":{
                "model": "simulation_models/simulation_model",
                "base_constants": {
                    "initialValue": 1000.0,
                    "interestRate": 0.05,
                    "depositRate": 1000.0
                },
                "scenarios":{
                    "base": {                
                    },
                    "scenarioLowInterest": {
                        "constants": {
                            "interestRate": 0.01
                    }
                    },
                    "scenarioHighInterest": {
                        "constants": {
                            "interestRate": 0.1
                        }
                    },
                    "scenarioLowDeposit": {
                        "constants": {
                            "depositRate": 2500.0
                        }
                    },
                    "scenarioHighDeposit": {
                        "constants": {
                            "depositRate": 100.0
                        }
                    },
                    "scenarioHighInitialValue": {
                        "constants": {
                            "initialValue": 5000.0                
                        }
                    }         
                }
            }
        })

        mock_json_content = json.dumps({
            "type": "sd",
            "smPortfolio":{
                "model": "simulation_models/simulation_model",
                "base_constants": {
                    "initialValue": 1000.0,
                    "interestRate": 0.05,
                    "depositRate": 1000.0
                },
                "scenarios":{
                    "base": {                
                    },
                    "scenarioLowInterest": {
                        "constants": {
                            "interestRate": 0.02 #changed
                    }
                    },
                    "scenarioHighInterest": {
                        "constants": {
                            "interestRate": 0.2 #changed
                        }
                    },
                    "scenarioLowDeposit": {
                        "constants": {
                            "depositRate": 2500.0
                        }
                    },
                    "scenarioHighDeposit": {
                        "constants": {
                            "depositRate": 100.0
                        }
                    },
                    "scenarioHighInitialValue": {
                        "constants": {
                            "initialValue": 5000.0                
                        }
                    }         
                }
            }
        })

        mock_open_func.side_effect = [
            mock_open(read_data=real_json_content).return_value,  #called when setting up the model and model_dictionary
            mock_open(read_data=real_json_content).return_value,  #called when setting the base constants
            mock_open(read_data=real_json_content).return_value,  #called when setting the base points
            mock_open(read_data=mock_json_content).return_value,  
            mock_open(read_data=mock_json_content).return_value,  
            mock_open(read_data=mock_json_content).return_value  
        ]        

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)
        self.assertEqual(sm.scenario_managers["smPortfolio"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"],0.01)
        self.assertEqual(sm.scenario_managers["smPortfolio"].scenarios["scenarioHighInterest"].dictionary["constants"]["interestRate"],0.1)

        sm.reset_scenario(scenario_manager="smPortfolio", scenario="scenarioLowInterest")
        self.assertEqual(sm.scenario_managers["smPortfolio"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"],0.02)
        self.assertEqual(sm.scenario_managers["smPortfolio"].scenarios["scenarioHighInterest"].dictionary["constants"]["interestRate"],0.2)

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