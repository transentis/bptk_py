import unittest

from BPTK_Py import Model, Scheduler
from BPTK_Py.logger.logger import logfile

class Test_Scheduler(unittest.TestCase):
    def test_init(self):
        scheduler = Scheduler()

        self.assertEqual(scheduler.current_time,0)
        self.assertEqual(scheduler.current_round, 0)
        self.assertEqual(scheduler.current_step, 0)
        self.assertEqual(scheduler.progress, 0)
        self.assertEqual(scheduler.delayed_events, [])

    def test_run(self):
        model = Model()
        scheduler = Scheduler()

        scheduler.run(model=model)

        try:
            with open(logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] Scheduler.run should be overriden in a subclass", content)          

    def test_run_step(self):
        model = Model()
        scheduler = Scheduler()

        scheduler.run_step(model=model, sim_round=1, dt=1)

        try:
            with open(logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] Scheduler.run_step should be overriden in a subclass", content) 

    def test_handle_delayed_event(self):
        scheduler = Scheduler()

        from BPTK_Py import Event, DelayedEvent
        event = Event(name="test", sender_id=1, receiver_id=0, data=[0])

        return_value = scheduler.handle_delayed_event(event,dt=1)

        self.assertEqual(event,return_value)
        self.assertEqual(id(event),id(return_value))
        self.assertEqual(scheduler.delayed_events,[])

        delayed_event = DelayedEvent(name="test", sender_id=1, receiver_id=0, data=[0],delay=1)

        return_value = scheduler.handle_delayed_event(delayed_event, dt=1)

        self.assertEqual(return_value,None)
        self.assertEqual(delayed_event,scheduler.delayed_events[0])
        self.assertEqual(delayed_event.delay,0)


if __name__ == '__main__':
    unittest.main()
