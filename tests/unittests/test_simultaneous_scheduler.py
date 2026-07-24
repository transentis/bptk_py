import unittest
from unittest import mock

from BPTK_Py import SimultaneousScheduler


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

    def _make_model(self, agents=None, events=None, data_collector=None,
                    starttime=0, stoptime=1, dt=1.0):
        model = mock.Mock()
        model.agents = list(agents or [])
        model.events = list(events or [])
        model.data_collector = data_collector
        model.starttime = starttime
        model.stoptime = stoptime
        model.dt = dt
        return model

    def test_run_resets_data_collector_and_initialises_progress_widget(self):
        """run() resets the data collector and primes a passed-in progress widget."""
        data_collector = mock.Mock()
        model = self._make_model(data_collector=data_collector)
        progress_widget = mock.Mock()
        progress_widget.value = -1

        scheduler = SimultaneousScheduler()
        scheduler.run(model, progress_widget=progress_widget, collect_data=False)

        data_collector.reset.assert_called_once()
        self.assertEqual(progress_widget.value, 1.0)
        self.assertEqual(scheduler.current_round, model.stoptime)

    def test_run_breaks_when_scheduler_stopped_between_rounds(self):
        """When self.running flips to False before a round, run() exits the outer loop."""
        model = self._make_model(stoptime=5)
        scheduler = SimultaneousScheduler()

        # Allow exactly one run_step invocation, then stop the scheduler. With the
        # default dt=1.0 there is a single step per round, so the outer break
        # fires on the next round before iterating through stoptime.
        run_step_calls = []
        original_run_step = scheduler.run_step

        def short_circuit(*args, **kwargs):
            run_step_calls.append(args)
            scheduler.running = False
            return original_run_step(*args, **kwargs)

        with mock.patch.object(scheduler, "run_step", side_effect=short_circuit):
            scheduler.run(model)

        self.assertEqual(len(run_step_calls), 1)

    def test_run_breaks_when_scheduler_stopped_between_steps(self):
        """When self.running flips to False mid-round, the inner step loop breaks."""
        # dt=0.5 -> round(1/dt) == 2 steps per round, so stopping after the first
        # step exercises the inner-loop break (which a single-step round can never
        # reach - the for loop simply ends).
        model = self._make_model(starttime=0, stoptime=1, dt=0.5)
        scheduler = SimultaneousScheduler()

        run_step_calls = []
        original_run_step = scheduler.run_step

        def short_circuit(*args, **kwargs):
            run_step_calls.append(args)
            scheduler.running = False  # stop after the first step of the round
            return original_run_step(*args, **kwargs)

        with mock.patch.object(scheduler, "run_step", side_effect=short_circuit):
            scheduler.run(model)

        # Only step 0 of the first round ran; step 1 was skipped via the inner break.
        self.assertEqual(len(run_step_calls), 1)
        self.assertEqual(run_step_calls[0][2], 0)  # positional arg: step == 0

    def test_run_step_updates_progress_widget(self):
        """run_step() copies its progress onto a passed-in widget."""
        model = self._make_model(stoptime=2)
        progress_widget = mock.Mock()
        progress_widget.value = -1

        scheduler = SimultaneousScheduler()
        scheduler.run_step(model, sim_round=1, step=0, progress_widget=progress_widget)

        self.assertEqual(progress_widget.value, scheduler.progress)
        self.assertGreater(progress_widget.value, 0)

    def test_run_step_dispatches_events_to_agents_and_records(self):
        """Events are delivered to the receiving agent and recorded by the data collector."""
        from BPTK_Py import Event

        agent0 = mock.Mock()
        agent1 = mock.Mock()
        event = Event(name="ping", sender_id=0, receiver_id=1, data=[42])

        data_collector = mock.Mock()
        model = self._make_model(agents=[agent0, agent1],
                                  events=[event],
                                  data_collector=data_collector)

        scheduler = SimultaneousScheduler()
        scheduler.run_step(model, sim_round=0, step=0)

        agent1.receive_event.assert_called_once_with(event)
        agent0.receive_event.assert_not_called()
        data_collector.record_event.assert_called_once_with(0.0, event)
        # Default collect_data=True—statistics collected every step.
        data_collector.collect_agent_statistics.assert_called_once()

if __name__ == '__main__':
    unittest.main()