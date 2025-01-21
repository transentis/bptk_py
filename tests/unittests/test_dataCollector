import unittest

from BPTK_Py import Event

from BPTK_Py import DataCollector


class TestAgent(unittest.TestCase):
    def setUp(self):
        pass

    def testDataCollectorInit(self):
        dataCollector = DataCollector()

        self.assertEqual(dataCollector.event_statistics,{})
        self.assertEqual(dataCollector.event_statistics,{})

    def testDataCollector_record_event(self):
        dataCollector = DataCollector()
        event= Event(name="eventName", sender_id=1, receiver_id=2)

        dataCollector.record_event(time=101,event=event)

        self.assertEqual(dataCollector.event_statistics,{101: {'eventName': 1}})
     
if __name__ == '__main__':
    unittest.main()

