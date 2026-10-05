import pytest
import io
import json
import os
import sys
import tempfile
import uuid
import unittest
from pathlib import Path
from unittest import mock

import BPTK_Py
import BPTK_Py.logger.logger as logmod
from BPTK_Py import bptk
from BPTK_Py import Agent, Model
from BPTK_Py.config import config as default_config
from BPTK_Py.scenariorunners import HybridRunner
from tests.helpers.log_helpers import clear_log, read_log


class _TrainingAgent(Agent):
    """Minimal agent used to exercise bptk.train_scenarios.

    Models a "learning" agent: each episode it accumulates ``rate`` per
    timestep into the property ``x``. ``begin_episode`` performs a soft reset
    of ``x`` (per-episode state) while ``end_episode`` bumps ``rate`` (the
    persistent, "learned" parameter). This produces a strictly increasing
    per-episode final value - i.e. a deterministic learning curve.
    """

    def __init__(self, agent_id, model, properties):
        super().__init__(agent_id=agent_id, model=model, properties=properties)
        self.agent_type = "learner"
        self.state = "active"
        self.rate = 1
        self.begin_episode_calls = []
        self.end_episode_calls = []
        self._initialize_properties()

    def _initialize_properties(self):
        self.set_property("x", {"type": "Double", "value": 0})

    def act(self, time, round_no, step_no):
        self.x += self.rate

    def begin_episode(self, episode_no):
        self.begin_episode_calls.append(episode_no)
        self.set_property_value("x", 0)  # soft reset of per-episode state

    def end_episode(self, episode_no):
        self.end_episode_calls.append(episode_no)
        self.rate += 1  # the "learned" parameter persists across episodes


class _TrainingModel(Model):
    def instantiate_model(self):
        self.register_agent_factory(
            "learner",
            lambda agent_id, model, properties: _TrainingAgent(agent_id, model, properties),
        )


class _ProgressRecorder:
    """Stands in for the tqdm-backed bar: the schedulers only write `value`."""

    def __init__(self):
        self.values = []

    @property
    def value(self):
        return self.values[-1] if self.values else 0

    @value.setter
    def value(self, value):
        self.values.append(value)

    def close(self):
        pass


def _build_two_scenario_training_bptk():
    """Two scenarios in one manager, so an episode has more than one step to show."""
    testBptk = bptk()
    model = _TrainingModel(name="trainingModel")
    scenario = {
        "runspecs": {"starttime": 1, "stoptime": 3, "dt": 1},
        "properties": {},
        "agents": [{"name": "learner", "count": 1}],
    }
    testBptk.register_scenario_manager({
        "trainManager": {"type": "abm", "model": model,
                         "scenarios": {"first": dict(scenario), "second": dict(scenario)}},
    })
    return testBptk


def _build_training_bptk():
    """Register a single-agent ABM scenario suitable for training."""
    testBptk = bptk()
    model = _TrainingModel(name="trainingModel")
    scenario_manager = {
        "trainManager": {
            "type": "abm",
            "model": model,
            "scenarios": {
                "trainScenario": {
                    "runspecs": {"starttime": 1, "stoptime": 10, "dt": 1},
                    "properties": {},
                    "agents": [{"name": "learner", "count": 1}],
                }
            },
        }
    }
    testBptk.register_scenario_manager(scenario_manager)
    return testBptk


