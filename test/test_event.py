import unittest

from BPTK_Py import Event, DelayedEvent

class TestEvent(unittest.TestCase):
    def setUp(self):
        pass

    def testSubclass(self):
        self.assertTrue(issubclass(DelayedEvent,Event))

    def testEventInit(self):
        self.assertEqual(Event(name="test", sender_id=1, receiver_id=0, data=[0]).name,"test")
        self.assertEqual(Event(name="test", sender_id=1, receiver_id=0, data=[0]).receiver_id, 0)
        self.assertEqual(Event(name="test", sender_id=1, receiver_id=0, data=[0]).sender_id, 1)

        self.assertRaises(ValueError,Event, name="test",sender_id="1",receiver_id=0,data=[0])
        self.assertRaises(ValueError, Event, name="test", sender_id="1", receiver_id="0", data=[0])
        self.assertRaises(ValueError, Event, name="test", sender_id=1, receiver_id="0", data=[0])

        self.assertRaises(ValueError, DelayedEvent, name="test", sender_id=1, receiver_id=0,delay="1", data=[0])

if __name__ == '__main__':
    unittest.main()
