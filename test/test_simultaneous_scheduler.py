import unittest

from BPTK_Py.abm.simultaneousScheduler import SimultaneousScheduler


class Test_SimultaneousScheduler(unittest.TestCase):
    def test_init(self):
        scheduler = SimultaneousScheduler()

        self.assertEqual(scheduler.current_time, 0)
        self.assertEqual(scheduler.current_round, 0)
        self.assertEqual(scheduler.current_step, 0)
        self.assertEqual(scheduler.progress, 0)
        self.assertEqual(scheduler.delayed_events, [])

    def test_handle_delayed_event(self):
        scheduler = SimultaneousScheduler()

        from BPTK_Py import Event, DelayedEvent
        event = Event(name="test", sender_id=1, receiver_id=0, data=[0])

        return_value = scheduler.handle_delayed_event(event, dt=1)

        self.assertEqual(event, return_value)
        self.assertEqual(id(event), id(return_value))
        self.assertEqual(scheduler.delayed_events, [])

        delayed_event = DelayedEvent(name="test", sender_id=1, receiver_id=0, data=[0], delay=1)

        return_value = scheduler.handle_delayed_event(delayed_event, dt=1)

        self.assertEqual(return_value, None)
        self.assertEqual(delayed_event, scheduler.delayed_events[0])
        self.assertEqual(delayed_event.delay, 0)

if __name__ == '__main__':
    unittest.main()