class TestBptk(unittest.TestCase):
    def test_init_with_config(self):
        matplotlib_via_config = {
            "font.family": "Arial",
            "axes.titlesize": 36,
            "axes.labelsize": 26,
            "lines.linewidth": 4,
            "lines.markersize": 16,
            "xtick.labelsize": 16,
            "ytick.labelsize": 16,
            "figure.figsize": (21, 11),
            'legend.fontsize': 18,
        }     

        testbptk1 = bptk()
        self.assertEqual(testbptk1.config.matplotlib_rc_settings,default_config.matplotlib_rc_settings)
        self.assertEqual(testbptk1.config.configuration["matplotlib_rc_settings"],default_config.matplotlib_rc_settings)    

        testbptk2 = bptk(configuration={"matplotlib_rc_settings" : matplotlib_via_config})
        self.assertEqual(testbptk2.config.matplotlib_rc_settings,matplotlib_via_config)
        self.assertEqual(testbptk2.config.configuration["matplotlib_rc_settings"],matplotlib_via_config)
        self.assertEqual(testbptk2.config.loglevel,"WARN")        

        #cleanup logfile
        clear_log()

        testbptk3= bptk(loglevel="DEBUG")

        content = read_log()

        # It starts, so the message says so, and which level it uses
        self.assertIn("[ERROR] Invalid log level DEBUG, using WARN instead. Valid loglevels: ['INFO', 'WARN', 'ERROR']", content)
        self.assertEqual(testbptk3.config.loglevel, "WARN")

    def test_set_state(self):
        testbptk1 = bptk()
        testbptk2 = bptk()

        testbptk1._set_state(state={"testproperty" : "testValue"})
        testbptk2._set_state(state={"lock" : True})

        self.assertEqual(testbptk1.session_state["testproperty"],"testValue")
        self.assertFalse(testbptk1.session_state["lock"])
        self.assertTrue(testbptk2.session_state["lock"])

    def test_is_locked(self):
        testbptk1 = bptk()
        testbptk2 = bptk()
        testbptk2.session_state = {"testproperty" : "testValue"}
        testbptk3 = bptk()
        testbptk3._set_state(state={"lock" : True})

        self.assertFalse(testbptk1.is_locked())
        self.assertFalse(testbptk2.is_locked())
        self.assertTrue(testbptk3.is_locked())

    def test_train_scenario_invalid(self):
        #cleanup logfile
        clear_log()

        testBptk = bptk()

        self.assertIsNone(testBptk._train_scenarios(scenarios=["1"],scenario_managers=["firstManager"],agent_states=["active"]))
        self.assertIsNone(testBptk._train_scenarios(scenarios=["1"],scenario_managers=["firstManager"],agent_properties=["property"]))  
        self.assertIsNone(testBptk._train_scenarios(scenarios=["1"],scenario_managers=["firstManager"],agent_properties=["property"],agent_property_types=[],agents=["agent"]))
        self.assertIsNone(testBptk._train_scenarios(scenarios=["1"],scenario_managers=["firstManager"],agent_properties=[],agent_property_types=["property_type"],agents=["agent"]))
        # No offending combination, just nothing to train: this is the call that reaches
        # the "No agents given" check. It used to be reached by the four above as well,
        # because their guards ended in a `sys.exit` that does nothing.
        self.assertIsNone(testBptk._train_scenarios(scenarios=["1"],scenario_managers=["firstManager"]))

        content = read_log()

        self.assertIn("[ERROR] You may only use the agent_states parameter if you also set the agents parameter!", content)     
        self.assertIn("[ERROR] You may only use the agent_properties parameter if you also set the agents parameter!", content)  
        self.assertIn("[ERROR] No agents given, aborting!", content)  
        self.assertIn("[ERROR] You must set the relevant property types if you specify an agent_property!", content)  
        self.assertIn("[ERROR] You may only use the agent_property_types parameter if you also set the agent_properties parameter!", content)  

    def _sd_session_bptk(self):
        """A bptk with one SD scenario manager, enough to begin a session on."""
        testBptk = bptk()
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="sessionModel")
        stock = model.stock("stock")
        stock.initial_value = 1.0
        stock.equation = model.converter("rate")
        model.converter("rate").equation = 1.0
        testBptk.register_scenario_manager({"smSession": {"model": model}})
        testBptk.register_scenarios(scenarios={"base": {}}, scenario_manager="smSession")
        return testBptk

    def _progress_through(self, starttime, stoptime):
        testBptk = bptk()
        model = Model(starttime=starttime, stoptime=stoptime, dt=1.0, name="progressModel")
        stock = model.stock("stock")
        stock.initial_value = 1.0
        stock.equation = 1.0
        testBptk.register_scenario_manager({"smProgress": {"model": model}})
        testBptk.register_scenarios(scenarios={"base": {}}, scenario_manager="smProgress")
        testBptk.begin_session(scenarios=["base"], scenario_managers=["smProgress"], equations=["stock"])

        seen = [testBptk.progress()]
        while testBptk.progress() < 1.0:
            testBptk.run_step()
            seen.append(testBptk.progress())
        testBptk.end_session()
        return seen

    def test_progress_counts_the_steps_of_the_session(self):
        """progress() used to divide the step by the stop time: a session from 10 to 20
        started at 50 %, and one that stops at 0 divided by zero."""
        self.assertEqual(self._progress_through(0.0, 3.0), [0.0, 0.25, 0.5, 0.75, 1.0])

        from_ten = self._progress_through(10.0, 20.0)
        self.assertEqual(from_ten[0], 0.0)
        self.assertEqual(len(from_ten), 12)  # eleven steps, 10 to 20
        self.assertEqual(from_ten[-1], 1.0)

        self.assertEqual(self._progress_through(0.0, 0.0), [0.0, 1.0])

    def test_begin_session_reports_an_unknown_scenario_manager(self):
        """A typo in a manager name used to start a session that carried nothing.

        run_scenarios has reported this since 3.0.0, with a suggestion. A session that
        swallows it is worse: the caller steps a session that will never produce the
        scenario they asked for, and nothing ever says why.
        """
        clear_log()
        testBptk = self._sd_session_bptk()

        testBptk.begin_session(scenarios=["base"], scenario_managers=["smSessio"],
                               equations=["stock"])

        content = read_log()
        self.assertIn('begin_session: scenario manager "smSessio" not found!', content)
        self.assertIn("smSession", content)
        testBptk.destroy()

    def test_begin_session_reports_an_unknown_scenario(self):
        clear_log()
        testBptk = self._sd_session_bptk()

        testBptk.begin_session(scenarios=["bse"], scenario_managers=["smSession"],
                               equations=["stock"])

        content = read_log()
        self.assertIn('begin_session: scenario "bse" not found', content)
        self.assertIn("base", content)
        testBptk.destroy()

    def test_begin_session_stays_quiet_when_every_name_matches(self):
        """The guard must not report the ordinary case."""
        clear_log()
        testBptk = self._sd_session_bptk()

        testBptk.begin_session(scenarios=["base"], scenario_managers=["smSession"],
                               equations=["stock"])

        content = read_log()
        self.assertNotIn("begin_session: scenario", content)
        self.assertNotIn("No simulation model containing", content)
        testBptk.destroy()

    def test_begin_session_refuses_an_agent_based_manager(self):
        """Sessions are SD-only, and used to say so by crashing.

        The cache asks every scenario for its memo grid, which an agent-based model has
        no equivalent of, so the call died on
        `AttributeError: _TrainingModel._get_cache is invalid` several frames down. The
        branch in run_step that prints "run_step currently only supports SD scenarios"
        was unreachable for the same reason: no such session ever began.
        """
        clear_log()
        testBptk = _build_training_bptk()

        result = testBptk.begin_session(scenarios=["trainScenario"],
                                        scenario_managers=["trainManager"],
                                        equations=["x"])

        self.assertIsNone(result)
        self.assertIsNone(testBptk.session_state)
        content = read_log()
        self.assertIn("sessions support System Dynamics scenarios only", content)
        self.assertIn("trainManager", content)
        testBptk.destroy()

    def test_version_tuple_stops_at_a_non_numeric_component(self):
        """`2.5.0rc1` cuts at the suffix; a component with no digits at all ends the tuple.

        The `break` was the one line of `_version_tuple` no test reached, and it is the
        one that decides what happens to a version string nobody planned for.

        The strings are arbitrary and deliberately not this package's version: it is the
        parser under test, and nothing here should have to be touched at a release.
        """
        self.assertEqual(bptk._version_tuple("1.2.3"), (1, 2, 3))
        self.assertEqual(bptk._version_tuple("2.5.0rc1"), (2, 5, 0))
        self.assertEqual(bptk._version_tuple("3.0.dev0"), (3, 0))
        self.assertEqual(bptk._version_tuple("dev"), ())

    def test_logfire_import_error_is_not_swallowed(self):
        """Asking for Logfire without the extra has to say so.

        Every other failure while configuring it is logged and the run continues; an
        ImportError is re-raised, because silence would look like success.
        """
        from unittest.mock import patch
        import BPTK_Py.logger.logger as logmod

        configuration = {"logfire_config": {"service_name": "test"}}

        with patch.object(logmod, "configure_logfire", side_effect=ImportError("no logfire")):
            with self.assertRaises(ImportError):
                bptk(configuration=configuration)

        with patch.object(logmod, "configure_logfire", side_effect=RuntimeError("boom")):
            testBptk = bptk(configuration=configuration)   # logged, not raised
            testBptk.destroy()

    def test_train_scenarios_without_a_matching_manager(self):
        """Agents that belong to no registered manager produce no dataframes at all."""
        testBptk = _build_training_bptk()

        result = testBptk.train_scenarios(
            scenarios=["trainScenario"],
            scenario_managers=["noSuchManager"],
            episodes=1,
            agents=["learner"],
            return_df=True,
        )

        self.assertIsNone(result)
        testBptk.destroy()

    def test_begin_session_reports_a_name_with_nothing_to_suggest(self):
        """The other half of the didyoumean branch: no candidates at all.

        `didyoumean` offers the nearest name however far it is, so the plain message
        only appears when nothing is registered to compare against - which is exactly
        the case where a reader most needs to be told the name matched nothing.
        """
        clear_log()
        testBptk = bptk()

        testBptk.begin_session(scenarios=["zzzzzzzz"], scenario_managers=["qqqqqqqq"],
                               equations=["stock"])

        content = read_log()
        self.assertIn('begin_session: scenario manager "qqqqqqqq" not found!', content)
        self.assertIn('begin_session: scenario "zzzzzzzz" not found', content)
        self.assertNotIn("Did you maybe mean", content)
        testBptk.destroy()

    def test_begin_session_errors(self):
        clear_log()

        testBptk = bptk()

        self.assertIsNone(testBptk.begin_session(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"]))
        self.assertIsNone(testBptk.begin_session(scenarios=["1","2","3"],scenario_managers=[],equations=["stock"]))

        content = read_log()

        self.assertIn("[ERROR] begin_session: No equations to simulate given! Aborting!", content)
        self.assertIn("[ERROR] Did not find any of the scenario manager(s) you specified. Maybe you made a typo or did not store the model in the scenarios folder? Scenario folder:", content)

    def test_begin_session_takes_no_agent_arguments(self):
        """Sessions run System Dynamics only; the agent parameters they used to accept
        were checked against each other and then never used."""
        testBptk = bptk()
        for argument in ("agents", "agent_states", "agent_properties", "agent_property_types",
                         "individual_agent_properties"):
            with self.assertRaises(TypeError):
                testBptk.begin_session(scenarios=["1"], scenario_managers=["firstManager"],
                                       equations=["stock"], **{argument: ["x"]})

    def test_run_step(self):
        testBptk = bptk()

        self.assertIsNone(testBptk.run_step())     

        from BPTK_Py import Model
        model = Model(starttime=0.0,stoptime=1.0,dt=1.0,name='test')
        stock = model.stock("stock")     
        stock.equation = 1.0
        flow = model.flow("flow")
        flow.equation= 2.0
        scenario_manager = {"testManager": {"model": model}}

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager)
        testBptk.register_scenarios(scenarios ={"testScenario": {}},scenario_manager="testManager")

        testBptk.begin_session(scenarios=["testScenario"],scenario_managers=["testManager"],equations=["stock"])
        self.assertNotEqual(testBptk.run_step(),{"msg":"Stoptime reached"}) #step 0
        self.assertNotEqual(testBptk.run_step(),{"msg":"Stoptime reached"}) #step 1
        self.assertEqual(testBptk.run_step(),{"msg":"Stoptime reached"}) #step 2

        testBptk2 = bptk()
        testBptk2.register_model(model)
        testBptk2.register_scenario_manager(scenario_manager)
        testBptk2.register_scenarios(scenarios ={"testScenario": {}},scenario_manager="testManager")

        testBptk2.begin_session(scenarios=["testScenario"],scenario_managers=["testManager"],equations=["stock","flow"])
        self.assertEqual(testBptk2.run_step(flat=False),{'testManager': {'testScenario': {'stock': {0.0: 0.0}, 'flow': {0.0: 2.0}}}})
        self.assertEqual(testBptk2.run_step(flat=True),{'testManager': {'testScenario': {'stock': 1.0, 'flow': 2.0}}})

    def test_run_step_delay_looks_back_at_the_value_set_at_that_step(self):
        """A constant overridden per step used to lose its history and collapse the delay.

        `delay` at step t asks its input for step t-2. A constant set per step used to be
        a `lambda t: value` that ignores t, so the lookback read the value set last and
        the order arrived the moment it was placed. Only `incoming` is requested, which
        is what keeps the input from being evaluated - and memoised - at its own step.
        """
        from BPTK_Py.sddsl import functions as sd

        model = Model(starttime=1.0, stoptime=6.0, dt=1.0, name="delay")
        orders = model.constant("orders")
        orders.equation = 8.0
        incoming = model.flow("incoming")
        incoming.equation = sd.delay(model, orders, 2.0, 8.0)

        testBptk = bptk()
        testBptk.register_scenario_manager({"mgr": {"model": model}})
        testBptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
        testBptk.begin_session(scenario_managers=["mgr"], scenarios=["base"],
                               equations=["incoming"], backend="python")

        placed = [8.0, 8.0, 8.0, 20.0, 20.0, 20.0]
        arrived = {}
        try:
            for value in placed:
                step = testBptk.run_step(
                    settings={"mgr": {"base": {"constants": {"orders": value}}}})
                for t, v in step["mgr"]["base"]["incoming"].items():
                    arrived[float(t)] = v
        finally:
            testBptk.end_session()

        # Two steps of lag: the jump to 20 is placed at t=4 and arrives at t=6
        self.assertEqual(
            arrived,
            {1.0: 8.0, 2.0: 8.0, 3.0: 8.0, 4.0: 8.0, 5.0: 8.0, 6.0: 20.0})

    def test_run_step_delay_looks_back_past_a_lost_simulation(self):
        """A simulation created mid-session gets the overrides of the steps it missed.

        That is a session restored into a fresh process, and a session the Rust engine
        handed over after a mid-run failure. Both arrive with no history at all, so a
        delay reaching back across the handover used to read the model's own constant
        instead of what was set at that step. The overrides are in the session's
        settings log; the runner replays them into the new simulation.
        """
        from BPTK_Py.sddsl import functions as sd

        model = Model(starttime=1.0, stoptime=6.0, dt=1.0, name="delay_resume")
        orders = model.constant("orders")
        orders.equation = 8.0
        incoming = model.flow("incoming")
        incoming.equation = sd.delay(model, orders, 2.0, 8.0)

        testBptk = bptk()
        testBptk.register_scenario_manager({"mgr": {"model": model}})
        testBptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
        testBptk.begin_session(scenario_managers=["mgr"], scenarios=["base"],
                               equations=["incoming"], backend="python")

        # The last order differs from the one that is due to arrive, so a delay that
        # reads the value set last is caught as surely as one that lost the history
        placed = [8.0, 8.0, 8.0, 20.0, 20.0, 12.0]
        arrived = {}
        try:
            for index, value in enumerate(placed):
                if index == 5:
                    # Everything the process was holding is gone: the simulation object
                    # and the memo with it. The last step has to look back to step 4,
                    # which is on the far side of the loss.
                    scenario = testBptk.scenario_manager_factory.scenario_managers["mgr"].scenarios["base"]
                    scenario.sd_simulation = None
                    testBptk.reset_scenario_cache(scenario_manager="mgr", scenario="base")
                step = testBptk.run_step(
                    settings={"mgr": {"base": {"constants": {"orders": value}}}})
                for t, v in step["mgr"]["base"]["incoming"].items():
                    arrived[float(t)] = v
        finally:
            testBptk.end_session()

        # Placed at step 4, arrives at step 6 - across the loss
        self.assertEqual(arrived[6.0], 20.0)

    @staticmethod
    def _column_name_bptk(manager):
        model = Model(starttime=1.0, stoptime=3.0, dt=1.0, name="columns")
        headcount = model.stock("headcount")
        headcount.initial_value = 10.0
        hiring = model.flow("hiring")
        hiring.equation = 1.0
        headcount.equation = hiring

        testBptk = bptk()
        testBptk.register_scenario_manager({manager: {"model": model}})
        testBptk.register_scenarios(scenarios={"base": {}, "freeze": {}},
                                    scenario_manager=manager)
        return testBptk

    def test_run_scenarios_column_names_do_not_depend_on_earlier_runs(self):
        """A run for one scenario used to rename a later run's column.

        With a single manager and a single scenario the columns are handed back under
        their bare equation name, which is a convenience - and the rule that does it was
        written into `series_names`, a dict default. A dict default belongs to the
        function rather than to the call, so the rule outlived the call and every
        `bptk()` in the process: a later run for two scenarios came back with one column
        bare and the other prefixed.
        """
        first = self._column_name_bptk("shared_manager")
        one = first.run_scenarios(scenario_managers=["shared_manager"],
                                  scenarios=["base"], equations=["headcount"],
                                  return_format="df")
        # The convenience itself, which the fix must not remove
        assert list(one.columns) == ["headcount"]

        second = self._column_name_bptk("shared_manager")
        both = second.run_scenarios(scenario_managers=["shared_manager"],
                                    scenarios=["base", "freeze"],
                                    equations=["headcount"], return_format="df")

        assert sorted(both.columns) == ["shared_manager_base_headcount",
                                        "shared_manager_freeze_headcount"]

    def test_plot_scenarios_column_names_do_not_depend_on_earlier_plots(self):
        """The same leak through the other door: `plot_scenarios` carried its own dict."""
        import matplotlib
        matplotlib.use("Agg")

        first = self._column_name_bptk("plotted_manager")
        one = first.plot_scenarios(scenario_managers=["plotted_manager"],
                                   scenarios=["base"], equations=["headcount"],
                                   return_df=True)
        assert list(one.columns) == ["headcount"]

        second = self._column_name_bptk("plotted_manager")
        both = second.plot_scenarios(scenario_managers=["plotted_manager"],
                                     scenarios=["base", "freeze"],
                                     equations=["headcount"], return_df=True)

        assert sorted(both.columns) == ["plotted_manager_base_headcount",
                                        "plotted_manager_freeze_headcount"]

    def _build_simple_step_bptk(self, configuration=None):
        """Helper: builds a minimal stock/flow bptk for backend-handling tests.

        Pass ``configuration`` to exercise instance-level config such as
        ``{"default_backend": "rust"}``."""
        from BPTK_Py import Model
        testBptk = bptk(configuration=configuration) if configuration else bptk()
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="rustBackendTest")
        stock = model.stock("stock")
        flow = model.flow("flow")
        constant = model.constant("constant")
        stock.initial_value = 0.0
        stock.equation = flow
        flow.equation = constant
        constant.equation = 1.0
        testBptk.register_model(model)
        testBptk.register_scenario_manager({"testManager": {"model": model}})
        testBptk.register_scenarios(scenarios={"testScenario": {}},
                                    scenario_manager="testManager")
        return testBptk

    def test_begin_session_backend_default_is_python(self):
        """When backend is not specified, session_state must record python."""
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"])
        self.assertEqual(testBptk.session_state["backend"], "python")
        testBptk.end_session()

    def test_begin_session_backend_explicit_python(self):
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend="python")
        self.assertEqual(testBptk.session_state["backend"], "python")
        testBptk.end_session()

    def test_begin_session_backend_explicit_rust(self):
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend="rust")
        self.assertEqual(testBptk.session_state["backend"], "rust")
        testBptk.end_session()

    def test_begin_session_backend_invalid_falls_back(self):
        """Invalid backend strings must log an [ERROR] and fall back to python."""
        clear_log()

        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend="bogus")
        self.assertEqual(testBptk.session_state["backend"], "python")

        content = read_log()
        self.assertIn("[ERROR] begin_session: invalid backend 'bogus'", content)
        testBptk.end_session()

    def test_begin_session_backend_none_uses_default(self):
        """backend=None (the default) resolves to the instance default_backend,
        which is 'python' for an unconfigured instance."""
        testBptk = self._build_simple_step_bptk()
        self.assertEqual(testBptk.default_backend, "python")
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend=None)
        self.assertEqual(testBptk.session_state["backend"], "python")
        testBptk.end_session()

    def test_default_backend_rust_used_when_backend_omitted(self):
        """A bptk configured with default_backend='rust' runs sessions
        on Rust when begin_session omits the backend argument; an explicit backend
        still overrides the instance default."""
        testBptk = self._build_simple_step_bptk(
            configuration={"default_backend": "rust"})
        self.assertEqual(testBptk.default_backend, "rust")

        # Omitted backend ⇒ inherits the 'rust' instance default.
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"])
        self.assertEqual(testBptk.session_state["backend"], "rust")
        testBptk.end_session()

        # Explicit 'python' overrides the 'rust' instance default.
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend="python")
        self.assertEqual(testBptk.session_state["backend"], "python")
        testBptk.end_session()

    @pytest.mark.requires_rust
    def test_default_backend_reaches_run_and_plot_scenarios(self):
        """Every method that takes a backend uses the instance default unless given one.
        run_scenarios and plot_scenarios used to stay on 'python' regardless."""
        from BPTK_Py.scenariorunners.sd_runner import SdRunner
        testBptk = self._build_simple_step_bptk(
            configuration={"default_backend": "rust"})
        call = dict(scenarios=["testScenario"], scenario_managers=["testManager"], equations=["stock"])

        with mock.patch.object(SdRunner, "run_scenario", autospec=True,
                               side_effect=SdRunner.run_scenario) as run:
            testBptk.run_scenarios(**call)
            testBptk.plot_scenarios(return_df=True, **call)
            testBptk.run_scenarios(backend="python", **call)

        self.assertEqual([c.kwargs["backend"] for c in run.call_args_list], ["rust", "rust", "python"])

    def test_default_backend_invalid_config_falls_back(self):
        """An invalid default_backend in the configuration logs an [ERROR] and
        leaves the instance default at 'python'."""
        testBptk = self._build_simple_step_bptk(
            configuration={"default_backend": "bogus"})
        self.assertEqual(testBptk.default_backend, "python")

    @pytest.mark.requires_rust
    def test_end_session_clears_rust_state(self):
        """After end_session, the Rust fields populated mid-session must all be reset
        on the underlying SimulationScenario."""
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock", "flow"], backend="rust")
        testBptk.run_step()

        sc = testBptk.scenario_manager_factory.get_scenario(
            scenario_manager="testManager", scenario="testScenario")
        # Sanity: mid-session, the Rust state is populated.
        self.assertIsNotNone(sc.rust_model)
        self.assertIsNotNone(sc._rust_initial)
        self.assertTrue(sc._rust_initial_returned)

        testBptk.end_session()

        self.assertIsNone(sc.rust_model)
        self.assertIsNone(sc._rust_initial)
        self.assertFalse(sc._rust_initial_returned)
        self.assertIsNone(testBptk.session_state)

    def test_end_session_python_session_no_rust_state(self):
        """A python-backed session must never populate the Rust fields, and
        end_session must leave them at their defaults."""
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend="python")
        testBptk.run_step()
        sc = testBptk.scenario_manager_factory.get_scenario(
            scenario_manager="testManager", scenario="testScenario")
        self.assertIsNone(sc.rust_model)
        self.assertIsNotNone(sc.sd_simulation)

        testBptk.end_session()

        self.assertIsNone(sc.rust_model)
        self.assertFalse(sc._rust_initial_returned)

    @pytest.mark.requires_rust
    def test_end_session_reset_exception_logged(self):
        """If rust_model.reset() raises, end_session must still complete, leave the
        scenario in a clean state and say what failed. The real RustSdModel.reset() is a
        Rust-defined attribute and can't be monkeypatched, so we swap the
        rust_model handle out for a MagicMock whose reset() raises."""
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"], backend="rust")
        testBptk.run_step()
        sc = testBptk.scenario_manager_factory.get_scenario(
            scenario_manager="testManager", scenario="testScenario")

        # Replace the real Rust handle with a MagicMock whose reset() raises.
        sc.rust_model = mock.MagicMock()
        sc.rust_model.reset.side_effect = RuntimeError("simulated boom")

        clear_log()
        testBptk.end_session()  # must not raise

        self.assertIsNone(sc.rust_model)
        self.assertIsNone(testBptk.session_state)
        self.assertIn("releasing the Rust state of testScenario failed: simulated boom", read_log())

    @pytest.mark.requires_rust
    def test_run_step_passes_backend_to_runner(self):
        """run_step must forward session_state['backend'] to SdRunner.run_scenario_step."""
        from BPTK_Py.scenariorunners.sd_runner import SdRunner
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock", "flow"], backend="rust")
        with mock.patch.object(SdRunner, "run_scenario_step",
                               wraps=SdRunner.run_scenario_step,
                               autospec=True) as mock_run:
            testBptk.run_step()
            self.assertTrue(mock_run.called)
            self.assertEqual(mock_run.call_args.kwargs["backend"], "rust")
        testBptk.end_session()

    def test_run_step_defaults_to_python_when_backend_missing(self):
        """Sessions reconstructed from external state may not carry the
        'backend' key; run_step must default to python rather than KeyError."""
        from BPTK_Py.scenariorunners.sd_runner import SdRunner
        testBptk = self._build_simple_step_bptk()
        testBptk.begin_session(scenarios=["testScenario"],
                               scenario_managers=["testManager"],
                               equations=["stock"])
        del testBptk.session_state["backend"]

        with mock.patch.object(SdRunner, "run_scenario_step",
                               wraps=SdRunner.run_scenario_step,
                               autospec=True) as mock_run:
            testBptk.run_step()
            self.assertEqual(mock_run.call_args.kwargs["backend"], "python")
        testBptk.end_session()

    def test_session_results(self):
        testBptk = bptk()

        self.assertEqual(testBptk.session_results(),{})   

        from BPTK_Py import Model
        model = Model(starttime=0.0,stoptime=15.0,dt=1.0,name='Portfolio')
        totalValue = model.stock("totalValue")
        interest = model.flow("interest")
        deposit = model.flow("deposit")
        interestRate = model.constant("interestRate")
        depositRate = model.constant("depositRate")
        initialValue = model.constant("initialValue")
        interestRate.equation = 0.05
        depositRate.equation = 1000.0
        initialValue.equation = 1000
        totalValue.initial_value = initialValue
        interest.equation = interestRate * totalValue
        deposit.equation = depositRate
        totalValue.equation = interest + deposit 

        scenario_manager = {
            "smPortfolio":{
            "model": model,
            "base_constants": {
                "totalValue": 1000.0,
                "interestRate": 0.05,
                "depositRate": 1000.0
                }
            }
        }          

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager)
        testBptk.register_scenarios(
            scenarios ={
                "base": {
                    },
                "scenarrioLowInterest": {
                    "constants": {
                        "interestRate": 0.01
                        }
                    }
            },
            scenario_manager="smPortfolio")        

        testBptk.begin_session(scenarios=["base","scenarrioLowInterest"],scenario_managers=["smPortfolio"],equations=["totalValue","interest"])
        testBptk.run_step()
        testBptk.run_step()
        self.assertEqual(testBptk.session_results(),testBptk.session_state["results_log"])

        result1= testBptk.session_results(index_by_time=False)
        result2= testBptk.session_results(index_by_time=False, flat=True)

        self.assertEqual(result1["smPortfolio"]["base"]["equations"]["totalValue"][0.0],1000)
        self.assertEqual(result1["smPortfolio"]["base"]["equations"]["totalValue"][1.0],2050)
        self.assertEqual(result1["smPortfolio"]["base"]["equations"]["interest"][0.0],50)
        self.assertEqual(result1["smPortfolio"]["base"]["equations"]["interest"][1.0],102.5)
        self.assertEqual(result1["smPortfolio"]["scenarrioLowInterest"]["equations"]["totalValue"][0.0],1000)
        self.assertEqual(result1["smPortfolio"]["scenarrioLowInterest"]["equations"]["totalValue"][1.0],2010)
        self.assertEqual(result1["smPortfolio"]["scenarrioLowInterest"]["equations"]["interest"][0.0],10)
        self.assertEqual(result1["smPortfolio"]["scenarrioLowInterest"]["equations"]["interest"][1.0],20.1)

        self.assertEqual(result2["smPortfolio"]["base"]["equations"]["totalValue"],[1000,2050])
        self.assertEqual(result2["smPortfolio"]["base"]["equations"]["interest"],[50,102.5])
        self.assertEqual(result2["smPortfolio"]["scenarrioLowInterest"]["equations"]["totalValue"],[1000,2010])
        self.assertEqual(result2["smPortfolio"]["scenarrioLowInterest"]["equations"]["interest"],[10,20.1])

    def test_run_scenarios_invalid(self):
        #cleanup logfile
        clear_log()

        testBptk = bptk()

        self.assertIsNone(testBptk.run_scenarios(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"]))
        self.assertIsNone(testBptk.run_scenarios(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],agent_states=["active"]))
        self.assertIsNone(testBptk.run_scenarios(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],agent_properties=["property"]))
        self.assertIsNone(testBptk.run_scenarios(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],agent_properties=["property"],agents=["agent1"]))
        self.assertIsNone(testBptk.run_scenarios(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock"],agent_property_types=["type"]))
        self.assertIsNone(testBptk.run_scenarios(scenarios=["1","2","3"],scenario_managers=[],equations=["stock"],agents=["agent1"]))        
        self.assertIsNone(testBptk.run_scenarios(scenarios=["1"], scenario_managers=["firstManager"],equations=["stock"]))

        content = read_log()

        self.assertIn("[ERROR] Neither any agents nor equations to simulate given! Aborting!", content) 
        self.assertIn("[ERROR] You may only use the agent_states parameter if you also set the agents parameter!", content)     
        self.assertIn("[ERROR] You may only use the agent_properties parameter if you also set the agents parameter!", content)  
        self.assertIn("[ERROR] You must set the relevant property types if you specify an agent_property!", content)  
        self.assertIn("[ERROR] You may only use the agent_property_types parameter if you also set the agent_properties parameter!", content)  
        self.assertIn("[ERROR] Did not find any of the scenario manager(s) you specified. Maybe you made a typo or did not store the model in the scenarios folder? Scenario folder:", content)  
        self.assertIn("[ERROR] Scenario manager \"firstManager\" not found!", content)  
        self.assertIn("[ERROR] Scenario \"1\" not found in any scenario manager!", content)  

        from BPTK_Py import Model
        model = Model(starttime=0.0,stoptime=15.0,dt=1.0,name='test')
        stock = model.stock("stock")     
        stock.equation = 1.0
        scenario_manager = {"testManager":{"model": model}}

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager)
        testBptk.register_scenarios(scenarios ={"base": {}},scenario_manager="testManager")

        self.assertIsNone(testBptk.run_scenarios(scenarios=["base"], scenario_managers=["testManage"],equations=["stock"]))
        self.assertIsNone(testBptk.run_scenarios(scenarios=["bas"], scenario_managers=["testManager"],equations=["stock"]))

        content = read_log()

        self.assertIn("[ERROR] Scenario manager \"testManage\" not found! Did you maybe mean one of \"testManager", content) 
        self.assertIn("[ERROR] Scenario \"bas\" not found in any scenario manager! Did you maybe mean one of \"base\"?", content) 

    def test_plot_lookup(self):
        from BPTK_Py import Model
        from BPTK_Py import sd_functions as sd
        model = Model(starttime=0.0,stoptime=5.0,dt=1.0,name='test')     
        model.points["testpoints"] = [
            [0, 0.1],
            [0.2, 0.2],
            [0.4, 0.3],
            [0.6, 0.4],
            [0.8, 0.5],
            [1, 0.6]
        ]

        scenario_manager = {"testManager": {"model": model}}

        testBptk = bptk()

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager)
        testBptk.register_scenarios(scenarios ={"testScenario": {"points": {"testpoints" : [[0,0.2],[0.2,0.4],[0.4,0.6],[0.6,0.8],[0.8,1.0],[1,1.2]]}}},scenario_manager="testManager")

        data = {
            "smTest_base_testpoints": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            "testManager_testScenario_testpoints": [0.2, 0.4, 0.6, 0.8, 1.0, 1.2]
        } 

        result = testBptk.plot_lookup(scenarios=["base","testScenario"],scenario_managers=["smTest","testManager"], lookup_names="testpoints",return_df=True)

        import pandas as pd
        self.assertTrue(result.equals(pd.DataFrame(data=data, index=[0.0,0.2,0.4,0.6,0.8,1.0])))

    def test_register_scenarios_error(self):
        #cleanup logfile
        clear_log()

        testBptk = bptk()  

        testBptk.register_scenarios(scenarios={},scenario_manager="testScenarioManager")

        content = read_log()

        self.assertIn("[ERROR] Scenario manager not found. Did you register it?", content) 

    def test_list_scenarios(self):
        from BPTK_Py import Model
        model = Model(starttime=0.0,stoptime=15.0,dt=1.0,name='test')
        stock = model.stock("stock")     
        stock.equation = 1.0
        scenario_manager1 = {"testManager1": {"model": model, "type": "type1"}}
        scenario_manager2 = {"testManager2": {"model": model, "type": "type2"}}

        testBptk = bptk()

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager1)
        testBptk.register_scenario_manager(scenario_manager2)
        testBptk.register_scenarios(scenarios ={"scenario11": {}, "scenario12": {}},scenario_manager="testManager1")
        testBptk.register_scenarios(scenarios ={"scenario21": {}, "scenario22": {}},scenario_manager="testManager2")

        #Redirect the console output
        import sys, io
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        testBptk.list_scenarios()
        output = new_stdout.getvalue()
        new_stdout.truncate(0)  # reset stdout
        new_stdout.seek(0)
        self.assertIn("*** smTest ***", output)
        self.assertIn("base", output)
        self.assertIn("*** testManager1 ***", output)
        self.assertIn("scenario11", output)
        self.assertIn("scenario12", output)
        self.assertIn("*** testManager2 ***", output)
        self.assertIn("scenario21", output)
        self.assertIn("scenario22", output)

        testBptk.list_scenarios(scenario_managers=["testManager1"])
        output = new_stdout.getvalue()
        self.assertNotIn("*** smTest ***", output)
        self.assertNotIn("base", output)
        self.assertIn("*** testManager1 ***", output)
        self.assertIn("*** testManager1 ***", output)
        self.assertIn("scenario11", output)
        self.assertIn("scenario12", output)
        self.assertNotIn("*** testManager2 ***", output)
        self.assertNotIn("scenario21", output)
        self.assertNotIn("scenario22", output)

        #Remove the redirection of the console output
        sys.stdout = old_stdout

    def test_get_scenario_names_empty(self):
        testBptk = bptk()  

        self.assertEqual(testBptk.get_scenario_names(format="invalid"),[])

    def test_get_scenarios(self):
        from BPTK_Py import Model
        model = Model(starttime=0.0,stoptime=15.0,dt=1.0,name='test')
        stock = model.stock("stock")     
        stock.equation = 1.0
        scenario_manager1 = {"testManager1": {"model": model, "type": "type1"}}
        scenario_manager2 = {"testManager2": {"model": model, "type": "type2"}}

        testBptk = bptk()

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager1)
        testBptk.register_scenario_manager(scenario_manager2)
        testBptk.register_scenarios(scenarios ={"scenario11": {}, "scenario12": {}},scenario_manager="testManager1")
        testBptk.register_scenarios(scenarios ={"scenario21": {}, "scenario22": {}},scenario_manager="testManager2")

        result=testBptk.get_scenarios()    

        from BPTK_Py.scenariomanager.scenario import SimulationScenario
        self.assertIsInstance(result["smTest_base"],SimulationScenario)    
        self.assertIsInstance(result["testManager1_scenario11"],SimulationScenario)    
        self.assertIsInstance(result["testManager1_scenario12"],SimulationScenario)    
        self.assertIsInstance(result["testManager2_scenario21"],SimulationScenario)    
        self.assertIsInstance(result["testManager2_scenario22"],SimulationScenario)    

    def test_get_scenarios_leaves_the_callers_list_alone(self):
        """The list passed in used to grow: ["base"] came back as ["base", "base"] with
        one manager, and with two it gained "mgr_base" and "other_base"."""
        from BPTK_Py import Model
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="list")
        model.converter("c").equation = 1.0
        testBptk = bptk()
        for manager in ("mgr", "other"):
            testBptk.register_scenario_manager({manager: {"model": model}})
            testBptk.register_scenarios(scenarios={"base": {}}, scenario_manager=manager)

        for managers, expected in ((["mgr"], ["base"]), (["mgr", "other"], ["mgr_base", "other_base"])):
            mine = ["base"]
            result = testBptk.get_scenarios(scenario_managers=managers, scenarios=mine)
            self.assertEqual(mine, ["base"])
            self.assertEqual(sorted(result), expected)

    def test_list_equations_prints_each_kind_once(self):
        """Two flows must not print the converters twice.

        Until 3.0.2 the converter and constant loops sat inside the flow loop, so the
        list came out multiplied by the number of flows - on a model with a handful of
        flows the output was unreadable and looked like the model had duplicates.
        """
        from BPTK_Py import Model
        import io
        from contextlib import redirect_stdout

        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="two_flows")
        model.stock("s").equation = 1.0
        model.flow("f1").equation = 1.0
        model.flow("f2").equation = 1.0
        model.converter("c").equation = 1.0
        model.constant("k").equation = 1.0

        testBptk = bptk()
        testBptk.register_scenario_manager({"sm": {"model": model}})
        testBptk.register_scenarios(scenarios={"base": {}}, scenario_manager="sm")

        captured = io.StringIO()
        with redirect_stdout(captured):
            testBptk.list_equations(scenario_managers=["sm"])
        output_text = captured.getvalue()

        self.assertEqual(output_text.count("\tconverter: \t\tc"), 1)
        self.assertEqual(output_text.count("\tconstant: \t\tk"), 1)
        self.assertEqual(output_text.count("\tflow: \t\t\tf1"), 1)
        self.assertEqual(output_text.count("\tflow: \t\t\tf2"), 1)

    def test_list_equations(self):
        from BPTK_Py import Model
        model = Model(starttime=0.0,stoptime=15.0,dt=1.0,name='test')
        stock = model.stock("testStock")     
        stock.equation = 1.0
        flow = model.flow("testFlow")
        flow.equation = 2.0
        converter = model.converter("testConverter")
        converter.equation = 3.0
        constant = model.constant("testConstant")
        constant.equation = 4.0

        scenario_manager = {"testManager": {"model": model}}
        testBptk = bptk()
        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager)       
        testBptk.register_scenarios(scenarios ={"testScenario": {}},scenario_manager="testManager")

        #Redirect the console output
        import sys, io
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        testBptk.list_equations(scenario_managers=["smTest"])
        output = new_stdout.getvalue()
        new_stdout.truncate(0)  # reset stdout
        new_stdout.seek(0)
        self.assertIn("Available Equations", output)
        self.assertIn("Scenario Manager: smTest", output)
        self.assertIn("Scenario: base", output)
        self.assertIn("\tstock: \t\t\ttestStock", output)
        self.assertIn("\tflow: \t\t\ttestFlow", output)
        self.assertIn("\tconverter: \t\ttestConverter", output)
        self.assertIn("\tconstant: \t\ttestConstant", output)
        self.assertNotIn("Scenario Manager: testManager", output)        
        self.assertNotIn("Scenario: testScenario", output)

        testBptk.list_equations(scenario_managers= [], scenarios=["testScenario"])
        output = new_stdout.getvalue()
        self.assertIn("Available Equations", output)
        self.assertIn("Scenario Manager: smTest", output)
        self.assertNotIn("Scenario: base", output)
        self.assertIn("Scenario Manager: testManager", output)
        self.assertIn("Scenario: testScenario", output)
        self.assertIn("\tstock: \t\t\ttestStock", output)
        self.assertIn("\tflow: \t\t\ttestFlow", output)
        self.assertIn("\tconverter: \t\ttestConverter", output)
        self.assertIn("\tconstant: \t\ttestConstant", output)

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

    def _capture_stdout(self, fn, *args, **kwargs):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            fn(*args, **kwargs)
            return sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

    def test_version_is_resolved(self):
        """BPTK_Py.__version__ resolves to a real version string, not the 'UNAVAILABLE' fallback."""
        from importlib.metadata import PackageNotFoundError, version as _installed
        try:
            _installed("BPTK-Py")
        except PackageNotFoundError:
            self.skipTest("BPTK-Py is on sys.path as a source checkout, not installed as a "
                          "distribution, so there is no metadata to resolve")

        self.assertNotEqual(BPTK_Py.__version__, "UNAVAILABLE")
        # Version must be a dotted numeric string.
        from importlib.metadata import version as _version
        self.assertRegex(BPTK_Py.__version__, r"^\d+(\.\d+)*")
        self.assertEqual(BPTK_Py.__version__, _version("BPTK-Py"))

    # --- bptk.update() ------------------------------------------------------
    # update() reads PyPI's JSON API. Until 2.4.1 it used distlib's XML-RPC
    # search, which PyPI switched off years ago - so the method could only ever
    # raise. The old tests mocked distlib's PackageIndex and therefore never
    # noticed; testBptk_update_network_error is the regression guard for that.

    @staticmethod
    def _fake_pypi_response(version):
        """A stand-in for urlopen's context manager, serving one JSON payload."""
        payload = json.dumps({"info": {"name": "bptk-py", "version": version}})
        response = mock.MagicMock()
        response.__enter__.return_value = io.StringIO(payload)
        return response

    def test_version_tuple(self):
        """Versions compare numerically, and a non-numeric suffix truncates."""
        self.assertEqual(bptk._version_tuple("2.4.1"), (2, 4, 1))
        self.assertEqual(bptk._version_tuple("2.5.0rc1"), (2, 5, 0))
        self.assertLess(bptk._version_tuple("2.4.1"), bptk._version_tuple("2.10.0"))
        self.assertLess(bptk._version_tuple("2.4.1"), bptk._version_tuple("2.4.2"))
        self.assertFalse(bptk._version_tuple("2.4.1") < bptk._version_tuple("2.4.1"))

    def test_update_already_latest(self):
        """update() prints 'up to date' when the local version matches PyPI."""
        with mock.patch("urllib.request.urlopen",
                        return_value=self._fake_pypi_response(BPTK_Py.__version__)):
            output = self._capture_stdout(bptk.update)

        self.assertIn("Nothing to do", output)
        self.assertIn(BPTK_Py.__version__, output)

    def test_update_installs_newer_version_terminal(self):
        """update() pip-installs when PyPI advertises a newer version (terminal flow)."""
        with mock.patch("urllib.request.urlopen",
                        return_value=self._fake_pypi_response("999.0.0")), \
             mock.patch.object(BPTK_Py, "__version__", "1.0.0"), \
             mock.patch("subprocess.check_call", return_value=0) as check_call, \
             mock.patch("builtins.get_ipython", create=True, side_effect=NameError):
            output = self._capture_stdout(bptk.update)

        self.assertIn("Update successfully completed", output)
        self.assertNotIn("Jupyter Notebook", output)
        check_call.assert_called_once()
        self.assertIn("BPTK-Py", check_call.call_args[0][0])

    def test_update_pip_failure(self):
        """update() reports an error when pip exits non-zero."""
        with mock.patch("urllib.request.urlopen",
                        return_value=self._fake_pypi_response("999.0.0")), \
             mock.patch.object(BPTK_Py, "__version__", "1.0.0"), \
             mock.patch("subprocess.check_call", return_value=1), \
             mock.patch("builtins.get_ipython", create=True, side_effect=NameError):
            output = self._capture_stdout(bptk.update)

        self.assertIn("Error Updating", output)

    def test_update_network_error(self):
        """A PyPI that cannot be reached is reported, not raised.

        This is what the distlib version did wrong: PyPI's XML-RPC search
        answers with a Fault, which escaped to the caller.
        """
        import urllib.error

        with mock.patch("urllib.request.urlopen",
                        side_effect=urllib.error.URLError("no route to host")):
            output = self._capture_stdout(bptk.update)

        self.assertIn("Could not reach", output)
        self.assertNotIn("Nothing to do", output)

    def _run_update_with_shell(self, shell_name):
        fake_shell = mock.Mock()
        fake_shell.__class__.__name__ = shell_name
        with mock.patch("urllib.request.urlopen",
                        return_value=self._fake_pypi_response("999.0.0")), \
             mock.patch.object(BPTK_Py, "__version__", "1.0.0"), \
             mock.patch("subprocess.check_call", return_value=0), \
             mock.patch("builtins.get_ipython", create=True, return_value=fake_shell):
            return self._capture_stdout(bptk.update)

    def test_update_notebook_hint(self):
        """isnotebook() returns True for a ZMQInteractiveShell - the kernel hint appears."""
        output = self._run_update_with_shell("ZMQInteractiveShell")
        self.assertIn("Update successfully completed", output)
        self.assertIn("Jupyter Notebook", output)

    def test_update_terminal_shell(self):
        """isnotebook() returns False for a TerminalInteractiveShell - no notebook hint."""
        output = self._run_update_with_shell("TerminalInteractiveShell")
        self.assertIn("Update successfully completed", output)
        self.assertNotIn("Jupyter Notebook", output)

    def test_update_other_shell(self):
        """isnotebook() returns False for any other shell class - no notebook hint."""
        output = self._run_update_with_shell("SomeOtherShell")
        self.assertIn("Update successfully completed", output)
        self.assertNotIn("Jupyter Notebook", output)

    def test_export_scenarios(self):
        from BPTK_Py import Model
        from BPTK_Py import sd_functions as sd
        model = Model(starttime=0.0,stoptime=3.0,dt=1.0,name='test')
        x = model.flow("x")
        testFunction1 = model.function("2times", lambda model, t: 2*(t+1))
        x.equation = testFunction1()
        y = model.flow("y")
        testFunction2 = model.function("3times", lambda model, t: 3*(t+1))
        y.equation = testFunction2()
        
        stock1 = model.stock("stock1")
        initialValue_stock1 = model.constant("initialValue_stock1")
        initialValue_stock1.equation = 1.0
        stock1.initial_value = initialValue_stock1
        stock1.equation = x

        stock2 = model.stock("stock2")
        initialValue_stock2 = model.constant("initialValue_stock2")
        initialValue_stock2.equation = 2.0
        stock2.initial_value = initialValue_stock2
        stock2.equation = y     

        testBptk = bptk()   

        scenario_manager = {
            "testmanager":{
            "model": model,
            "base_constants": {
                "initialValue_stock1": 1.0,
                "initialValue_stock2": 2.0
                }
            }
        }          

        testBptk.register_model(model)
        testBptk.register_scenario_manager(scenario_manager)
        testBptk.register_scenarios(
            scenarios ={
                "highStock1": {
                    "constants": {
                        "initialValue_stock1": 10.0
                    }
                },
                "highStock2": {
                    "constants": {
                        "initialValue_stock2": 20.0
                    }
                },
                "VeryHighStock1": {
                    "constants": {
                        "initialValue_stock1": 100.0
                    }
                },                                
            },
            scenario_manager="testmanager")        

        result1 = testBptk.export_scenarios(scenario_manager="testmanager", scenarios=["highStock1","highStock2"], equations=["stock1","stock2"])
        result2 = testBptk.export_scenarios(scenario_manager="testmanager", scenarios=["highStock1","highStock2"], equations=["stock1","stock2"],
                                        interactive_scenario= "VeryHighStock1",
                                        interactive_equations=["stock1"],
                                        interactive_settings={})
        data_scenario = {
            "stock1": [10.0, 12.0, 16.0, 22.0, 1.0, 3.0, 7.0, 13.0],
            "stock2": [2.0, 5.0, 11.0, 20.0, 20.0, 23.0, 29.0, 38.0],
            "scenario": ["highStock1", "highStock1", "highStock1", "highStock1","highStock2", "highStock2", "highStock2", "highStock2"],
            "time": [0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0]
        }

        data_indicator = {
            "highStock1": [10.0, 12.0, 16.0, 22.0, 2.0, 5.0, 11.0, 20.0],
            "highStock2": [1.0, 3.0, 7.0, 13.0, 20.0, 23.0, 29.0, 38.0],
            "indicator": ["stock1", "stock1", "stock1", "stock1","stock2", "stock2", "stock2", "stock2"],
            "time": [0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0]            
        }

        data_interactive = {
            "stock1" : [100.0, 102.0, 106.0, 112.0],
            "time" : [0.0, 1.0, 2.0, 3.0]
        }

        import pandas as pd
        self.assertTrue(result1["scenario"].equals(pd.DataFrame(data=data_scenario)))
        self.assertTrue(result1["indicator"].equals(pd.DataFrame(data=data_indicator)))
        self.assertTrue(result1["interactive"].equals(pd.DataFrame()))
        self.assertTrue(result2["interactive"].equals(pd.DataFrame(data=data_interactive)))

    def test_train_scenarios_learning_curve(self):
        """train_scenarios runs an ABM over episodes and returns one row per
        episode holding the episode's final value (collect_data=False path)."""
        import pandas as pd

        testBptk = _build_training_bptk()
        episodes = 3

        df = testBptk.train_scenarios(
            scenarios=["trainScenario"],
            scenario_managers=["trainManager"],
            episodes=episodes,
            agents=["learner"],
            agent_states=["active"],
            agent_properties=["x"],
            agent_property_types=["total"],
            return_df=True,
        )

        self.assertIsInstance(df, pd.DataFrame)
        # one row per episode
        self.assertEqual(len(df), episodes)

        column_name = "learner_active_x_total"
        self.assertIn(column_name, df.columns)

        # rate is 1, 2, 3 across the three episodes; over 10 timesteps the
        # per-episode final value is 10, 20, 30 - a strictly rising curve.
        #
        # These three values alone prove both episode hooks fired correctly:
        #  - if begin_episode had NOT soft-reset x, it would accumulate across
        #    episodes (ep1 -> 30 instead of 20);
        #  - if end_episode had NOT bumped rate, every episode would yield 10.
        self.assertEqual(list(df[column_name]), [10.0, 20.0, 30.0])

        testBptk.destroy()

    def test_train_scenarios_takes_comma_strings(self):
        """agent_properties and agent_property_types were passed on unsplit, so a
        string was read character by character."""
        testBptk = _build_training_bptk()

        df = testBptk.train_scenarios(
            scenarios="trainScenario", scenario_managers="trainManager", episodes=3,
            agents="learner", agent_states="active", agent_properties="x",
            agent_property_types="total", return_df=True,
        )

        self.assertEqual(list(df["learner_active_x_total"]), [10.0, 20.0, 30.0])
        testBptk.destroy()

    def test_train_scenarios_with_a_progress_bar_returns_the_result(self):
        """The progress bar used to put the training in a thread, whose result was lost:
        train_scenarios returned None."""
        testBptk = _build_training_bptk()

        df = testBptk.train_scenarios(
            scenarios=["trainScenario"],
            scenario_managers=["trainManager"],
            episodes=3,
            agents=["learner"],
            agent_states=["active"],
            agent_properties=["x"],
            agent_property_types=["total"],
            return_df=True,
            progress_bar=True,
        )

        self.assertEqual(list(df["learner_active_x_total"]), [10.0, 20.0, 30.0])

        testBptk.destroy()

    def test_train_scenarios_with_a_progress_bar_raises_to_the_caller(self):
        testBptk = _build_training_bptk()

        with mock.patch.object(testBptk, "_train_scenarios", side_effect=RuntimeError("training failed")), \
                mock.patch("BPTK_Py.util.ProgressBar") as progress_bar:
            with self.assertRaisesRegex(RuntimeError, "training failed"):
                testBptk.train_scenarios(scenarios=["trainScenario"], scenario_managers=["trainManager"],
                                         return_df=True, progress_bar=True)

        # The bar is closed on the way out, error or not
        progress_bar.return_value.close.assert_called_once()

        testBptk.destroy()

    def test_list_parameters_given_as_comma_strings(self):
        """Every list parameter also takes a comma string. agents used to be the
        exception: it was iterated letter by letter, which ended in a KeyError about
        something else. The coverage report cannot show this - each split is a one-line
        conditional, counted as covered whichever branch ran."""
        # Agent-based: every agent parameter as a string
        testBptk = _build_training_bptk()
        as_list = testBptk.run_scenarios(
            scenario_managers=["trainManager"], scenarios=["trainScenario"], agents=["learner"],
            agent_states=["active"], agent_properties=["x"], agent_property_types=["total"])
        as_string = testBptk.run_scenarios(
            scenario_managers="trainManager", scenarios="trainScenario", agents="learner",
            agent_states="active", agent_properties="x", agent_property_types="total")
        self.assertEqual(list(as_string.columns), list(as_list.columns))
        testBptk.destroy()

        # System Dynamics: two equations in one string
        sdBptk = self._sd_session_bptk()
        df = sdBptk.run_scenarios(scenario_managers="smSession", scenarios="base", equations="stock,rate")
        self.assertEqual(sorted(df.columns), ["rate", "stock"])

        # A session keeps lists, whatever it was given. Sessions are System Dynamics only.
        sdBptk.begin_session(scenario_managers="smSession", scenarios="base", equations="stock,rate")
        self.assertEqual(sdBptk.session_state["scenario_managers"], ["smSession"])
        self.assertEqual(sdBptk.session_state["scenarios"], ["base"])
        self.assertEqual(sdBptk.session_state["equations"], ["stock", "rate"])

    def test_run_scenarios_agents_without_agent_states(self):
        """Naming an agent but no states must return that agent's states, not crash.

        `get_stats_for` put a plain `0` into the per-timestep output when no state was
        named, and the loop right below it asked that output for `.items()`. So the
        most ordinary ABM call there is - plot an agent - raised
        `AttributeError: 'int' object has no attribute 'items'`. Naming no state now
        means all of them.
        """
        import pandas as pd

        testBptk = _build_training_bptk()

        df = testBptk.run_scenarios(
            scenario_managers=["trainManager"],
            scenarios=["trainScenario"],
            agents=["learner"],
        )

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(list(df.columns), ["trainManager_trainScenario_learner_active"])
        self.assertEqual(df.iloc[0].iloc[0], 1)
        testBptk.destroy()

    def test_run_scenarios_agents_with_and_without_states_agree(self):
        """Asking for the only state the agent has is the same as asking for none."""
        without = _build_training_bptk().run_scenarios(
            scenario_managers=["trainManager"], scenarios=["trainScenario"],
            agents=["learner"])
        with_state = _build_training_bptk().run_scenarios(
            scenario_managers=["trainManager"], scenarios=["trainScenario"],
            agents=["learner"], agent_states=["active"])

        self.assertTrue(without.equals(with_state))

    def test_train_scenarios_invalid_arguments_stop_before_training(self):
        """The four argument guards used to log and then train anyway.

        Each ended in `sys.exit` without parentheses - an expression with no effect. The
        test above could not see it: it asserted `None`, and `None` came back either
        way. What has to be asserted is that the run does not happen.
        """
        from unittest.mock import patch
        from BPTK_Py.scenariorunners.hybrid_runner import HybridRunner

        testBptk = _build_training_bptk()

        with patch.object(HybridRunner, "train_scenario") as trainer:
            result = testBptk.train_scenarios(
                scenarios=["trainScenario"],
                scenario_managers=["trainManager"],
                episodes=2,
                agents=["learner"],
                agent_properties=["x"],
                agent_property_types=[],
                return_df=True,
            )

        self.assertIsNone(result)
        trainer.assert_not_called()
        testBptk.destroy()

    def test_train_scenarios_no_agents_returns_none(self):
        """Without agents there is nothing to train, so None is returned."""
        testBptk = _build_training_bptk()

        result = testBptk.train_scenarios(
            scenarios=["trainScenario"],
            scenario_managers=["trainManager"],
            episodes=2,
            agents=[],
            return_df=True,
        )

        self.assertIsNone(result)
        testBptk.destroy()

    def test_train_scenarios_accepts_comma_separated_strings(self):
        """Scenario/manager/agent args may be passed as comma-separated strings."""
        import pandas as pd

        testBptk = _build_training_bptk()

        df = testBptk.train_scenarios(
            scenarios="trainScenario",
            scenario_managers="trainManager",
            episodes=1,
            agents="learner",
            agent_states=["active"],
            agent_properties=["x"],
            agent_property_types=["total"],
            return_df=True,
        )

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        column_name = "learner_active_x_total"
        self.assertEqual(list(df[column_name]), [10.0])
        testBptk.destroy()

    def test_train_scenarios_multiple_managers_join(self):
        """Training across two managers joins their per-episode result frames."""
        import pandas as pd

        testBptk = _build_training_bptk()
        # register a second, independent ABM manager
        testBptk.register_scenario_manager({
            "trainManager2": {
                "type": "abm",
                "model": _TrainingModel(name="trainingModel2"),
                "scenarios": {
                    "trainScenario": {
                        "runspecs": {"starttime": 1, "stoptime": 10, "dt": 1},
                        "properties": {},
                        "agents": [{"name": "learner", "count": 1}],
                    }
                },
            }
        })

        df = testBptk.train_scenarios(
            scenarios=["trainScenario"],
            scenario_managers=["trainManager", "trainManager2"],
            episodes=2,
            agents=["learner"],
            agent_states=["active"],
            agent_properties=["x"],
            agent_property_types=["total"],
            return_df=True,
        )

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)  # two episodes
        # with two managers the series names keep their full prefix
        col1 = "trainManager_trainScenario_learner_active_x_total"
        col2 = "trainManager2_trainScenario_learner_active_x_total"
        self.assertIn(col1, df.columns)
        self.assertIn(col2, df.columns)
        self.assertEqual(list(df[col1]), [10.0, 20.0])
        self.assertEqual(list(df[col2]), [10.0, 20.0])
        testBptk.destroy()


    # ------------------------------------------------------------------
    # bptk.py coverage: config, isnotebook shell branches, init branches,
    # progress-bar training, lookup/reset/register/export.
    # ------------------------------------------------------------------

    def test_conf_preserves_slider_layout(self):
        """A non-None slider_layout survives the deepcopy (it is popped and restored)."""
        from BPTK_Py.bptk import conf
        from BPTK_Py.config import config as default_config
        sentinel = {"widget": "layout"}
        default_config.configuration["slider_layout"] = sentinel
        try:
            self.assertEqual(conf().configuration["slider_layout"], sentinel)
        finally:
            default_config.configuration.pop("slider_layout", None)

    def test_init_configures_logfire(self):
        """A logfire_config dict triggers configure_logfire during init."""
        import BPTK_Py.logger.logger as logmod2
        with mock.patch.object(logmod2, "configure_logfire", return_value=True) as cfg:
            bptk(configuration={"logfire_config": {"token": "x"}})
        cfg.assert_called_once()

    def test_init_logfire_failure_is_caught(self):
        """A failure while configuring logfire is caught, not raised."""
        import BPTK_Py.logger.logger as logmod2
        with mock.patch.object(logmod2, "configure_logfire", side_effect=RuntimeError("boom")):
            testBptk = bptk(configuration={"logfire_config": {"token": "x"}})
        self.assertIsNotNone(testBptk)

    def test_init_appends_scenario_base_path_to_syspath(self):
        """The parent of the scenario storage path is added to sys.path if absent."""
        import sys, tempfile, os
        from pathlib import Path
        tmp = tempfile.TemporaryDirectory()
        storage = os.path.join(tmp.name, "myproject", "scenarios")
        os.makedirs(storage)
        # bptk resolves the path first, so compare against the resolved parent.
        base_path = str(Path(storage).resolve().parent)  # .../myproject
        self.assertNotIn(base_path, sys.path)
        try:
            bptk(configuration={"scenario_storage": storage})
            self.assertIn(base_path, sys.path)
        finally:
            if base_path in sys.path:
                sys.path.remove(base_path)
            tmp.cleanup()

    def test_plot_lookup_single_scenario(self):
        """plot_lookup with a single lookup source hits the single-dataframe branch."""
        from BPTK_Py import Model
        import pandas as pd
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="lk")
        model.points["testpoints"] = [[0, 0.1], [1, 0.6]]
        testBptk = bptk()
        testBptk.register_scenario_manager({"lkManager": {"model": model}})
        testBptk.register_scenarios(scenarios={"base": {}}, scenario_manager="lkManager")

        result = testBptk.plot_lookup(scenarios=["base"], scenario_managers=["lkManager"],
                                      lookup_names="testpoints", return_df=True)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result.columns), 1)

    def test_plot_scenarios_without_data_returns_none(self):
        """A run that produced nothing must not reach the visualizer.

        run_scenarios() returns None when no scenario matched, and passing that
        on raised `'NoneType' object has no attribute 'columns'` - a traceback on
        a documentation page where the reason was already in the log.
        """
        testBptk = bptk()
        with mock.patch.object(testBptk, "run_scenarios", return_value=None):
            with mock.patch.object(testBptk.visualizer, "plot") as plot:
                result = testBptk.plot_scenarios(scenarios=["nope"], scenario_managers=["nope"])
        self.assertIsNone(result)
        plot.assert_not_called()

    @pytest.mark.requires_extra("plotting")
    def test_plot_lookup_format_axes(self):
        """format="axes" hands the Axes back, as plot_scenarios() already did."""
        import matplotlib.axes
        from BPTK_Py import Model
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="lk")
        model.points["testpoints"] = [[0, 0.1], [1, 0.6]]
        testBptk = bptk()
        testBptk.register_scenario_manager({"lkManager": {"model": model}})
        testBptk.register_scenarios(scenarios={"base": {}}, scenario_manager="lkManager")

        ax = testBptk.plot_lookup(scenarios=["base"], scenario_managers=["lkManager"],
                                  lookup_names="testpoints", format="axes")

        self.assertIsInstance(ax, matplotlib.axes.Axes)

    def test_reset_scenario_delegates_to_factory(self):
        """reset_scenario and reset_all_scenarios delegate to the factory."""
        testBptk = bptk()
        with mock.patch.object(testBptk.scenario_manager_factory, "reset_scenario") as reset_one:
            testBptk.reset_scenario(scenario_manager="m", scenario="s")
        reset_one.assert_called_once_with(scenario_manager="m", scenario="s")

        with mock.patch.object(testBptk.scenario_manager_factory, "reset_all_scenarios") as reset_all:
            testBptk.reset_all_scenarios()
        reset_all.assert_called_once()

    def test_register_model_from_source_path(self):
        """register_model with a filesystem path registers a manager pointing at that source."""
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix=".itmx", delete=False)
        tmp.write(b"<xmile></xmile>")
        tmp.close()
        try:
            testBptk = bptk()
            # Stub register_scenarios so we don't XMILE-compile the dummy source;
            # we only care that the path branch registers the manager + prints.
            with mock.patch.object(testBptk, "register_scenarios"):
                output = self._capture_stdout(
                    testBptk.register_model, tmp.name, "SourcedManager")
            self.assertIn("Successfully registered", output)
            self.assertIn("SourcedManager", testBptk.scenario_manager_factory.scenario_managers)
        finally:
            os.unlink(tmp.name)

    def test_export_scenarios_defaults_interactive_and_file(self):
        """export_scenarios: default (all) scenarios, non-empty interactive settings,
        and writing to a spreadsheet file."""
        from BPTK_Py import Model
        import tempfile, os
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="exp")
        stock = model.stock("stock")
        rate = model.constant("rate")
        rate.equation = 1.0
        stock.initial_value = 0.0
        stock.equation = rate

        testBptk = bptk()
        testBptk.register_scenario_manager({"expManager": {"model": model, "base_constants": {"rate": 1.0}}})
        testBptk.register_scenarios(
            scenarios={"base": {}, "fast": {"constants": {"rate": 2.0}}},
            scenario_manager="expManager")

        # No `scenarios` argument -> all scenario names are looked up.
        result = testBptk.export_scenarios(scenario_manager="expManager", equations=["stock"])
        self.assertIn("scenario", result)

        # Non-empty interactive settings exercise the per-setting property assignment.
        result_i = testBptk.export_scenarios(
            scenario_manager="expManager", scenarios=["base"], equations=["stock"],
            interactive_scenario="base", interactive_equations=["stock"],
            interactive_settings={"rate": [1.0, 3.0, 1.0]})
        self.assertFalse(result_i["interactive"].empty)
        self.assertIn("rate", result_i["interactive"].columns)

        # A filename triggers the spreadsheet-export branch (openpyxl is not a
        # dependency here, so the writer and to_excel are stubbed out).
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.close()
        try:
            with mock.patch("pandas.ExcelWriter"), mock.patch("pandas.DataFrame.to_excel"):
                ret = testBptk.export_scenarios(scenario_manager="expManager", scenarios=["base"],
                                                equations=["stock"], filename=tmp.name)
            self.assertIsNone(ret)
        finally:
            os.unlink(tmp.name)

        # time_column_name names the time column in all three tables
        renamed = testBptk.export_scenarios(
            scenario_manager="expManager", equations=["stock"], time_column_name="t",
            interactive_scenario="base", interactive_equations=["stock"],
            interactive_settings={"rate": [1.0, 2.0, 1.0]})
        for table in ("scenario", "indicator", "interactive"):
            self.assertIn("t", renamed[table].columns, table)
            self.assertNotIn("time", renamed[table].columns, table)

        # Without equations there is nothing to export: say so, rather than failing inside
        with self.assertRaisesRegex(ValueError, "needs the equations"):
            testBptk.export_scenarios(scenario_manager="expManager")

    def test_register_model_from_source_requires_name(self):
        """register_model from a path without a manager name logs an error and aborts."""
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix=".itmx", delete=False)
        tmp.close()
        try:
            clear_log()
            testBptk = bptk()
            testBptk.register_model(tmp.name)  # no scenario_manager name
            content = read_log()
            self.assertIn("[ERROR] Please define a name for the new scenario manager", content)
        finally:
            os.unlink(tmp.name)

    def test_register_scenario_manager_twice_changes_nothing(self):
        """A second registration under the same name is a no-op, not a partial one.

        It used to drop the model but still merge the scenarios from the same
        dictionary, so a scenario added in that call ran against the model the caller
        had just replaced - and the log said "Successfully registered" right after
        saying the model was ignored.
        """
        model_first = Model(starttime=0.0, stoptime=1.0, dt=1.0, name="first")
        stock = model_first.stock("stock")
        stock.initial_value = 0.0
        stock.equation = model_first.constant("rate")
        model_first.constant("rate").equation = 1.0

        model_second = Model(starttime=0.0, stoptime=1.0, dt=1.0, name="second")
        stock2 = model_second.stock("stock")
        stock2.initial_value = 0.0
        stock2.equation = model_second.constant("rate")
        model_second.constant("rate").equation = 99.0

        testBptk = bptk()
        testBptk.register_scenario_manager({"sm": {"model": model_first, "scenarios": {"base": {}}}})

        clear_log()

        testBptk.register_scenario_manager({"sm": {"model": model_second, "scenarios": {"added": {}}}})

        manager = testBptk.scenario_manager_factory.scenario_managers["sm"]
        # Neither half of the call was applied: no scenario was merged in, and the
        # scenario that was already there still runs the first model - rate 1.0, not 99.
        self.assertEqual(sorted(manager.scenarios.keys()), ["base"])
        df = testBptk.run_scenarios(
            scenario_managers=["sm"], scenarios=["base"], equations=["stock"]
        )
        self.assertEqual(df.iloc[-1].iloc[0], 1.0)

        content = read_log()
        self.assertIn("[ERROR] Scenario manager 'sm' is already registered", content)
        self.assertNotIn("Successfully registered scenario manager sm", content)


