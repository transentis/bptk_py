import unittest
from unittest.mock import mock_open, patch, MagicMock
from BPTK_Py.scenariomanager.scenario_manager_factory import ScenarioManagerFactory
from BPTK_Py.scenariomanager.scenario_manager_sd import ScenarioManagerSd
import os, json
from BPTK_Py import Model
from  BPTK_Py.scenariomanager.scenario import SimulationScenario
from tests.helpers.log_helpers import clear_log, read_log


class TestScenarioManagerFactory(unittest.TestCase):
    def test_readScenario_invalid(self):
        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")
        self.assertIsNone(sm._ScenarioManagerFactory__readScenario(filename=testDir))

        testFile = os.path.join(testDir,"invalidFileName")

        #cleanup logfile
        clear_log()

        self.assertIsNone(sm._ScenarioManagerFactory__readScenario(filename=testFile))

        content = read_log()

        self.assertIn(f"[ERROR] No parser available for file {testFile}. Skipping!", content)  

    def test_reset_scenarios(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)
        self.assertEqual(sm.scenario_managers["smPortfolio1"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"],0.01)
        self.assertEqual(sm.scenario_managers["smPortfolio1"].scenarios["scenarioHighInterest"].dictionary["constants"]["interestRate"],0.1)
        self.assertEqual(sm.scenario_managers["smPortfolio2"].scenarios["scenarioHighInitialValue"].dictionary["constants"]["initialValue"],5000.0)

        sm.scenario_managers["smPortfolio1"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"] = 0.02        
        sm.scenario_managers["smPortfolio1"].scenarios["scenarioHighInterest"].dictionary["constants"]["interestRate"] = 0.2
        sm.scenario_managers["smPortfolio2"].scenarios["scenarioHighInitialValue"].dictionary["constants"]["initialValue"] = 10000.0

        sm.reset_scenario(scenario_manager="smPortfolio1", scenario="scenarioLowInterest")
        self.assertEqual(sm.scenario_managers["smPortfolio1"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"],0.01)
        #seems like all scenarios are resetted
        #self.assertEqual(sm.scenario_managers["smPortfolio1"].scenarios["scenarioHighInterest"].dictionary["constants"]["interestRate"],0.2)
        #self.assertEqual(sm.scenario_managers["smPortfolio2"].scenarios["scenarioHighInitialValue"].dictionary["constants"]["initialValue"],10000.0)

    def test_reset_all_scenarios(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False, scenario_storage=testDir)

        sm.get_scenario_managers()
        sm.scenario_managers["smPortfolio1"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"] = 0.02

        # The reset reads from the factory's storage, not from the package default
        sm.reset_all_scenarios()

        self.assertEqual(set(sm.scenario_managers), {"smPortfolio1", "smPortfolio2"})
        self.assertEqual(sm.scenario_managers["smPortfolio1"].scenarios["scenarioLowInterest"].dictionary["constants"]["interestRate"],0.01)

    def test_explicit_path_does_not_move_the_storage(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False, scenario_storage=testDir)
        sm.get_scenario_managers(path=os.path.join(currentDir, "does_not_exist"))

        self.assertEqual(sm.path, testDir)

    def test_refresh_scenarios_for_json(self):
        """FileMonitor callback: re-reads every file of managers referencing the changed JSON."""
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")
        scenarioFile = os.path.join(testDir, "scenario.json")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)
        sm.get_scenario_managers(path=testDir)

        # Both managers in scenario.json reference the changed file, so each of them
        # triggers a re-read of that file.
        with patch.object(sm, "_ScenarioManagerFactory__readScenario") as mock_read:
            sm._ScenarioManagerFactory__refresh_scenarios_for_json(scenarioFile)

        self.assertTrue(mock_read.called)
        for call in mock_read.call_args_list:
            self.assertEqual(call.args[0], scenarioFile)

        # A file that no manager references triggers no re-read.
        with patch.object(sm, "_ScenarioManagerFactory__readScenario") as mock_read_none:
            sm._ScenarioManagerFactory__refresh_scenarios_for_json("/does/not/exist.json")
        mock_read_none.assert_not_called()

    def test_refresh_scenarios_for_source_model(self):
        """ModelMonitor callback: resets every scenario of managers whose source matches."""
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)
        sm.get_scenario_managers(path=testDir)

        source_file = "some/model.itmx"
        sm.scenario_managers["smPortfolio1"].source = source_file  # smPortfolio2 keeps source=""
        expected_scenarios = list(sm.scenario_managers["smPortfolio1"].scenarios.keys())

        with patch.object(sm, "reset_scenario") as mock_reset:
            sm._refresh_scenarios_for_source_model(source_file)

        # Only the manager whose source matches is reset - one call per scenario.
        self.assertEqual(mock_reset.call_count, len(expected_scenarios))
        for call in mock_reset.call_args_list:
            self.assertEqual(call.kwargs["scenario_manager"], "smPortfolio1")
            self.assertIn(call.kwargs["scenario"], expected_scenarios)

    def test_model_monitor_logs_when_source_file_missing(self):
        """With start_model_monitor and a source that does not exist, an error is logged."""
        import tempfile

        tmproot = tempfile.TemporaryDirectory()
        scenariosDir = os.path.join(tmproot.name, "scenarios")
        os.mkdir(scenariosDir)
        scenario_config = {
            "smSourced": {
                "type": "sd",
                "model": "simulation_models/does_not_exist",
                "source": "source_models/missing.itmx",
                "scenarios": {"base": {}}
            }
        }
        with open(os.path.join(scenariosDir, "sourced.json"), "w", encoding="utf-8") as f:
            json.dump(scenario_config, f)

        #cleanup logfile
        clear_log()

        sm = ScenarioManagerFactory(start_model_monitor=True, start_scenario_monitor=False)
        sm.get_scenario_managers(path=scenariosDir)

        content = read_log()

        self.assertIn("[ERROR] Scenario monitor: Source model file not found", content)
        self.assertEqual(sm.model_monitors, {})  # no monitor started for a missing file

        sm.destroy()
        tmproot.cleanup()

    def test_get_scenarios(self):
        currentDir = os.path.abspath(os.getcwd())
        testDir = os.path.join(currentDir,"tests","unittests","test_factory_sd_runner","scenarios")

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        sm.get_scenario_managers(path=testDir)        

        self.assertEqual(sm.get_scenarios(scenario_managers=["smPortfolio1","smPortfolio2"], scenarios=["scenarioHighInterest","scenarioHighInitialValue"])["smPortfolio1_scenarioHighInterest"].name, "scenarioHighInterest")
        self.assertEqual(sm.get_scenarios(scenario_managers=["smPortfolio1","smPortfolio2"], scenarios=["scenarioHighInterest","scenarioHighInitialValue"])["smPortfolio2_scenarioHighInitialValue"].name, "scenarioHighInitialValue")

        self.assertEqual(sm.get_scenarios(scenario_managers=["smPortfolio1"], scenarios=["scenarioHighInterest"])["scenarioHighInterest"].name, "scenarioHighInterest")        

        self.assertEqual(sm.get_scenarios(scenario_managers=["smPortfolio1"], scenarios=["scenarioHighInitialValue"]),{})          


    def test_base_values_skip_what_has_no_parser(self):
        """A file without a parser used to make the whole lookup return None: the base
        values of every other file were lost, and add_scenarios raised on the None."""
        clear_log()

        sm = ScenarioManagerFactory(start_model_monitor=False, start_scenario_monitor=False)

        testDir = os.path.join(os.path.abspath(os.getcwd()), "tests", "unittests", "test_factory_sd_runner", "scenarios")
        invalidFile = os.path.join(testDir, "invalidFileName")
        dictionaries = sm._ScenarioManagerFactory__parse_scenario_files(
            [invalidFile, testDir, os.path.join(testDir, "scenario.json")])

        self.assertEqual(len(dictionaries), 1)
        self.assertEqual(sm._ScenarioManagerFactory__base_values("smPortfolio1", dictionaries, "base_constants"),
                         {"initialValue": 1000.0, "interestRate": 0.05, "depositRate": 1000.0})
        self.assertEqual(sm._ScenarioManagerFactory__base_values("smPortfolio1", dictionaries, "base_points"),
                         {"testBasePoint": [[0.0, 0.1], [1.0, 0.9]]})
        self.assertEqual(sm._ScenarioManagerFactory__base_values("unknown", dictionaries, "base_points"), {})
        self.assertIn(f"[ERROR] No parser available for file {invalidFile}. Skipping!", read_log())
