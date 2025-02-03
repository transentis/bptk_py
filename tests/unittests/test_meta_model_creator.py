import unittest

from BPTK_Py import Model, Agent
from BPTK_Py.modelparser.meta_model_creator import ModelCreator, serializable_agent
from BPTK_Py import DataCollector


class TestModelCreator(unittest.TestCase):
    def setUp(self):
        pass

    def testModelCreator_add_scenario(self):
        modelCreator = ModelCreator(name="testModelCreator")

        dataCollector = DataCollector()

        properties = {
            "property1":
            {
                "type": "String",
                "value": "testProperty1"
            },
            "property2":
            {
                "type": "Integer",
                "value": 2
            }
        }

        return_value = modelCreator.add_scenario(name="testScenario",starttime=1, stoptime=10, dt=2, properties=properties, datacollector=dataCollector)
        self.assertEqual(return_value,modelCreator)

        self.assertEqual(modelCreator.scenarios["testScenario"]["runspecs"]["starttime"],1)
        self.assertEqual(modelCreator.scenarios["testScenario"]["runspecs"]["stoptime"],10)
        self.assertEqual(modelCreator.scenarios["testScenario"]["runspecs"]["dt"],2)
        self.assertEqual(modelCreator.scenarios["testScenario"]["runspecs"]["dt"],2)
        self.assertEqual(modelCreator.scenarios["testScenario"]["agents"],[])
        self.assertEqual(modelCreator.scenarios["testScenario"]["properties"]["property1"]["type"],"String")
        self.assertEqual(modelCreator.scenarios["testScenario"]["properties"]["property1"]["value"],"testProperty1")
        self.assertEqual(modelCreator.scenarios["testScenario"]["properties"]["property2"]["type"],"Integer")
        self.assertEqual(modelCreator.scenarios["testScenario"]["properties"]["property2"]["value"],2)
        self.assertEqual(modelCreator.datacollector, dataCollector)

    def testModelCreator_add_agent(self):
        modelCreator = ModelCreator(name="testModelCreator")
        agent = serializable_agent(name="testAgent", count=1, step=2)        
        modelCreator.add_scenario(name="testScenario",starttime=1, stoptime=10, dt=2)

        modelCreator.add_agent(scenario="testScenario", agent=agent)

        self.assertEqual(modelCreator.scenarios["testScenario"]["agents"][0].name,"testAgent")
        self.assertEqual(modelCreator.scenarios["testScenario"]["agents"][0].count,1)
        self.assertEqual(modelCreator.scenarios["testScenario"]["agents"][0].step,2)

    def testModelCreator_create_model_standard(self):
        import BPTK_Py.logger.logger as logmod
        import sys, io

        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        #Redirect the console output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        modelCreator = ModelCreator(name="testModelCreator")
        serialAgent = serializable_agent(name="testAgent", count=3, step=4)        
        modelCreator.add_scenario(name="testScenario",starttime=1, stoptime=10, dt=2)
        modelCreator.add_agent(scenario="testScenario", agent=serialAgent)

        model, dictionaryValues = modelCreator.create_model()

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()    

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[WARN] Could not load specific model class. Using standard Model", content)  
        self.assertIn("Empty module name", output)  
        self.assertIn("ERROR", output)              

        self.assertIsInstance(model,Model)

        self.assertEqual(dictionaryValues["testModelCreator"]["name"],"testModelCreator")
        self.assertEqual(dictionaryValues["testModelCreator"]["type"],"abm")
        self.assertIsNone(dictionaryValues["testModelCreator"]["datacollector"])
        self.assertIsNone(dictionaryValues["testModelCreator"]["json_dict"])
        self.assertEqual(dictionaryValues["testModelCreator"]["model"],"model")
        self.assertFalse(dictionaryValues["testModelCreator"]["silent"])
        self.assertEqual(dictionaryValues["testModelCreator"]["properties"],[])
        self.assertEqual(dictionaryValues["testModelCreator"]["scenarios"]["testScenario"]["runspecs"]["starttime"],1)
        self.assertEqual(dictionaryValues["testModelCreator"]["scenarios"]["testScenario"]["runspecs"]["stoptime"],10)
        self.assertEqual(dictionaryValues["testModelCreator"]["scenarios"]["testScenario"]["runspecs"]["dt"],2)
        self.assertEqual(dictionaryValues["testModelCreator"]["scenarios"]["testScenario"]["agents"][0]["name"],"testAgent")
        self.assertEqual(dictionaryValues["testModelCreator"]["scenarios"]["testScenario"]["agents"][0]["count"],3)
        self.assertEqual(dictionaryValues["testModelCreator"]["scenarios"]["testScenario"]["agents"][0]["step"],4)
        self.assertEqual(dictionaryValues["testModelCreator"]["scenarios"]["testScenario"]["agents"][0]["properties"],{})
        self.assertEqual(dictionaryValues["testModelCreator"]["scenarios"]["testScenario"]["agents"][0]["classname"],"BPTK_Py.Agent")
        self.assertFalse(dictionaryValues["testModelCreator"]["scenarios"]["testScenario"]["agents"][0]["silent"])
        self.assertEqual(dictionaryValues["testModelCreator"]["scenarios"]["testScenario"]["properties"],{})

        agentModel = Model()
        agent = model.agent_factories["testAgent"](agent_id=101, model=agentModel,properties={})

        self.assertIsInstance(agent,Agent)
        self.assertEqual(agent.id,101)
        self.assertEqual(agent.model,agentModel)
        self.assertEqual(agent.properties,{})
        self.assertEqual(agent.agent_type,"testAgent")

