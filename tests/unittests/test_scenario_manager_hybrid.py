import unittest

from BPTK_Py import Model, Agent
from BPTK_Py.scenariomanager.scenario_manager_hybrid import ScenarioManagerHybrid

class TestScenarioManagerSD(unittest.TestCase):
    def setUp(self):
        pass

    def testScenarioManagerHybrid_init_error(self):
        with self.assertRaises(ValueError) as context:
            scenarioManager = ScenarioManagerHybrid(json_config="testJsonConfig",name="testName",model="testModel") 

    def testScenarioMagerHybrid_get_config(self):
        scenarioManager = ScenarioManagerHybrid(json_config="testJsonConfig",name="testName",model=Model()) 

        self.assertEqual(scenarioManager.get_config(),"testJsonConfig")

    def testScenarioManagerHybrid_instantiate_model(self):
        import BPTK_Py.logger.logger as logmod
        logmod.loglevel="INFO"

        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()  

        model = Model()
        func1 = lambda agent_id, model, properties: Agent(agent_id=agent_id,model=model,properties=properties,agent_type="agent1")
        func2 = lambda agent_id, model, properties: Agent(agent_id=agent_id,model=model,properties=properties,agent_type="agent2")
        model.register_agent_factory(agent_type="agent1",agent_factory=func1)
        model.register_agent_factory(agent_type="agent2",agent_factory=func2)
        scenarioManager = ScenarioManagerHybrid(json_config="testJsonConfig",name="testScenarioManagerName",model=model) 

        scenarioDictionary = {
            "scenario1": {
                "runspecs": {
                    "starttime" : 1.0,
                    "stoptime" : 10.0,
                    "dt" : 2.0
                },
                "properties": {
                    "property1" : {
                        "type" : "Integer",
                        "value" : 1
                    },
                    "property2" : {
                        "type" : "String",
                        "value" : "StringValue1"
                    }
                },
                "agents" : [
                    {
                        "name" : "agent1",
                        "count" : 1,
                        "properties" : {
                            "agentproperty" : {
                                "type" : "String",
                                "value" : "testAgentProperty1"
                            }
                        }
                    },
                    {
                        "name" : "agent2",
                        "count" : 2,
                        "properties" : {
                            "agentproperty" : {
                                "type" : "String",
                                "value" : "testAgentProperty2"
                            }
                        }
                    }
                ]
                },
            "scenario2": {
                "runspecs": {
                    "starttime" : 2.0,
                    "stoptime" : 22.0,
                    "dt" : 4.0
                },
                "properties": {
                    "property1" : {
                        "type" : "String",
                        "value" : "StringValue2"

                    }
                },
                "agents" : [
                    {
                        "name" : "agent1",
                        "count" : 3,
                        "properties" : {
                            "agentproperty" : {
                                "type" : "String",
                                "value" : "testAgentProperty3"
                            }
                        }
                    },
                    {
                        "name" : "agent2",
                        "count" : 1,
                        "properties" : {
                            "agentproperty" : {
                                "type" : "String",
                                "value" : "testAgentProperty4"
                            }
                        }
                    }
                ]
            }
        }

        scenarioManager.instantiate_model(scenario_dictionary=scenarioDictionary,reset=True)

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[INFO] Resetting the simulation scenarios for testScenarioManagerName", content)         
        self.assertIn("[INFO] Successfully instantiated the simulation model for scenario scenario1", content)         
        self.assertIn("[INFO] Successfully instantiated the simulation model for scenario scenario2", content)  

        self.assertEqual(scenarioManager.scenarios["scenario1"].starttime,1.0)
        self.assertEqual(scenarioManager.scenarios["scenario1"].stoptime,10.0)
        self.assertEqual(scenarioManager.scenarios["scenario1"].dt,2.0)
        self.assertEqual(scenarioManager.scenarios["scenario1"].property1,1)
        self.assertEqual(scenarioManager.scenarios["scenario1"].property2,"StringValue1")
        self.assertEqual(scenarioManager.scenarios["scenario1"].agent(agent_id=0).get_property_value(name="agentproperty"),"testAgentProperty1")
        self.assertEqual(scenarioManager.scenarios["scenario1"].agent(agent_id=1).get_property_value(name="agentproperty"),"testAgentProperty2")
        self.assertEqual(scenarioManager.scenarios["scenario1"].agent(agent_id=2).get_property_value(name="agentproperty"),"testAgentProperty2")

        self.assertEqual(scenarioManager.scenarios["scenario2"].starttime,2.0)
        self.assertEqual(scenarioManager.scenarios["scenario2"].stoptime,22.0)
        self.assertEqual(scenarioManager.scenarios["scenario2"].dt,4.0)
        self.assertEqual(scenarioManager.scenarios["scenario2"].property1,"StringValue2")
        self.assertEqual(scenarioManager.scenarios["scenario2"].agent(agent_id=0).get_property_value(name="agentproperty"),"testAgentProperty3")
        self.assertEqual(scenarioManager.scenarios["scenario2"].agent(agent_id=1).get_property_value(name="agentproperty"),"testAgentProperty3")
        self.assertEqual(scenarioManager.scenarios["scenario2"].agent(agent_id=2).get_property_value(name="agentproperty"),"testAgentProperty3")
        self.assertEqual(scenarioManager.scenarios["scenario2"].agent(agent_id=3).get_property_value(name="agentproperty"),"testAgentProperty4")

if __name__ == '__main__':
    unittest.main()   
