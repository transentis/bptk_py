"""Unit tests for BPTK_Py.widgets.agentstatuswidget.AgentStatusWidget.

Covers initialisation guards, button layout, start/stop lifecycle and the
threaded monitor_agents loop that maps agent states to button colours.
"""

import time
import unittest
from unittest import mock

import ipywidgets as widgets

from BPTK_Py.widgets.agentstatuswidget import AgentStatusWidget


def _make_agent(state):
    agent = mock.Mock()
    agent.state = state
    return agent


class TestAgentStatusWidgetInit(unittest.TestCase):
    def test_missing_agents_argument_raises_keyerror(self):
        with self.assertRaises(KeyError):
            AgentStatusWidget(states=[None, "INPROGRESS", "DONE"])

    def test_missing_states_argument_raises_keyerror(self):
        with self.assertRaises(KeyError):
            AgentStatusWidget(agents=[_make_agent("active")])

    def test_button_layout_wraps_into_rows_of_ten(self):
        agents = [_make_agent("active") for _ in range(12)]
        widget = AgentStatusWidget(agents=agents, states=[None, "INPROGRESS", "DONE"])

        self.assertEqual(len(widget.buttons), 12)
        self.assertIsInstance(widget.main_Vbox, widgets.VBox)
        rows = widget.main_Vbox.children
        # 12 buttons → two HBox rows: 10 in the first, 2 in the second.
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[0].children), 10)
        self.assertEqual(len(rows[1].children), 2)

    def test_initial_state_is_not_running(self):
        widget = AgentStatusWidget(agents=[_make_agent("idle")],
                                    states=[None, "y", "r"])

        self.assertFalse(widget.running)
        self.assertEqual(widget.buttons[0].button_style, "info")


class TestAgentStatusWidgetLifecycle(unittest.TestCase):
    def test_start_returns_vbox_and_starts_thread(self):
        agents = [_make_agent("active")]
        widget = AgentStatusWidget(agents=agents, states=[None, "y", "r"])

        try:
            returned = widget.start()
            self.assertIs(returned, widget.main_Vbox)
            self.assertTrue(widget.running)
            self.assertTrue(widget.thread.is_alive())
        finally:
            widget.stop()
            widget.thread.join(timeout=2)

    def test_stop_terminates_monitor_thread(self):
        widget = AgentStatusWidget(agents=[_make_agent("active")],
                                    states=[None, "y", "r"])

        widget.start()
        widget.stop()
        widget.thread.join(timeout=2)

        self.assertFalse(widget.running)
        self.assertFalse(widget.thread.is_alive())

    def test_monitor_agents_updates_button_styles(self):
        """The threaded monitor maps states[1]→warning and states[2]→danger."""
        agents = [_make_agent("INPROGRESS"), _make_agent("DONE"), _make_agent("OTHER")]
        widget = AgentStatusWidget(agents=agents, states=[None, "INPROGRESS", "DONE"])

        # Patch time.sleep inside the widget module so the monitor loop spins fast.
        with mock.patch("BPTK_Py.widgets.agentstatuswidget.time.sleep", return_value=None):
            widget.start()
            # Give the monitor thread a brief moment to iterate at least once.
            deadline = time.time() + 2.0
            while time.time() < deadline:
                if (widget.buttons[0].button_style == "warning"
                        and widget.buttons[1].button_style == "danger"):
                    break
                time.sleep(0.01)
            widget.stop()
            widget.thread.join(timeout=2)

        self.assertEqual(widget.buttons[0].button_style, "warning")
        self.assertEqual(widget.buttons[1].button_style, "danger")
        # Agent with a state that matches neither slot keeps the default colour.
        self.assertEqual(widget.buttons[2].button_style, "info")

    def test_monitor_agents_returns_none_when_stopped(self):
        widget = AgentStatusWidget(agents=[_make_agent("idle")],
                                    states=[None, "y", "r"])
        # Not running → monitor_agents should exit immediately and return None.
        widget.running = False
        self.assertIsNone(widget.monitor_agents())


if __name__ == "__main__":
    unittest.main()
