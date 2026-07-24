import unittest
from unittest import mock

from BPTK_Py.scenariomanager.scenario_manager_factory import ScenarioManagerFactory
from BPTK_Py.scenariorunners.sd_runner import SdRunner
import BPTK_Py.logger.logger as logmod
import os
import pandas as pd

class TestSdRunner(unittest.TestCase):
    def setUp(self):
        pass

    def test_run_scenario_step(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)
        sdRunner = SdRunner(scenario_manager_factory=sm)

        settings = {
            "smPortfolio1": {
                "scenarioLowInterest": {
                    "points": {
                        "testBasePoints": [
                            [0.0,0.2],
                            [1.0,0.8]                        
                        ]
                    }    
                }
            }
        }

        self.assertEqual(sdRunner.run_scenario_step(step=0, settings=settings, scenario_manager="smPortfolio1", scenarios=["scenarioLowInterest"], equations=["totalValue"]),{'scenarioLowInterest': {'totalValue': {0.0: 1000.0}}})
        self.assertEqual(sdRunner.run_scenario_step(step=1, settings=settings, scenario_manager="smPortfolio1", scenarios=["scenarioLowInterest"], equations=["totalValue"]),{'scenarioLowInterest': {'totalValue': {1.0: 2010.0}}})
        self.assertEqual(sdRunner.run_scenario_step(step=2, settings=settings, scenario_manager="smPortfolio1", scenarios=["scenarioLowInterest"], equations=["totalValue"]),{'scenarioLowInterest': {'totalValue': {2.0: 3030.1}}})

    def test_run_scenario_step_invalid(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)
        sdRunner = SdRunner(scenario_manager_factory=sm)

        self.assertEqual(sdRunner.run_scenario_step(step=1, settings=[], scenario_manager="testManager", scenarios=["testScenario"], equations=[]),{})

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] No scenarios found for scenario manager \"testManager\" and scenarios \"testScenario\"", content)  

    def test_run_scenario_did_you_mean(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)
        sdRunner = SdRunner(scenario_manager_factory=sm)

        self.assertEqual(sdRunner.run_scenario(sd_results_dict={},return_format="json", scenario_managers=["smPortfolio1"], scenarios=["scenarioLowInterest"], equations=["totalValu"]),{})        

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] No simulation model containing equation \"totalValu\". Did you maybe mean one of \"totalValue", content)

    def test_run_scenario_array_equations_and_no_suggestion(self):
        """Array ("*") equations are stripped of their index before lookup;
        when no equations exist at all, the no-suggestion error branch fires."""
        from BPTK_Py import Model
        from BPTK_Py.scenariomanager.scenario import SimulationScenario
        from BPTK_Py.scenariomanager.scenario_manager_sd import ScenarioManagerSd

        #cleanup logfile
        with open(logmod.logfile, "w", encoding="UTF-8"):
            pass

        # A model with no equations -> all_equations is empty, so didyoumean returns nothing.
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0, name="empty")
        scenario = SimulationScenario(dictionary={}, name="emptyScenario",
                                      model=model, scenario_manager_name="emptyMgr")
        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)
        manager = ScenarioManagerSd(scenarios={"emptyScenario": scenario}, name="emptyMgr", model=model)
        manager.type = "sd"
        sm.scenario_managers["emptyMgr"] = manager
        sdRunner = SdRunner(scenario_manager_factory=sm)

        # "stock[*]" exercises the array-index stripping branch (regex match);
        # "foo*" exercises the "*" branch without brackets (regex miss).
        result = sdRunner.run_scenario(sd_results_dict={}, return_format="json",
                                       scenario_managers=["emptyMgr"], scenarios=["emptyScenario"],
                                       equations=["stock[*]", "foo*"])

        self.assertEqual(result, {})

        with open(logmod.logfile, "r", encoding="UTF-8") as file:
            content = file.read()
        self.assertIn("[ERROR] No simulation model containing equation \"stock[*]\"", content)
        self.assertIn("[ERROR] No simulation model containing equation \"foo*\"", content)

    def test_run_scenario_invalid(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)
        sdRunner = SdRunner(scenario_manager_factory=sm)

        self.assertIsNone(sdRunner.run_scenario(sd_results_dict={}, return_format="json", scenario_managers=["testManager"], scenarios=["testScenario"], equations=[]))

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] No scenario found for scenario_managers=[\'testManager\'] and scenario_names=[\'testScenario\']. Cancelling", content)  

    def test_run_scenarios_invalid(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)
        sdRunner = SdRunner(scenario_manager_factory=sm)

        self.assertEqual(sdRunner._run_scenarios(scenario_managers=["testManager"], scenarios=["testScenario"], equations=[]),{})

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] No scenarios found for scenario managers \"testManager\" and scenarios \"testScenario\"", content)  

    # ------------------------------------------------------------------
    # Phase 4 Substep 4d: backend dispatch + step-by-step Rust execution
    # ------------------------------------------------------------------

    def _build_runner_and_scenario(self):
        """Helper: load the smPortfolio1 scenario manager + scenarioLowInterest
        scenario from the existing fixture, return (runner, scenario_obj)."""
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir, "tests", "unittests",
                               "test_factory_sd_runner", "scenarios")
        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)
        sm.get_scenario_managers(path=testDir)
        runner = SdRunner(scenario_manager_factory=sm)
        sc = sm.get_scenario(scenario_manager="smPortfolio1", scenario="scenarioLowInterest")
        return runner, sc

    def test_run_scenario_step_python_dispatch_called(self):
        """With backend='python', the runner must invoke _run_scenario_step_python
        and not _run_scenario_step_rust."""
        runner, _ = self._build_runner_and_scenario()
        with mock.patch.object(SdRunner, "_run_scenario_step_python",
                               autospec=True) as py_mock, \
             mock.patch.object(SdRunner, "_run_scenario_step_rust",
                               autospec=True) as rust_mock:
            py_mock.side_effect = lambda self, sc, *a, **kw: setattr(
                sc, "result", pd.DataFrame({"totalValue": {0.0: 0.0}}))
            runner.run_scenario_step(step=0, settings=None,
                                     scenario_manager="smPortfolio1",
                                     scenarios=["scenarioLowInterest"],
                                     equations=["totalValue"],
                                     backend="python")
            py_mock.assert_called_once()
            rust_mock.assert_not_called()

    def test_run_scenario_step_rust_dispatch_called(self):
        """With backend='rust', the runner must invoke _run_scenario_step_rust."""
        runner, _ = self._build_runner_and_scenario()
        with mock.patch.object(SdRunner, "_run_scenario_step_python",
                               autospec=True) as py_mock, \
             mock.patch.object(SdRunner, "_run_scenario_step_rust",
                               autospec=True) as rust_mock:
            rust_mock.side_effect = lambda self, sc, *a, **kw: setattr(
                sc, "result", pd.DataFrame({"totalValue": {0.0: 0.0}}))
            runner.run_scenario_step(step=0, settings=None,
                                     scenario_manager="smPortfolio1",
                                     scenarios=["scenarioLowInterest"],
                                     equations=["totalValue"],
                                     backend="rust")
            rust_mock.assert_called_once()
            py_mock.assert_not_called()

    def test_run_scenario_step_sticky_failed_skips_rust(self):
        """A scenario flagged _rust_failed must skip the Rust path even when
        backend='rust' is requested (no retry within the same session)."""
        runner, sc = self._build_runner_and_scenario()
        sc._rust_failed = True
        with mock.patch.object(SdRunner, "_run_scenario_step_python",
                               autospec=True) as py_mock, \
             mock.patch.object(SdRunner, "_run_scenario_step_rust",
                               autospec=True) as rust_mock:
            py_mock.side_effect = lambda self, sc, *a, **kw: setattr(
                sc, "result", pd.DataFrame({"totalValue": {0.0: 0.0}}))
            runner.run_scenario_step(step=0, settings=None,
                                     scenario_manager="smPortfolio1",
                                     scenarios=["scenarioLowInterest"],
                                     equations=["totalValue"],
                                     backend="rust")
            py_mock.assert_called_once()
            rust_mock.assert_not_called()

    def test_run_scenario_step_value_error_triggers_fallback(self):
        runner, sc = self._build_runner_and_scenario()
        with mock.patch.object(SdRunner, "_run_scenario_step_rust",
                               autospec=True,
                               side_effect=ValueError("simulated rust failure")):
            runner.run_scenario_step(step=0, settings=None,
                                     scenario_manager="smPortfolio1",
                                     scenarios=["scenarioLowInterest"],
                                     equations=["totalValue"],
                                     backend="rust")
        self.assertTrue(sc._rust_failed)
        self.assertIsNone(sc.rust_model)
        self.assertIsNotNone(sc.result)  # python path produced a result

    def test_run_scenario_step_import_error_triggers_fallback(self):
        runner, sc = self._build_runner_and_scenario()
        with mock.patch.object(SdRunner, "_run_scenario_step_rust",
                               autospec=True,
                               side_effect=ImportError("_rust_engine not built")):
            runner.run_scenario_step(step=0, settings=None,
                                     scenario_manager="smPortfolio1",
                                     scenarios=["scenarioLowInterest"],
                                     equations=["totalValue"],
                                     backend="rust")
        self.assertTrue(sc._rust_failed)
        self.assertIsNotNone(sc.result)

    def test_run_scenario_step_attribute_error_triggers_fallback(self):
        """E.g. an XMILE SimulationModel that lacks to_json — must fall back."""
        runner, sc = self._build_runner_and_scenario()
        with mock.patch.object(SdRunner, "_run_scenario_step_rust",
                               autospec=True,
                               side_effect=AttributeError("no to_json")):
            runner.run_scenario_step(step=0, settings=None,
                                     scenario_manager="smPortfolio1",
                                     scenarios=["scenarioLowInterest"],
                                     equations=["totalValue"],
                                     backend="rust")
        self.assertTrue(sc._rust_failed)
        self.assertIsNotNone(sc.result)

    def test_run_scenario_step_fallback_logs_warning(self):
        """Fallback must emit a [WARN] log line so operators see the switch."""
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        runner, _ = self._build_runner_and_scenario()
        with mock.patch.object(SdRunner, "_run_scenario_step_rust",
                               autospec=True,
                               side_effect=ValueError("boom")):
            runner.run_scenario_step(step=0, settings=None,
                                     scenario_manager="smPortfolio1",
                                     scenarios=["scenarioLowInterest"],
                                     equations=["totalValue"],
                                     backend="rust")

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()
        self.assertIn("[WARN]", content)
        self.assertIn("falling back to Python", content)

    def test_run_scenario_step_rust_first_call_initialises_model(self):
        """The first invocation of _run_scenario_step_rust must populate
        rust_model, _rust_initial, and flip _rust_initial_returned to True."""
        runner, sc = self._build_runner_and_scenario()
        self.assertIsNone(sc.rust_model)
        runner._run_scenario_step_rust(sc, step=0, settings=None,
                                       scenario_manager="smPortfolio1",
                                       scenario="scenarioLowInterest",
                                       equations=["totalValue", "interest"])
        self.assertIsNotNone(sc.rust_model)
        self.assertIsNotNone(sc._rust_initial)
        self.assertTrue(sc._rust_initial_returned)
        # Initial step: t=0, totalValue starts at initialValue=1000
        self.assertEqual(sc.result.index.name, "t")
        self.assertEqual(list(sc.result.index), [0.0])
        self.assertAlmostEqual(sc.result.loc[0.0, "totalValue"], 1000.0)

    def test_run_scenario_step_rust_subsequent_call_advances_cursor(self):
        runner, sc = self._build_runner_and_scenario()
        runner._run_scenario_step_rust(sc, step=0, settings=None,
                                       scenario_manager="smPortfolio1",
                                       scenario="scenarioLowInterest",
                                       equations=["totalValue"])
        runner._run_scenario_step_rust(sc, step=1.0, settings=None,
                                       scenario_manager="smPortfolio1",
                                       scenario="scenarioLowInterest",
                                       equations=["totalValue"])
        self.assertEqual(list(sc.result.index), [1.0])
        # interestRate=0.01, depositRate=1000 → totalValue(1)=1000+1000+10=2010
        self.assertAlmostEqual(sc.result.loc[1.0, "totalValue"], 2010.0)

    def test_run_scenario_step_rust_per_step_constant_override(self):
        """A constants override in `settings` takes effect during the run_step
        call where it is applied: the integration for the cursor advance uses
        the new constant, so the *next* run_step call's value reflects it.
        PyO3 methods can't be patched directly (Rust-defined, read-only), so
        we verify observable behaviour via the resulting stock values."""
        runner, sc = self._build_runner_and_scenario()
        # Step 0: initial value = 1000 (interestRate=0.01 from scenarioLowInterest)
        runner._run_scenario_step_rust(sc, step=0, settings=None,
                                       scenario_manager="smPortfolio1",
                                       scenario="scenarioLowInterest",
                                       equations=["totalValue"])
        # Step 1 with override interestRate=0.5: stock(1)=2010 (already integrated
        # at init with old rate), but flow(1) is recomputed with new rate, so
        # stock(2) = 2010 + dt*(0.5*2010 + 1000) = 4015 (effect visible NEXT step).
        runner._run_scenario_step_rust(
            sc, step=1.0,
            settings={"smPortfolio1": {"scenarioLowInterest":
                      {"constants": {"interestRate": 0.5}}}},
            scenario_manager="smPortfolio1",
            scenario="scenarioLowInterest",
            equations=["totalValue"])
        self.assertAlmostEqual(sc.result.loc[1.0, "totalValue"], 2010.0)
        # Step 2 with no further override: stock(2) reflects the prior step's
        # integration done with the new interestRate → 4015.
        runner._run_scenario_step_rust(sc, step=2.0, settings=None,
                                       scenario_manager="smPortfolio1",
                                       scenario="scenarioLowInterest",
                                       equations=["totalValue"])
        self.assertAlmostEqual(sc.result.loc[2.0, "totalValue"], 4015.0)

    def test_run_scenario_step_rust_per_step_points_override_accepts_list_of_list(self):
        """The runner accepts list-of-list (JSON shape) points and normalises
        them to list-of-tuple before sending to rust_model.set_points. We verify
        by feeding list-of-list and checking the call doesn't raise — if the
        normalisation were missing, PyO3 would raise TypeError on the tuple
        conversion (covered explicitly by tests/test_rust_step.py's per-step
        points parity test)."""
        runner, sc = self._build_runner_and_scenario()
        runner._run_scenario_step_rust(sc, step=0, settings=None,
                                       scenario_manager="smPortfolio1",
                                       scenario="scenarioLowInterest",
                                       equations=["totalValue"])
        # The fixture model has a points table "testBasePoint"; we override it
        # in list-of-list shape (the JSON-native format).
        runner._run_scenario_step_rust(
            sc, step=1.0,
            settings={"smPortfolio1": {"scenarioLowInterest":
                      {"points": {"testBasePoint": [[0, 0.5], [1, 0.6]]}}}},
            scenario_manager="smPortfolio1",
            scenario="scenarioLowInterest",
            equations=["totalValue"])
        # The step must produce a row; if the list→tuple normalisation were
        # missing, set_points would raise TypeError above.
        self.assertEqual(list(sc.result.index), [1.0])

    def test_run_scenario_step_rust_settings_for_other_manager_ignored(self):
        """Settings under a different scenario_manager name must not affect
        the active scenario — observable via the unchanged stepwise value."""
        runner, sc = self._build_runner_and_scenario()
        runner._run_scenario_step_rust(sc, step=0, settings=None,
                                       scenario_manager="smPortfolio1",
                                       scenario="scenarioLowInterest",
                                       equations=["totalValue"])
        runner._run_scenario_step_rust(
            sc, step=1.0,
            settings={"smOtherManager": {"scenarioLowInterest":
                      {"constants": {"interestRate": 99.0}}}},
            scenario_manager="smPortfolio1",
            scenario="scenarioLowInterest",
            equations=["totalValue"])
        # interestRate stayed at 0.01 → totalValue(1) = 2010, not 100k+.
        self.assertAlmostEqual(sc.result.loc[1.0, "totalValue"], 2010.0)

    def test_run_scenario_step_rust_settings_for_other_scenario_ignored(self):
        runner, sc = self._build_runner_and_scenario()
        runner._run_scenario_step_rust(sc, step=0, settings=None,
                                       scenario_manager="smPortfolio1",
                                       scenario="scenarioLowInterest",
                                       equations=["totalValue"])
        runner._run_scenario_step_rust(
            sc, step=1.0,
            settings={"smPortfolio1": {"someOtherScenario":
                      {"constants": {"interestRate": 99.0}}}},
            scenario_manager="smPortfolio1",
            scenario="scenarioLowInterest",
            equations=["totalValue"])
        self.assertAlmostEqual(sc.result.loc[1.0, "totalValue"], 2010.0)

    def test_run_scenario_step_rust_missing_settings_is_no_op(self):
        """Empty / None settings must not change behaviour."""
        runner, sc = self._build_runner_and_scenario()
        runner._run_scenario_step_rust(sc, step=0, settings=None,
                                       scenario_manager="smPortfolio1",
                                       scenario="scenarioLowInterest",
                                       equations=["totalValue"])
        # No-settings step must produce the same result as the baseline.
        runner._run_scenario_step_rust(sc, step=1.0, settings={},
                                       scenario_manager="smPortfolio1",
                                       scenario="scenarioLowInterest",
                                       equations=["totalValue"])
        self.assertAlmostEqual(sc.result.loc[1.0, "totalValue"], 2010.0)

    def test_run_scenario_step_rust_non_numeric_constant_raises(self):
        """A non-numeric value in sc.constants must raise ValueError so the
        runner can fall back to Python."""
        runner, sc = self._build_runner_and_scenario()
        sc.constants["interestRate"] = "lambda t: t + 1"  # non-numeric override

        with self.assertRaises(ValueError) as ctx:
            runner._run_scenario_step_rust(sc, step=0, settings=None,
                                           scenario_manager="smPortfolio1",
                                           scenario="scenarioLowInterest",
                                           equations=["totalValue"])
        self.assertIn("Non-numeric constant", str(ctx.exception))

    def test_run_scenario_step_python_first_call_creates_simulation(self):
        runner, sc = self._build_runner_and_scenario()
        self.assertIsNone(sc.sd_simulation)
        runner._run_scenario_step_python(sc, step=0, settings=None,
                                         scenario_manager="smPortfolio1",
                                         scenario="scenarioLowInterest",
                                         equations=["totalValue"])
        self.assertIsNotNone(sc.sd_simulation)
        self.assertIsNotNone(sc.result)

    def test_run_scenario_step_python_reuses_simulation(self):
        runner, sc = self._build_runner_and_scenario()
        runner._run_scenario_step_python(sc, step=0, settings=None,
                                         scenario_manager="smPortfolio1",
                                         scenario="scenarioLowInterest",
                                         equations=["totalValue"])
        first_sim = sc.sd_simulation
        runner._run_scenario_step_python(sc, step=1.0, settings=None,
                                         scenario_manager="smPortfolio1",
                                         scenario="scenarioLowInterest",
                                         equations=["totalValue"])
        self.assertIs(sc.sd_simulation, first_sim)

    def test_run_scenario_step_dt_mismatch_advances_multiple_internal_steps(self):
        """When session dt > model dt, the Rust runner must issue multiple
        internal step() calls per run_step so the returned t matches the caller.
        Built via bptk.register_scenario_manager rather than the JSON fixture
        because the fixture only ships a dt=1.0 model."""
        from BPTK_Py import Model
        import BPTK_Py
        model = Model(starttime=0.0, stoptime=5.0, dt=0.25, name="dtMismatch")
        stock = model.stock("stock")
        flow = model.flow("flow")
        constant = model.constant("constant")
        stock.initial_value = 0.0
        stock.equation = flow
        flow.equation = constant
        constant.equation = 1.0

        b = BPTK_Py.bptk()
        b.register_scenario_manager({"dtMgr": {"model": model}})
        b.register_scenarios(scenarios={"base": {}}, scenario_manager="dtMgr")
        runner = SdRunner(b.scenario_manager_factory)
        sc = b.scenario_manager_factory.get_scenario(
            scenario_manager="dtMgr", scenario="base")

        runner._run_scenario_step_rust(sc, step=0.0, settings=None,
                                       scenario_manager="dtMgr",
                                       scenario="base",
                                       equations=["stock"])
        # Caller advances by 1.0 (session dt) but model dt is 0.25 → 4 internal steps.
        runner._run_scenario_step_rust(sc, step=1.0, settings=None,
                                       scenario_manager="dtMgr",
                                       scenario="base",
                                       equations=["stock"])
        self.assertAlmostEqual(sc.rust_model.current_time(), 1.0)
        self.assertEqual(list(sc.result.index), [1.0])
        # stock(1.0) = integral of constant=1.0 from 0 to 1.0 = 1.0
        self.assertAlmostEqual(sc.result.loc[1.0, "stock"], 1.0)


if __name__ == '__main__':
    unittest.main()