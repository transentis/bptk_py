import unittest

from BPTK_Py import Agent
from BPTK_Py import Model
from BPTK_Py.modeling.datacollectors.agent_datacollector import AgentDataCollector

class TestAgent(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()