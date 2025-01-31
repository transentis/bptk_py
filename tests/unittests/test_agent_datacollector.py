import unittest

from BPTK_Py import Agent
from BPTK_Py import Model
from BPTK_Py.modeling.datacollectors.agent_datacollector import AgentDataCollector
import pandas as pd

class TestAgentDataCollector(unittest.TestCase):
    def setUp(self):
        pass

    def testAgentDataCollectorInit(self):
        agentDataCollector = AgentDataCollector()

        self.assertEqual(agentDataCollector.event_statistics,{})
        self.assertEqual(agentDataCollector.event_statistics,{})

    def testAgentDataCollector_collect_agent_statistics(self):
        model = Model()
        agent = Agent(agent_id=101, model=model, properties={"name": {"type" : "Integer", "value": 121}},agent_type="testAgent1")

        agentDataCollector = AgentDataCollector()

        agentDataCollector.collect_agent_statistics(time=1, agents=[agent])

        self.assertEqual(agentDataCollector.agent_statistics,{'testAgent1': {101: {1: {'id': 101, 'time': 1, 'agent_state': 'active', 'agent_type': 'testAgent1', 'name': 121}}}})

    def testAgentDataCollector_get_agent_stats(self):
        model = Model()
        agent1 = Agent(agent_id=1001, model=model, properties={"agentName": {"type" : "String", "value": "testAgent1"}},agent_type="testAgentType1") 
        agent2 = Agent(agent_id=1002, model=model, properties={"agentName": {"type" : "String", "value": "testAgent2"}},agent_type="testAgentType1")   
        agent3 = Agent(agent_id=1003, model=model, properties={"agentName": {"type" : "String", "value": "testAgent3"}},agent_type="testAgentType2")

        agentDataCollector = AgentDataCollector()

        agentDataCollector.collect_agent_statistics(time=1, agents=[agent1,agent2,agent3])
        agentDataCollector.collect_agent_statistics(time=2, agents=[agent1])

        return_value = agentDataCollector.get_agent_stats()
        pd_columns = ["id","time","agent_state","agent_type"] 

        pd1_data = [
            [1001, 1, "active", "testAgentType1"],
            [1001, 2, "active", "testAgentType1"]
        ]
        self.assertTrue(return_value["testAgentType1"][1001].equals(pd.DataFrame(data=pd1_data, columns=pd_columns)))

        pd2_data = [[1002, 1, "active", "testAgentType1"]]
        self.assertTrue(return_value["testAgentType1"][1002].equals(pd.DataFrame(data=pd2_data, columns=pd_columns)))        

        pd3_data = [[1003, 1, "active", "testAgentType2"]]
        self.assertTrue(return_value["testAgentType2"][1003].equals(pd.DataFrame(data=pd3_data, columns=pd_columns)))    

    def testAgentDataCollector_plot_agent_stats(self):
        import matplotlib.pyplot as plt

        model = Model()
        agent1 = Agent(agent_id=1001, model=model, properties={"agentName": {"type" : "String", "value": "testAgent1"}},agent_type="testAgentType1") 
        agent2 = Agent(agent_id=1002, model=model, properties={"agentName": {"type" : "String", "value": "testAgent2"}},agent_type="testAgentType1")   
        agent3 = Agent(agent_id=1003, model=model, properties={"agentName": {"type" : "String", "value": "testAgent3"}},agent_type="testAgentType2")

        agentDataCollector = AgentDataCollector()

        agentDataCollector.collect_agent_statistics(time=1, agents=[agent1,agent2,agent3])
        agentDataCollector.collect_agent_statistics(time=2, agents=[agent1])

        result1 = agentDataCollector.plot_agent_stats(agent_ids=[1001,1002], properties=["time", "agent_state"], agent_type="testAgentType1")
        result2 = agentDataCollector.plot_agent_stats(agent_ids=[1003], properties=["time", "agent_state"], agent_type="testAgentType2")

        self.assertIsInstance(result1,plt.Axes)
        self.assertIsInstance(result2,plt.Axes)

if __name__ == '__main__':
    unittest.main()