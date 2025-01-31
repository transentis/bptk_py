import unittest

from BPTK_Py import Event, Agent, Model

from BPTK_Py import DataCollector


class TestDataCollector(unittest.TestCase):
    def setUp(self):
        pass

    def testDataCollectorInit(self):
        dataCollector = DataCollector()

        self.assertEqual(dataCollector.event_statistics,{})
        self.assertEqual(dataCollector.agent_statistics,{})

    def testDataCollector_record_event(self):
        dataCollector = DataCollector()
        event= Event(name="eventName", sender_id=1, receiver_id=2)

        dataCollector.record_event(time=101,event=event)

        self.assertEqual(dataCollector.event_statistics,{101: {'eventName': 1}})

    def testDataCollector_collect_agent_statistics(self):
        model = Model()
        dataCollector = DataCollector()

        agent1 = Agent(agent_id=1, model=model, properties={"property1" : { "type": "Double" , "value" : 10}}, agent_type="testAgent")
        agent2 = Agent(agent_id=2, model=model, properties={"property1" : { "type": "Double" , "value" : 20}}, agent_type="testAgent")
        agent3 = Agent(agent_id=3, model=model, properties={"property1" : { "type": "Double" , "value" : 30}}, agent_type="testAgent")
        agent3.state="inactive"
        agent4 = Agent(agent_id=4, model=model, properties={"property2" : { "type": "Double" , "value" : 45}}, agent_type="testAgent")

        dataCollector.collect_agent_statistics(agents=[agent1,agent2,agent3,agent4], time=1)

        print(dataCollector.agent_statistics)

        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["active"]["count"],3)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["active"]["property1"]["total"],30)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["active"]["property1"]["min"],10)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["active"]["property1"]["max"],20)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["active"]["property1"]["mean"],15)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["active"]["property2"]["total"],45)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["active"]["property2"]["min"],45)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["active"]["property2"]["max"],45)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["active"]["property2"]["mean"],15)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["inactive"]["count"],1)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["inactive"]["property1"]["total"],30)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["inactive"]["property1"]["min"],30)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["inactive"]["property1"]["max"],30)
        self.assertEqual(dataCollector.agent_statistics[1]["testAgent"]["inactive"]["property1"]["mean"],30)
     
if __name__ == '__main__':
    unittest.main()