class TestSerializableAgent(unittest.TestCase):
    def setUp(self):
        pass

    def testSerializableAgent_init(self):         
        properties = {
            "property1":
            {
                "type": "String",
                "value": "testProperty1"
            },
            "property2":
            {
                "type": "Integer",
                "value": 2
            }
        }    
        agent1 = serializable_agent(name="testAgent1", count=1, step=2)   
        agent2 = serializable_agent(name="testAgent2", count=3, step=4, properties=properties, classname="testClassName", previous="testPrevious", target="testTarget" , silent=True)   

        self.assertEqual(agent1.count,1)
        self.assertEqual(agent1.step,2)
        self.assertEqual(agent1.name,"testAgent1")
        self.assertEqual(agent1.properties,{})            
        self.assertEqual(agent1.classname,"BPTK_Py.Agent")
        self.assertFalse(agent1.silent)

        self.assertEqual(agent2.count,3)
        self.assertEqual(agent2.step,4)
        self.assertEqual(agent2.name,"testAgent2")
        self.assertEqual(agent2.properties["property1"]["type"],"String")
        self.assertEqual(agent2.properties["property1"]["value"],"testProperty1")
        self.assertEqual(agent2.properties["property2"]["type"],"Integer")
        self.assertEqual(agent2.properties["property2"]["value"],2)
        self.assertEqual(agent2.properties["previous"]["type"],"String")
        self.assertEqual(agent2.properties["previous"]["value"],"testPrevious")        
        self.assertEqual(agent2.properties["target"]["type"],"String")
        self.assertEqual(agent2.properties["target"]["value"],"testTarget")            
        self.assertEqual(agent2.classname,"testClassName")
        self.assertTrue(agent2.silent)

    def testSerializableAgent_set_previous(self):         
        agent = serializable_agent(name="testAgent", count=1, step=2)   

        agent.set_previous(name="testNamePrevious")

        self.assertEqual(agent.properties["previous"]["type"],"String")
        self.assertEqual(agent.properties["previous"]["value"],"testNamePrevious") 

    def testSerializableAgent_set_target(self):         
        agent = serializable_agent(name="testAgent", count=1, step=2)   

        agent.set_target(name="testNameTarget")

        self.assertEqual(agent.properties["target"]["type"],"String")
        self.assertEqual(agent.properties["target"]["value"],"testNameTarget") 

    def testSerializableAgent_set_property(self):     
        import sys, io


        agentNotSilent = serializable_agent(name="testAgent1", count=1, step=2)
        agentSilent = serializable_agent(name="testAgent2", count=1, step=2,silent=True) 

        #Redirect the console output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout           

        agentNotSilent.set_property(name="testNamePropertyNotSilent", type="Integer", value=11)

        self.assertEqual(agentNotSilent.properties["testNamePropertyNotSilent"]["type"],"Integer")
        self.assertEqual(agentNotSilent.properties["testNamePropertyNotSilent"]["value"],11)         

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        self.assertIn("Setting testNamePropertyNotSilent of testAgent1 to 11", output)  

        #Redirect the console output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout           

        agentSilent.set_property(name="testNamePropertySilent", type="String", value="12")

        self.assertEqual(agentSilent.properties["testNamePropertySilent"]["type"],"String")
        self.assertEqual(agentSilent.properties["testNamePropertySilent"]["value"],"12")         

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        self.assertNotIn("Setting testNamePropertySilent of testAgent2 to 12", output)  

if __name__ == '__main__':
    unittest.main()    