class TestMatplotlibStyling(unittest.TestCase):
    """Who decides how a chart looks.

    A `bptk()` carries its own plotting configuration, and the package-wide
    `plotting_config` is the look of the two paths that have no `bptk()` in reach -
    `Element.plot()` and `plot_agent_stats()`. Each test starts from the package
    defaults, because that object outlives a test.
    """

    DEFAULT_TITLESIZE = default_config.matplotlib_rc_settings["axes.titlesize"]

    def setUp(self):
        pytest.importorskip("matplotlib.pyplot")
        from BPTK_Py.visualizations import plotting_config

        plotting_config.reset()

    tearDown = setUp

    @staticmethod
    def _element():
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="demo")
        constant = model.constant("constant")
        constant.equation = 2.0
        return constant

    def _titlesize_of_a_scenario_plot(self, testBptk, **kwargs):
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="styling")
        stock = model.stock("stock")
        stock.initial_value = 0.0
        stock.equation = model.constant("rate")
        model.constant("rate").equation = 1.0
        testBptk.register_model(model, scenario_manager="smStyling")
        axes = testBptk.plot_scenarios(
            scenario_managers=["smStyling"], scenarios=["base"],
            equations=["stock"], format="axes", **kwargs
        )
        return axes.title.get_fontsize()

    def test_constructing_bptk_leaves_rcparams_alone(self):
        """bptk() used to write config.matplotlib_rc_settings into plt.rcParams."""
        import matplotlib.pyplot as plt
        plt.rcdefaults()
        before = plt.rcParams["axes.titlesize"]

        bptk()

        self.assertEqual(plt.rcParams["axes.titlesize"], before)

    def test_element_plot_is_styled_without_a_bptk_instance(self):
        """Our own plot must not depend on a bptk() having been built."""
        import matplotlib.pyplot as plt
        plt.rcdefaults()

        axes = self._element().plot(format="axes")

        self.assertEqual(axes.title.get_fontsize(), self.DEFAULT_TITLESIZE)
        # ...and the style is gone again once the call returns, so a chart drawn
        # outside BPTK keeps matplotlib's own defaults.
        self.assertEqual(plt.rcParams["axes.titlesize"], "large")

    def test_instance_configuration_stays_with_that_instance(self):
        """It used to style every plot in the process, which is what a notebook noticed:
        the same cell looked different depending on which cell had run before."""
        testBptk = bptk(configuration={"matplotlib_rc_settings": {"axes.titlesize": 7}})

        self.assertEqual(self._titlesize_of_a_scenario_plot(testBptk), 7.0)
        # Neither the path with no bptk() in reach ...
        self.assertEqual(self._element().plot(format="axes").title.get_fontsize(),
                         self.DEFAULT_TITLESIZE)
        # ... nor a second instance built without a configuration of its own
        self.assertEqual(self._titlesize_of_a_scenario_plot(bptk()),
                         self.DEFAULT_TITLESIZE)

    def test_the_package_wide_configuration_is_what_element_plot_reads(self):
        """Writing there is how the paths without a `bptk()` are styled."""
        from BPTK_Py.visualizations import plotting_config

        plotting_config.update({"matplotlib_rc_settings": {"axes.titlesize": 9}})

        self.assertEqual(self._element().plot(format="axes").title.get_fontsize(), 9.0)
        # and an instance built afterwards starts from it
        self.assertEqual(self._titlesize_of_a_scenario_plot(bptk()), 9.0)

    def test_per_call_settings_win_and_leave_the_configuration_alone(self):
        """The override is for one draw; the next plot reads its configuration again."""
        testBptk = bptk(configuration={"matplotlib_rc_settings": {"axes.titlesize": 7}})
        override = {"axes.titlesize": 21}

        self.assertEqual(
            self._element().plot(format="axes", matplotlib_rc_settings=override).title.get_fontsize(),
            21.0,
        )
        self.assertEqual(
            self._titlesize_of_a_scenario_plot(testBptk, matplotlib_rc_settings=override),
            21.0,
        )
        # Each back to its own baseline: the instance to what it was given, the
        # element to the package-wide look
        self.assertEqual(self._titlesize_of_a_scenario_plot(testBptk), 7.0)
        self.assertEqual(self._element().plot(format="axes").title.get_fontsize(),
                         self.DEFAULT_TITLESIZE)

    def test_figsize_and_linewidth_are_mirrored_between_both_forms(self):
        """`figsize` and `figure.figsize` name the same thing, in either direction.

        The plot calls pass figsize and lw as explicit arguments, and an explicit argument
        beats an rc setting - so without the mirror, setting `figure.figsize` did nothing.
        """
        def measure(axes):
            return (
                tuple(round(float(v), 1) for v in axes.figure.get_size_inches()),
                axes.get_lines()[0].get_linewidth() if axes.get_lines() else None,
            )

        from BPTK_Py.visualizations import plotting_config

        # the rc form, package-wide - which is what Element.plot() reads
        plotting_config.update({"matplotlib_rc_settings": {"figure.figsize": (4, 3),
                                                           "lines.linewidth": 1}})
        self.assertEqual(measure(self._element().plot(format="axes")), ((4.0, 3.0), 1.0))

        # the convenience form, package-wide
        self.setUp()
        plotting_config.update({"figsize": (6, 5), "linewidth": 7})
        self.assertEqual(measure(self._element().plot(format="axes")), ((6.0, 5.0), 7.0))

        # and the same mirror on an instance of its own
        self.setUp()
        instance = bptk(configuration={"matplotlib_rc_settings": {"figure.figsize": (3, 9)}})
        self.assertEqual(instance.plotting_config["figsize"], (3, 9))

        # the rc form on a single call, and gone again afterwards
        self.setUp()
        axes = self._element().plot(
            format="axes", matplotlib_rc_settings={"figure.figsize": (8, 2), "lines.linewidth": 5}
        )
        self.assertEqual(measure(axes), ((8.0, 2.0), 5.0))
        default_figsize = tuple(float(v) for v in default_config.matplotlib_rc_settings["figure.figsize"])
        self.assertEqual(measure(self._element().plot(format="axes"))[0], default_figsize)

    def test_reset_returns_to_the_package_defaults(self):
        from BPTK_Py.visualizations import plotting_config

        plotting_config.update({"matplotlib_rc_settings": {"axes.titlesize": 7}})
        plotting_config.reset()

        self.assertEqual(
            self._element().plot(format="axes").title.get_fontsize(), self.DEFAULT_TITLESIZE
        )


