import unittest

from BPTK_Py import Event, Model, Agent
from BPTK_Py.modeling.datacollectors.csv_datacollector import CSVDataCollector

import os, shutil

class TestCSVDataCollector(unittest.TestCase):
    def setUp(self):
        pass

    def testCSVDataCollectorInit(self):
        csvDataCollector = CSVDataCollector(prefix="testDir")

        self.assertEqual(csvDataCollector.event_statistics,{})
        self.assertEqual(csvDataCollector.event_statistics,{})
        self.assertEqual(csvDataCollector.prefix,"testDir")
        self.assertIsNone(csvDataCollector.column_names)
        self.assertEqual(csvDataCollector.observed_ids,[])
        self.assertIsNone(csvDataCollector.headlines)
        self.assertEqual(csvDataCollector.cache,{})      

        #Cleanup the folder
        shutil.rmtree(csvDataCollector.prefix)          

    def testCSVDataCollector_record_event(self):
        csvDataCollector = CSVDataCollector(prefix="testDir")
        event= Event(name="eventName", sender_id=1, receiver_id=2)

        csvDataCollector.record_event(time=101,event=event)

        self.assertEqual(csvDataCollector.event_statistics,{101: {'eventName': 1}})   

        #Cleanup the folder
        shutil.rmtree(csvDataCollector.prefix)          

    def testCSVDataCollector_collect_agent_statistics(self):
        csvDataCollector = CSVDataCollector(prefix="testDir")  

        model = Model()
        agent = Agent(agent_id=101, model=model, properties={"name": {"type" : "String", "value": "agentName"}},agent_type="testAgent1")

        csvDataCollector.collect_agent_statistics(sim_time=1,agents=[agent])

        fileName = os.path.join(csvDataCollector.prefix,f"{agent.id}_{agent.agent_type}.csv")

        self.assertTrue(os.path.isfile(fileName))

        with open(fileName, "r") as file:
            lines = file.readlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0].strip(), "id;time;name")
            self.assertEqual(lines[1].strip(), f"{agent.id};1;{agent.properties['name']['value']}")

        self.assertEqual(csvDataCollector.observed_ids,[agent.id])

        #overwrite existing file

        csvDataCollector.collect_agent_statistics(sim_time=2,agents=[agent])

        self.assertTrue(os.path.isfile(fileName))

        with open(fileName, "r") as file:
            lines = file.readlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0].strip(), "id;time;name")
            self.assertEqual(lines[1].strip(), f"{agent.id};2;{agent.properties['name']['value']}")

        self.assertEqual(csvDataCollector.observed_ids,[agent.id])
    
        #Cleanup the folder
        shutil.rmtree(csvDataCollector.prefix)  

    def testCSVDataCollector_reset(self):
        csvDataCollector = CSVDataCollector(prefix="testDir")  

        model = Model()
        agent = Agent(agent_id=101, model=model, properties={"name": {"type" : "String", "value": "agentName"}},agent_type="testAgent1")

        csvDataCollector.collect_agent_statistics(sim_time=1,agents=[agent])

        event= Event(name="eventName", sender_id=1, receiver_id=2)

        csvDataCollector.record_event(time=101,event=event)        

        csvDataCollector.reset()

        self.assertEqual(csvDataCollector.agent_statistics,{})
        self.assertEqual(csvDataCollector.event_statistics,{})
        self.assertEqual(csvDataCollector.cache,{})
        self.assertEqual(csvDataCollector.observed_ids,[])

        #Cleanup the folder
        shutil.rmtree(csvDataCollector.prefix)  

    def testCSVDataCollector_statistics(self):
        csvDataCollector = CSVDataCollector(prefix="testDir")  

        self.assertEqual(csvDataCollector.statistics(),{})

        #Cleanup the folder
        shutil.rmtree(csvDataCollector.prefix)  

if __name__ == '__main__':
    unittest.main()