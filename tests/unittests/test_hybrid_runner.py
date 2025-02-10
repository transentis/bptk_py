import unittest
import pandas as pd

from BPTK_Py.scenariorunners.hybrid_runner import HybridRunner
import BPTK_Py.logger.logger as logmod

class TestHybridRunner(unittest.TestCase):
    def setUp(self):
        pass    

    def testHybridRunner_get_df_for_agent(self):
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
        #agent_states =[] is not covered yet
        self.assertTrue(hybridRunner.get_df_for_agent(data=data,agent_name="agent1",agent_states=["state1"],agent_properties=[],agent_property_types=["type1"]).equals(pd.DataFrame(data=pd3_data, index=pd_index,columns=pd3_columns)))
        self.assertTrue(hybridRunner.get_df_for_agent(data=data,agent_name="agent1",agent_states=["state1"],agent_properties=["property1"],agent_property_types=[]).equals(pd.DataFrame()))

    def testHybridRunner_run_scenario_empty(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        hybridRunner = HybridRunner(scenario_manager_factory="testScenarioManagerFactory")

        self.assertTrue(hybridRunner.run_scenario(abm_results_dict={}, return_format=None, scenarios=[]).equals(pd.DataFrame()))

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] No scenario to simulate found", content)  

if __name__ == '__main__':
    unittest.main()    