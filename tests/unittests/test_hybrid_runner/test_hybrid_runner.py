import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import os

from BPTK_Py.scenariorunners.hybrid_runner import HybridRunner
from BPTK_Py.scenariomanager.scenario_manager_factory import ScenarioManagerFactory
from tests.helpers.log_helpers import clear_log, read_log

class TestHybridRunner(unittest.TestCase):
    def test_get_df_for_agent(self):
        hybridRunner = HybridRunner(scenario_manager_factory="testScenarioManagerFactory")

        data = {
            "t1": {
                "agent1": { 
                    "state1": { 
                        "count": 1,  
                        "property1": {  
                            "type1": 2,  
                            "type2": 3
                        },
                        "property2": {  
                            "type1": 4,  
                            "type2": 5
                        }    
                    },
                    "state2": {
                        "count": 6, 
                        "property1": {
                            "type1": 7,
                            "type2": 8
                        },
                        "property2": {  
                            "type1": 9,  
                            "type2": 10
                        }     
                    }
                },
                "agent2": { 
                    "state1": { 
                        "count": 11,  
                        "property1": {  
                            "type1": 12,  
                            "type2": 13
                        },
                        "property2": {  
                            "type1": 14,  
                            "type2": 15
                        }    
                    },
                    "state2": {
                        "count": 16, 
                        "property1": {
                            "type1": 17,
                            "type2": 18
                        },
                        "property2": {  
                            "type1": 19,  
                            "type2": 20
                        }     
                    }
                }                
            },
            "t2": {
                "agent1": {
                    "state1": {
                        "count": 21, 
                        "property1": {  
                            "type1": 22,  
                            "type2": 23
                        },
                        "property2": {  
                            "type1": 24,  
                        "type2": 25
                        }                
                    },
                    "state2": {
                        "count": 26,
                        "property1": {
                            "type1": 27,
                            "type2": 28
                        },
                        "property2": {  
                                "type1": 29,  
                            "type2": 30
                        }               
                    }
                },
                "agent2": {
                    "state1": {
                        "count": 31, 
                        "property1": {  
                            "type1": 32,  
                            "type2": 33
                        },
                        "property2": {  
                            "type1": 34,  
                        "type2": 35
                        }                
                    },
                    "state2": {
                        "count": 36,
                        "property1": {
                            "type1": 37,
                            "type2": 38
                        },
                        "property2": {  
                                "type1": 39,  
                            "type2": 40
                        }               
                    }
                }                
            }    
        }
        pd_index = ["t1","t2"]
        pd1_data = [2,22]
        pd1_columns = ["state1_property1_type1"] 
        pd2_data = [
            [12,13,14,15,17,18,19,20],
            [32,33,34,35,37,38,39,40]
        ]
        pd2_columns = [
            "state1_property1_type1","state1_property1_type2","state1_property2_type1","state1_property2_type2",
            "state2_property1_type1","state2_property1_type2","state2_property2_type1","state2_property2_type2"           
        ]
        pd3_data = [1,21]
        pd3_columns = ["state1"]

        self.assertTrue(hybridRunner.get_df_for_agent(data=data,agent_name=None,agent_states=["state1"],agent_properties=["property1"],agent_property_types=["type1"]).equals(pd.DataFrame()))
        self.assertTrue(hybridRunner.get_df_for_agent(data=data,agent_name="agent1",agent_states=["state1"],agent_properties=["property1"],agent_property_types=["type1"]).equals(pd.DataFrame(data=pd1_data,index=pd_index,columns=pd1_columns)))
        self.assertTrue(hybridRunner.get_df_for_agent(data=data,agent_name="agent2",agent_states=["state1","state2"],agent_properties=["property1","property2"],agent_property_types=["type1","type2"]).equals(pd.DataFrame(data=pd2_data,index=pd_index,columns=pd2_columns)))
        # agent_states=[] has its own test below
        self.assertTrue(hybridRunner.get_df_for_agent(data=data,agent_name="agent1",agent_states=["state1"],agent_properties=[],agent_property_types=["type1"]).equals(pd.DataFrame(data=pd3_data, index=pd_index,columns=pd3_columns)))
        self.assertTrue(hybridRunner.get_df_for_agent(data=data,agent_name="agent1",agent_states=["state1"],agent_properties=["property1"],agent_property_types=[]).equals(pd.DataFrame()))

    def test_run_scenario_invalid(self):
        #cleanup logfile
        clear_log()

        hybridRunner = HybridRunner(scenario_manager_factory="testScenarioManagerFactory")

        self.assertTrue(hybridRunner.run_scenario(abm_results_dict={}, return_format=None, scenarios=[]).equals(pd.DataFrame()))
        hybridRunner.run_scenario(abm_results_dict={},return_format=None,scenarios={"scenario1","scenario2"})

        content = read_log()

        self.assertIn("[ERROR] No scenario to simulate found", content)

    def test_run_scenario(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_hybrid_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)        
        hybridRunner = HybridRunner(scenario_manager_factory=sm)

        #return format="json" without agent_properties
        result = hybridRunner.run_scenario(abm_results_dict={},
                                        return_format="json",
                                        scenarios=["test"],
                                        scenario_managers=["ABMsmSimpleProjectManagement"],
                                        agents=["task"],
                                        agent_states=["open"],
                                        agent_property_types=["total"])
        
        self.assertEqual(result,{'ABMsmSimpleProjectManagement': {'test': {'agents': {'task': {'open': {0: 18, 1: 17, 2: 16, 3: 15, 4: 13, 5: 12}}}}}})

        #return format="dict" without agent_properties
        result = hybridRunner.run_scenario(abm_results_dict={},
                                        return_format="dict",
                                        scenarios=["test"],
                                        scenario_managers=["ABMsmSimpleProjectManagement"],
                                        agents=["task"],
                                        agent_states=["open"],
                                        agent_property_types=["total"])        
        
        self.assertTrue(result["ABMsmSimpleProjectManagement"]["test"]["agents"]["task"]["open"].equals(pd.DataFrame({"open": [18, 17, 16, 15, 13, 12]})["open"]))

        #return format="dict" with agent_properties
        result = hybridRunner.run_scenario(abm_results_dict={},
                                        return_format="dict",
                                        scenarios=["test"],
                                        scenario_managers=["ABMsmSimpleProjectManagement"],
                                        agents=["task"],
                                        agent_states=["open"],
                                        agent_property_types=["mean","max","min","total"],
                                        agent_properties=["effort"])

        self.assertTrue(result["ABMsmSimpleProjectManagement"]["test"]["agents"]["task"]["open"]["properties"]["effort"]["mean"].
                        equals(pd.DataFrame({"mean": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]})["mean"]))
        self.assertTrue(result["ABMsmSimpleProjectManagement"]["test"]["agents"]["task"]["open"]["properties"]["effort"]["max"].
                        equals(pd.DataFrame({"max": [1, 1, 1, 1, 1, 1]})["max"]))
        self.assertTrue(result["ABMsmSimpleProjectManagement"]["test"]["agents"]["task"]["open"]["properties"]["effort"]["min"].
                        equals(pd.DataFrame({"min": [1, 1, 1, 1, 1, 1]})["min"]))
        self.assertTrue(result["ABMsmSimpleProjectManagement"]["test"]["agents"]["task"]["open"]["properties"]["effort"]["total"].
                        equals(pd.DataFrame({"total": [18, 17, 16, 15, 13, 12]})["total"]))

    def test_train_scenario(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_hybrid_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)        
        hybridRunner = HybridRunner(scenario_manager_factory=sm)     

        result1=hybridRunner.train_scenario(scenarios=["test"],
                    scenario_managers=["ABMsmSimpleProjectManagement"],
                    agents=["task"],
                    agent_states=["closed"],
                    episodes=5
        )

        self.assertTrue(result1.equals(pd.DataFrame({"ABMsmSimpleProjectManagement_test_task_closed": [7, 14, 17, 20, 20]}, index=[0, 1, 2, 3, 4])))

        result2=hybridRunner.train_scenario(scenarios=["test"],
                    scenario_managers=["ABMsmSimpleProjectManagement"],
                    agents=["task"],
                    agent_states=["closed"],
                    agent_properties=["effort"],
                    agent_property_types=["total"],
                    episodes=5
        )

        self.assertTrue(result2.equals(pd.DataFrame({"ABMsmSimpleProjectManagement_test_task_closed_effort_total": [7, 14, 17, 20, 20]}, index=[0, 1, 2, 3, 4])))

    def test_get_df_for_agent_empty_states(self):
        """With no agent_states named, every state the agent has is returned.

        This test used to pin the opposite: `get_stats_for` stored a bare `0` for the
        timestep and the loop below it called `.items()` on that int, so the most
        ordinary ABM call there is - plot an agent - raised AttributeError. The
        behaviour was recorded rather than fixed. Naming no state means all of them.
        """
        hybridRunner = HybridRunner(scenario_manager_factory="testScenarioManagerFactory")

        data = {1.0: {"agent1": {"open": {"count": 1}, "closed": {"count": 2}}}}

        df = hybridRunner.get_df_for_agent(data=data, agent_name="agent1",
                                           agent_states=[], agent_properties=[],
                                           agent_property_types=[])

        self.assertEqual(sorted(df.columns), ["closed", "open"])
        self.assertEqual(df.loc[1.0, "open"], 1)
        self.assertEqual(df.loc[1.0, "closed"], 2)

    def _build_runner(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir, "tests", "unittests", "test_hybrid_runner", "scenarios")
        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)
        sm.get_scenario_managers(path=testDir)
        return HybridRunner(scenario_manager_factory=sm), sm

    def test_run_scenario_skips_unfinished(self):
        """An unfinished scenario (scheduler.progress < 1.0) is skipped."""
        hybridRunner, sm = self._build_runner()
        scenario = sm.get_scenario("ABMsmSimpleProjectManagement", "test")

        # First run to populate statistics so the second call does not re-run it.
        hybridRunner.run_scenario(abm_results_dict={}, return_format="df",
                                  scenarios=["test"], scenario_managers=["ABMsmSimpleProjectManagement"],
                                  agents=["task"], agent_states=["open"], agent_property_types=["total"])

        # Simulate a cancelled/unfinished run.
        scenario.scheduler.progress = 0.5

        result = hybridRunner.run_scenario(abm_results_dict={}, return_format="df",
                                           scenarios=["test"], scenario_managers=["ABMsmSimpleProjectManagement"],
                                           agents=["task"], agent_states=["open"], agent_property_types=["total"])

        # The only scenario was skipped -> nothing to concatenate -> empty frame.
        self.assertTrue(result.equals(pd.DataFrame()))

    def test_run_scenario_no_data(self):
        """If a finished scenario produces no statistics, an empty frame is returned."""
        hybridRunner, sm = self._build_runner()
        scenario = sm.get_scenario("ABMsmSimpleProjectManagement", "test")

        clear_log()

        with patch.object(scenario, "statistics", return_value={}):
            result = hybridRunner.run_scenario(abm_results_dict={}, return_format="df",
                                               scenarios=["test"], scenario_managers=["ABMsmSimpleProjectManagement"],
                                               agents=["task"], agent_states=["open"], agent_property_types=["total"])

        self.assertTrue(result.equals(pd.DataFrame()))
        content = read_log()
        self.assertIn("[WARN] No output data produced.", content)

    def test_train_scenario_progress_widget(self):
        """train_scenario updates a passed-in progress widget each episode."""
        hybridRunner, sm = self._build_runner()
        progress_widget = MagicMock()
        progress_widget.value = -1

        episodes = 3
        hybridRunner.train_scenario(scenarios=["test"],
                                    scenario_managers=["ABMsmSimpleProjectManagement"],
                                    agents=["task"],
                                    agent_states=["open"],
                                    agent_property_types=["total"],
                                    episodes=episodes,
                                    progress_widget=progress_widget)

        # The widget value was written during training; last update is (episodes-1)/episodes.
        self.assertEqual(progress_widget.value, (episodes - 1) / episodes)