class TestTrainingProgress(unittest.TestCase):
    """The bar tracks the work, not only the episodes.

    Every episode trains each scenario in turn, so a bar that moves once per
    episode stands still for that whole round - the longer the training and the
    more scenarios, the less it says.
    """

    @pytest.mark.requires_threads
    def test_the_bar_advances_once_per_scenario(self):
        testBptk = _build_two_scenario_training_bptk()
        recorder = _ProgressRecorder()

        runner = HybridRunner(testBptk.scenario_manager_factory)
        runner.train_scenario(scenarios=["first", "second"], agents=["learner"],
                              episodes=2, scenario_managers=["trainManager"],
                              progress_widget=recorder)

        # Two episodes over two scenarios: four steps, and each one shows.
        self.assertEqual(recorder.values, [0.0, 0.25, 0.5, 0.75])


_STORAGE_MODEL_SOURCE = '''
from BPTK_Py import Model


class {class_name}(Model):

    def __init__(self):
        super().__init__(starttime=0, stoptime=4, dt=1, name="{class_name}")
        growth = self.constant("growth")
        growth.equation = 2.0
        level = self.stock("level")
        level.initial_value = 0.0
        inflow = self.flow("inflow")
        inflow.equation = growth
        level.equation = inflow
'''


_STORAGE_ABM_SOURCE = '''
from BPTK_Py import Agent, Model


class CounterAgent(Agent):

    def initialize(self):
        self.agent_type = "counter"
        self.state = "active"
        self.set_property("tally", {"type": "Double", "value": 0.0})

    def act(self, time, round_no, step_no):
        self.tally += 1.0


class Counter(Model):

    def instantiate_model(self):
        self.register_agent_factory(
            "counter", lambda agent_id, model, properties: CounterAgent(agent_id, model, properties))
'''


