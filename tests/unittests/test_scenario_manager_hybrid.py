import unittest

from BPTK_Py import Model, Agent
from BPTK_Py.scenariomanager.scenario_manager_hybrid import ScenarioManagerHybrid
from tests.helpers.log_helpers import clear_log, read_log

class TestScenarioManagerSD(unittest.TestCase):
    def test_scenario_manager_hybrid_init_error(self):
        with self.assertRaises(ValueError) as context:
            scenarioManager = ScenarioManagerHybrid(json_config="testJsonConfig",name="testName",model="testModel") 

    def test_scenario_manager_hybrid_get_config(self):
        scenarioManager = ScenarioManagerHybrid(json_config="testJsonConfig",name="testName",model=Model()) 

        self.assertEqual(scenarioManager.get_config(),"testJsonConfig")

    def test_scenario_manager_hybrid_instantiate_model(self):
        import BPTK_Py.logger.logger as logmod
        logmod.loglevel="INFO"

        #cleanup logfile
        clear_log()

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

        content = read_log()

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

    def test_scenario_manager_hybrid_instantiate_model_missing_module(self):
        """If the configured model module cannot be imported, the manager logs and skips."""
        import BPTK_Py.logger.logger as logmod
        logmod.loglevel = "INFO"
        clear_log()

        json_config = {"model": "nonexistent.module.Foo", "scenarios": {"scenario1": {}}}
        scenarioManager = ScenarioManagerHybrid(json_config=json_config, name="mgr", model=None)

        scenarioManager.instantiate_model(reset=True)

        self.assertEqual(scenarioManager.scenarios, {})  # nothing instantiated

        content = read_log()
        self.assertIn("[ERROR] File nonexistent/module.py not found", content)
        # The message used to end on "Original Error: " with nothing after it
        self.assertIn("Original Error: No module named 'nonexistent'", content)

    def test_scenario_manager_hybrid_initialises_its_base(self):
        scenarioManager = ScenarioManagerHybrid(json_config={}, name="mgr")

        self.assertEqual(scenarioManager.name, "mgr")
        self.assertEqual(scenarioManager.type, "abm")
        self.assertEqual(scenarioManager.scenarios, {})

    def test_scenario_manager_hybrid_instantiate_model_missing_class(self):
        """If the model class is not found in the module, the manager logs and skips."""
        import BPTK_Py.logger.logger as logmod
        logmod.loglevel = "INFO"
        clear_log()

        json_config = {"model": "BPTK_Py.NonExistentClass", "scenarios": {"scenario1": {}}}
        scenarioManager = ScenarioManagerHybrid(json_config=json_config, name="mgr", model=None)

        scenarioManager.instantiate_model(reset=True)

        self.assertEqual(scenarioManager.scenarios, {})  # nothing instantiated

        content = read_log()
        self.assertIn("[ERROR] Could not find class NonExistentClass in BPTK_Py", content)