class TestScenarioStorageModelPath(unittest.TestCase):
    """A scenario file names its model relative to the project directory - the parent
    of the folder the file sits in - either as a path to a module
    ("simulation_models/growth") or as a dotted class ("src.growth.Growth"). Neither the
    working directory nor whether "scenario_storage" is relative or absolute may change
    which module that names."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._cwd = os.getcwd()
        self._sys_path = list(sys.path)
        self._modules = set(sys.modules)
        # A fresh package name per test: the modules of an earlier test stay in
        # sys.modules and would otherwise answer for this one.
        self.package = "pkg_" + uuid.uuid4().hex[:8]
        self.root = Path(self._tmp.name).resolve()
        self.project = self.root / "project"
        (self.project / "scenarios").mkdir(parents=True)
        (self.project / self.package).mkdir()
        (self.root / "elsewhere").mkdir()

    def tearDown(self):
        os.chdir(self._cwd)
        sys.path[:] = self._sys_path
        for name in set(sys.modules) - self._modules:
            del sys.modules[name]
        self._tmp.cleanup()

    def _write_project(self, notation):
        """A model and a scenario file naming it in the given notation."""
        if notation == "path":
            class_name = "simulation_model"
            model = "{}/growth".format(self.package)
        else:
            class_name = "Growth"
            model = "{}.growth.Growth".format(self.package)
        (self.project / self.package / "growth.py").write_text(
            _STORAGE_MODEL_SOURCE.format(class_name=class_name))
        (self.project / "scenarios" / "growth.json").write_text(json.dumps({
            "smGrowth": {
                "model": model,
                "base_constants": {"growth": 2.0},
                "scenarios": {"base": {}, "fast": {"constants": {"growth": 5.0}}},
            }
        }))

    def _run(self, storage):
        instance = bptk(configuration={
            "scenario_storage": storage,
            "set_scenario_monitor": False,
            "set_model_monitor": False,
        })
        df = instance.run_scenarios(scenario_managers=["smGrowth"],
                                    scenarios=["base", "fast"],
                                    equations=["level"])
        return list(df["smGrowth_base_level"]), list(df["smGrowth_fast_level"])

    def _assert_runs(self, storage):
        base, fast = self._run(storage)
        self.assertEqual(base, [0.0, 2.0, 4.0, 6.0, 8.0])
        self.assertEqual(fast, [0.0, 5.0, 10.0, 15.0, 20.0])

    # The layout the default configuration expects: relative storage, run from the
    # project directory.

    def test_relative_storage_from_project_dir_path_notation(self):
        self._write_project("path")
        os.chdir(self.project)
        self._assert_runs("scenarios/")

    def test_a_file_without_a_parser_beside_the_scenarios_is_skipped(self):
        """A README among the scenario files used to drop every manager's base
        constants - growth fell back to the model's 2.0 - and made register_scenarios
        raise AttributeError."""
        self._write_project("class")
        scenario_file = self.project / "scenarios" / "growth.json"
        scenario_file.write_text(scenario_file.read_text().replace('"growth": 2.0', '"growth": 3.0'))
        (self.project / "scenarios" / "README.md").write_text("notes")
        os.chdir(self.project)
        base, _ = self._run("scenarios/")
        self.assertEqual(base, [0.0, 3.0, 6.0, 9.0, 12.0])

        instance = bptk(configuration={"scenario_storage": "scenarios/",
                                       "set_scenario_monitor": False, "set_model_monitor": False})
        instance.register_scenarios(scenarios={"more": {}}, scenario_manager="smGrowth")
        self.assertIn("more", instance.scenario_manager_factory.scenario_managers["smGrowth"].scenarios)

    def test_relative_storage_from_project_dir_class_notation(self):
        self._write_project("class")
        os.chdir(self.project)
        self._assert_runs("scenarios/")

    # Relative storage that reaches into the project from outside it.

    def test_relative_storage_from_parent_dir_path_notation(self):
        self._write_project("path")
        os.chdir(self.root)
        self._assert_runs("project/scenarios/")

    def test_relative_storage_from_parent_dir_class_notation(self):
        self._write_project("class")
        os.chdir(self.root)
        self._assert_runs("project/scenarios/")

    def test_relative_storage_from_sibling_dir_class_notation(self):
        self._write_project("class")
        os.chdir(self.root / "elsewhere")
        self._assert_runs("../project/scenarios/")

    # Absolute storage, run from a directory that has nothing to do with the project.

    def test_absolute_storage_from_elsewhere_path_notation(self):
        self._write_project("path")
        os.chdir(self.root / "elsewhere")
        self._assert_runs(str(self.project / "scenarios"))

    def test_absolute_storage_from_elsewhere_class_notation(self):
        self._write_project("class")
        os.chdir(self.root / "elsewhere")
        self._assert_runs(str(self.project / "scenarios"))

    def test_absolute_storage_from_project_dir_class_notation(self):
        self._write_project("class")
        os.chdir(self.project)
        self._assert_runs(str(self.project / "scenarios"))

    # A reset reads the scenarios again from the configured storage, not from ./scenarios.

    def test_reset_reads_from_configured_storage(self):
        self._write_project("class")
        os.chdir(self.root / "elsewhere")
        instance = bptk(configuration={
            "scenario_storage": str(self.project / "scenarios"),
            "set_scenario_monitor": False,
            "set_model_monitor": False,
        })

        instance.reset_all_scenarios()
        self.assertEqual(instance.get_scenario_names(), ["base", "fast"])

        instance.reset_scenario(scenario_manager="smGrowth", scenario="fast")
        self.assertEqual(instance.get_scenario_names(format="dict"), {"smGrowth": ["base", "fast"]})

    # Agent-based models go through the hybrid scenario manager, which imports the
    # dotted class as it stands.

    def _assert_abm_runs(self, storage):
        (self.project / self.package / "counter.py").write_text(_STORAGE_ABM_SOURCE)
        (self.project / "scenarios" / "counter.json").write_text(json.dumps({
            "smCounter": {
                "type": "abm",
                "name": "counter",
                "model": "{}.counter.Counter".format(self.package),
                "scenarios": {"base": {
                    "runspecs": {"starttime": 0, "stoptime": 3, "dt": 1},
                    "properties": {},
                    "agents": [{"name": "counter", "count": 2}],
                }},
            }
        }))
        instance = bptk(configuration={
            "scenario_storage": storage,
            "set_scenario_monitor": False,
            "set_model_monitor": False,
        })
        df = instance.run_scenarios(scenario_managers=["smCounter"], scenarios=["base"],
                                    agents=["counter"], agent_states=["active"],
                                    agent_properties=["tally"],
                                    agent_property_types=["total"])
        self.assertEqual(list(df["smCounter_base_counter_active_tally_total"]),
                         [2.0, 4.0, 6.0, 8.0])

    def test_abm_relative_storage_from_project_dir(self):
        os.chdir(self.project)
        self._assert_abm_runs("scenarios/")

    def test_abm_relative_storage_from_parent_dir(self):
        os.chdir(self.root)
        self._assert_abm_runs("project/scenarios/")

    def test_abm_absolute_storage_from_elsewhere(self):
        os.chdir(self.root / "elsewhere")
        self._assert_abm_runs(str(self.project / "scenarios"))
