import unittest
import os

import pytest
from pandas.testing import assert_frame_equal

import BPTK_Py
from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
from tests.helpers.arrayed_fixtures import build_workforce_model
from BPTK_Py.scenariomanager.scenario import SimulationScenario
from BPTK_Py.scenariomanager.scenario_manager_sd import ScenarioManagerSd
from tests.helpers.log_helpers import clear_log, read_log

class TestScenarioManagerSD(unittest.TestCase):
    def test_defaults_are_not_shared(self):
        first = ScenarioManagerSd(name="first")
        second = ScenarioManagerSd(name="second")

        first.scenarios["only_in_first"] = None
        first.base_constants["only_in_first"] = 1.0
        first.base_points["only_in_first"] = [[0, 0]]

        self.assertEqual(second.scenarios, {})
        self.assertEqual(second.base_constants, {})
        self.assertEqual(second.base_points, {})

    def test_load_scenarios(self):
        import BPTK_Py.logger.logger as logmod
        logmod.loglevel="INFO"

        #cleanup logfile
        clear_log()

        class TestableTestScenarioManagerSD(ScenarioManagerSd):
            def __init__(self, base_points, base_constants):
                super().__init__(base_points=base_points, base_constants=base_constants,scenarios={})
                self.called_instantiate_model = 0

            def instantiate_model(self):
                self.called_instantiate_model = 1

        scenarioManager = TestableTestScenarioManagerSD(base_constants={ "constant1" : 1.0 , "constant2" : 2.0 }, base_points= { "point1" : "11+11" , "point2" : "22+22" })

        scenario1 = SimulationScenario(dictionary={ "constants" : { "constant1" : 1.0 , "constant2" : 2.0 } , "points" : { "point1" : "11+11" , "point2" : "22+22" } },name="scenario1", model=Model(), scenario_manager_name="scenarioManagerName")
        scenario2 = SimulationScenario(dictionary={ "constants" : { "constant1" : 11.0 , "constant2" : 12.0 } , "points" : { "point1" : "111+111" , "point2" : "222+222" } },name="scenario2", model=Model(), scenario_manager_name="scenarioManagerName")
        scenarioManager.scenarios[scenario1.name] = scenario1

        scenarioDictionary = {
            "base": {
            },
            "scenario1" : {
                "constants": {
                    "constant1" : 1.1 
                },
                "points": {
                    "point2" : "33+33"
                }               
            },
            "scenario2" : {
                "constants": {
                    "constant1" : 11.0, 
                    "constant2" : 12.0
                },
                "points": {
                    "point1" : "111+111",
                    "point2" : "222+222"
                }               
            },            
        }

        scenarioManager.load_scenarios(scen_dict=scenarioDictionary,model_file="testModelFile",source="testSource")    

        self.assertEqual(scenarioManager.scenarios["base"].dictionary["constants"]["constant1"],1.0)
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["constants"]["constant2"],2.0)
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["points"]["point1"],"11+11")
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["points"]["point2"],"22+22")

        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["constants"]["constant1"],1.1)
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["constants"]["constant2"],2.0)
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["points"]["point1"],"11+11")
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["points"]["point2"],"33+33")

        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["constants"]["constant1"],11.0)
        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["constants"]["constant2"],12.0)
        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["points"]["point1"],"111+111")
        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["points"]["point2"],"222+222")        

        content = read_log()

        self.assertIn("[INFO] Model scenario1 was updated!", content)          
        self.assertNotIn("[INFO] Model scenario2 was updated!", content) 

        self.assertEqual(scenarioManager.model_file,"testModelFile")
        self.assertEqual(scenarioManager.source,"testSource")      
        self.assertEqual(scenarioManager.called_instantiate_model,1)   

    def test_add_scenarios(self):
        class TestableTestScenarioManagerSD(ScenarioManagerSd):
            def __init__(self, base_points, base_constants):
                super().__init__(base_points=base_points, base_constants=base_constants,scenarios={})
                self.called_instantiate_model = 0

            def instantiate_model(self):
                self.called_instantiate_model = 1

        scenarioManager = TestableTestScenarioManagerSD(base_constants={ "constant1" : 100.0 , "constant2" : 200.0 }, base_points= { "point1" : "8+8" , "point2" : "9+9" })

        scenarioDictionary = {
            "base": {
            },
            "scenario1" : {
                "constants": {
                    "constant1" : 101.0 
                },
                "points": {
                    "point2" : "19+19"
                }               
            },
            "scenario2" : {
                "constants": {
                    "constant1" : 102.0,
                    "constant2" : 202.0
                },
                "points": {
                    "point1" : "28+28",
                    "point2" : "29+29"
                }               
            }                           
        }

        scenarioManager.add_scenarios(scenario_dictionary=scenarioDictionary)

        self.assertEqual(scenarioManager.scenarios["base"].dictionary["constants"]["constant1"],100.0)
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["constants"]["constant2"],200.0)
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["points"]["point1"],"8+8")
        self.assertEqual(scenarioManager.scenarios["base"].dictionary["points"]["point2"],"9+9")

        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["constants"]["constant1"],101.0)
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["constants"]["constant2"],200.0)
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["points"]["point1"],"8+8")
        self.assertEqual(scenarioManager.scenarios["scenario1"].dictionary["points"]["point2"],"19+19")        

        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["constants"]["constant1"],102.0)
        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["constants"]["constant2"],202.0)
        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["points"]["point1"],"28+28")
        self.assertEqual(scenarioManager.scenarios["scenario2"].dictionary["points"]["point2"],"29+29")  

        self.assertEqual(scenarioManager.called_instantiate_model,1) 

    def test_get_cloned_model_none(self):
        scenarioManager = ScenarioManagerSd()

        self.assertIsNone(scenarioManager.get_cloned_model(model=None))

    def test_instantiate_model_source_file_missing(self):
        """A compiled model with a source path that no longer exists clears source."""
        import BPTK_Py.logger.logger as logmod
        import tempfile, os
        logmod.loglevel = "INFO"
        clear_log()

        tmpdir = tempfile.TemporaryDirectory()
        # a compiled .py exists on disk, but the referenced source file does not
        with open(os.path.join(tmpdir.name, "model.py"), "w", encoding="utf-8") as f:
            f.write("simulation_model = None\n")
        missing_source = os.path.join(tmpdir.name, "missing.itmx")

        scenarioManager = ScenarioManagerSd(
            scenarios={}, name="mgr",
            model_file=os.path.join(tmpdir.name, "model"),
            source=missing_source,
        )

        scenarioManager.instantiate_model()

        # The missing source was reported and reset to "".
        self.assertEqual(scenarioManager.source, "")
        content = read_log()
        self.assertIn("[ERROR] Source model file not found", content)

        tmpdir.cleanup()

    def test_instantiate_model_bare_model_filename(self):
        """A model file without a parent directory uses just the stem as the package link."""
        # model_file has no directory component -> Path("baremodel.py").parent.name == ""
        scenarioManager = ScenarioManagerSd(scenarios={}, name="mgr", model_file="baremodel", source="")

        # The import will fail (no such module), which is caught internally and clears scenarios.
        scenarioManager.instantiate_model()

        self.assertEqual(scenarioManager.scenarios, {})

    def test_instantiate_model_reports_an_error_inside_the_module(self):
        """Only a failed import means "the last part is a class". An error raised by the
        model module itself used to send the loader down that path too, and the log
        then named an import that was never the problem."""
        import sys, tempfile
        import BPTK_Py.logger.logger as logmod

        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, "broken_model.py"), "w", encoding="UTF-8") as file:
                file.write("raise RuntimeError('the model itself is broken')\n")
            sys.path.insert(0, folder)
            try:
                clear_log()
                manager = ScenarioManagerSd(scenarios={}, name="mgr", model_file="broken_model", source="")
                manager.model_module = "broken_model"
                manager.instantiate_model()
            finally:
                sys.path.remove(folder)
                sys.modules.pop("broken_model", None)

        self.assertIn("the model itself is broken", read_log())

    def test_refuses_a_stock_among_the_constants(self):
        """A stock set as a constant used to stay at that value for the whole run."""
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="m")
        stock = model.stock("population")
        stock.initial_value = 10.0
        stock.equation = 1.0
        model.constant("food").equation = 1.0

        manager = ScenarioManagerSd(scenarios={}, name="sm", model=model)
        with self.assertRaises(ValueError) as raised:
            manager.add_scenarios({"x": {"constants": {"population": 80.0, "food": 2.0}}})
        self.assertIn("'population'", str(raised.exception))
        self.assertNotIn("'food'", str(raised.exception))
        self.assertIn("initial_value", str(raised.exception))

        with self.assertRaises(ValueError):
            ScenarioManagerSd(scenarios={}, name="sm2", model=model,
                              base_constants={"population": 80.0}).add_scenarios({"base": {}})

    def test_refuses_a_stock_set_as_a_constant_later(self):
        from BPTK_Py.scenariomanager.scenario import SimulationScenario

        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="m")
        model.stock("population").equation = 1.0
        scenario = SimulationScenario(dictionary={}, name="s", model=model, scenario_manager_name="sm")

        with self.assertRaises(ValueError):
            scenario.configure_settings({"constants": {"population": 5.0}})

    def test_add_scenarios_instantiates_the_model_once(self):
        """For a model read from a file each call imports the module again; it used to
        run once per scenario added."""
        class CountingScenarioManagerSD(ScenarioManagerSd):
            calls = 0

            def instantiate_model(self):
                CountingScenarioManagerSD.calls += 1

        manager = CountingScenarioManagerSD()
        manager.add_scenarios({"a": {}, "b": {}, "c": {}})
        self.assertEqual(CountingScenarioManagerSD.calls, 1)

        manager.add_scenarios({})
        self.assertEqual(CountingScenarioManagerSD.calls, 1)

    def test_add_scenarios_warns_only_on_a_different_definition(self):
        """Registering the same scenario twice is ordinary; registering two different
        scenarios under one name is a mistake.

        A notebook cell run again re-registers what it registered before, and warning
        about that would put a line in the log on every interaction. Two *different*
        definitions under one name is the case that cost a documentation page its table:
        the second registration won, and the text above the first one no longer matched.
        """
        import BPTK_Py.logger.logger as logmod

        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="m")
        model.constant("c").equation = 1.0
        manager = ScenarioManagerSd(scenarios={}, name="sm", model=model)

        clear_log()

        manager.add_scenarios({"x": {}})
        manager.add_scenarios({"x": {}})
        after_same_definition = read_log()
        self.assertNotIn("already registered with a different", after_same_definition)

        manager.add_scenarios({"x": {"constants": {"c": 2.0}}})
        after_different_definition = read_log()
        self.assertIn(
            "scenario 'x' is already registered with a different definition",
            after_different_definition,
        )

    def test_leaves_the_callers_dict_alone(self):
        """The scenario used to keep the caller's dict and merge the base constants into
        it, so a setting on the scenario changed the caller's dict - and the same
        definition registered again was then warned about as a different one."""
        import BPTK_Py.logger.logger as logmod

        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="m")
        model.constant("c").equation = 1.0
        manager = ScenarioManagerSd(scenarios={}, name="sm", model=model, base_constants={"c": 1.0})
        mine = {"base": {"constants": {}}, "high": {"constants": {"c": 5.0}}}

        manager.add_scenarios(mine)
        self.assertEqual(mine, {"base": {"constants": {}}, "high": {"constants": {"c": 5.0}}})

        manager.scenarios["high"].set_property_value("c", 9.0)
        self.assertEqual(mine["high"], {"constants": {"c": 5.0}})
        self.assertEqual(manager.scenarios["high"].get_property_value("c"), 9.0)

        clear_log()
        manager.add_scenarios({"base": {"constants": {}}, "high": {"constants": {"c": 5.0}}})
        self.assertNotIn("already registered with a different", read_log())

    def test_load_scenarios_leaves_the_callers_dict_alone(self):
        manager = ScenarioManagerSd(scenarios={}, name="sm", base_constants={"c": 1.0},
                                    base_points={"p": [[0, 0], [1, 1]]})
        manager.instantiate_model = lambda: None
        mine = {"base": {}}

        manager.load_scenarios(scen_dict=mine, model_file="unused")

        self.assertEqual(mine, {"base": {}})
        self.assertEqual(manager.scenarios["base"].constants, {"c": 1.0})
        self.assertEqual(manager.scenarios["base"].points, {"p": [[0, 0], [1, 1]]})


def _every_kind_model():
    """One of each element kind, and each thing a clone has to carry over: a stock
    starting from a constant and one starting from an expression, a lookup, a
    user-defined function and a delay."""
    model = Model(starttime=0.0, stoptime=6.0, dt=1.0, name="every_kind")
    model.points["curve"] = [(0.0, 1.0), (6.0, 4.0)]
    model.function("double", lambda model, t, value: 2.0 * value)

    start = model.constant("start")
    start.equation = 10.0
    rate = model.constant("rate")
    rate.equation = 0.5

    from_constant = model.stock("from_constant")
    from_constant.initial_value = start
    from_expression = model.stock("from_expression")
    from_expression.initial_value = start * 2.0 + 5.0

    inflow = model.flow("inflow")
    inflow.equation = sd.lookup(sd.time(), "curve") * rate
    exchange = model.biflow("exchange")
    exchange.equation = (from_expression - from_constant) * 0.1

    from_constant.equation = inflow + exchange
    from_expression.equation = -exchange

    doubled = model.converter("doubled")
    doubled.equation = model.functions["double"](from_constant)
    delayed = model.converter("delayed")
    delayed.equation = sd.delay(model, doubled, 2.0, 0.0)
    return model


_EVERY_KIND = ["start", "rate", "from_constant", "from_expression", "inflow", "exchange",
               "doubled", "delayed"]


class TestGetClonedModel(unittest.TestCase):
    """What a scenario's copy of a registered model has to keep."""

    def _clone(self, model):
        return ScenarioManagerSd().get_cloned_model(model)

    def test_every_element_kind_is_copied_under_its_name(self):
        model = _every_kind_model()
        clone = self._clone(model)

        self.assertIsNot(clone, model)
        for kind in ("constants", "converters", "flows", "biflows", "stocks"):
            original_elements = getattr(model, kind)
            cloned_elements = getattr(clone, kind)
            self.assertEqual(sorted(cloned_elements), sorted(original_elements), kind)
            for name in original_elements:
                self.assertIsNot(cloned_elements[name], original_elements[name], name)
                self.assertIs(cloned_elements[name].model, clone, name)
        self.assertEqual(sorted(clone.fn), ["double"])
        self.assertEqual((clone.starttime, clone.stoptime, clone.dt, clone.name),
                         (model.starttime, model.stoptime, model.dt, model.name))

    def test_the_clone_serialises_as_the_original(self):
        for model in (_every_kind_model(), build_workforce_model()):
            with self.subTest(model=model.name):
                self.assertEqual(self._clone(model).to_json(), model.to_json())

    def test_an_arrayed_element_of_the_clone_leads_to_the_clone(self):
        """The clone used to share the original's index of sub-elements, so its parent
        handed out the original model's elements, and it lost the arrayed flags - each
        scenario serialised the parents as bogus entities of value 0.0."""
        model = build_workforce_model()
        clone = self._clone(model)

        self.assertTrue(clone.stocks["headcount"].arrayed)
        self.assertTrue(clone.stocks["headcount"].named_arrayed)
        self.assertIs(clone.stocks["headcount"]["junior"], clone.stocks["headcount[junior]"])
        self.assertIs(model.stocks["headcount"]["junior"], model.stocks["headcount[junior]"])

    def test_the_clone_has_points_of_its_own(self):
        model = _every_kind_model()
        clone = self._clone(model)

        clone.points["curve"] = [(0.0, 9.0)]
        self.assertEqual(model.points["curve"], [(0.0, 1.0), (6.0, 4.0)])

    def test_the_clone_runs_as_the_original_on_python(self):
        for model, equations in ((_every_kind_model(), _EVERY_KIND),
                                 (build_workforce_model(), ["headcount[junior]", "headcount[senior]",
                                                            "total_cost", "average_salary"])):
            with self.subTest(model=model.name):
                clone = self._clone(model)
                assert_frame_equal(clone.simulate(equations), model.simulate(equations))

    @pytest.mark.requires_rust
    def test_the_clone_runs_as_the_original_on_rust(self):
        model = _every_kind_model()
        clone = self._clone(model)
        # The engine returns its columns in no fixed order.
        assert_frame_equal(clone.simulate(_EVERY_KIND, backend="rust")[_EVERY_KIND],
                           model.simulate(_EVERY_KIND, backend="rust")[_EVERY_KIND])

    def test_the_clone_starts_with_an_empty_memo(self):
        model = _every_kind_model()
        model.simulate(_EVERY_KIND)
        clone = self._clone(model)

        self.assertTrue(all(len(clone.memo.get(name, {})) == 0 for name in _EVERY_KIND))

    def test_a_change_to_the_clone_leaves_the_original_alone(self):
        model = _every_kind_model()
        before = model.simulate(_EVERY_KIND)
        clone = self._clone(model)

        clone.constants["start"].equation = 99.0
        clone.constants["rate"].equation = 3.0
        model.reset_cache()

        assert_frame_equal(model.simulate(_EVERY_KIND), before)
        self.assertEqual(clone.simulate(["from_constant"]).iloc[0, 0], 99.0)


class TestScenariosOfARegisteredModel(unittest.TestCase):
    """The same through the public path: every scenario runs on its own clone, so its
    constants and points reach it and nothing else."""

    def _bptk(self, model):
        instance = BPTK_Py.bptk()
        instance.register_scenario_manager({"mgr": {"model": model}})
        instance.register_scenarios(scenarios={
            "base": {},
            "low": {"constants": {"start": 1.0}, "points": {"curve": [[0.0, 10.0], [6.0, 10.0]]}},
            "high": {"constants": {"start": 50.0}, "points": {"curve": [[0.0, 20.0], [6.0, 20.0]]}},
        }, scenario_manager="mgr")
        return instance

    def _first_row(self, backend):
        df = self._bptk(_every_kind_model()).run_scenarios(
            scenario_managers=["mgr"], scenarios=["base", "low", "high"],
            equations=["from_constant", "from_expression", "inflow"], backend=backend)
        return df.iloc[0].to_dict()

    def _assert_first_row(self, row):
        # A stock's initial value follows the scenario's constant; the lookup is the
        # scenario's own; and the base scenario keeps the model's values.
        self.assertEqual(row["mgr_base_from_constant"], 10.0)
        self.assertEqual(row["mgr_low_from_constant"], 1.0)
        self.assertEqual(row["mgr_high_from_constant"], 50.0)
        self.assertEqual(row["mgr_low_from_expression"], 7.0)
        self.assertEqual(row["mgr_high_from_expression"], 105.0)
        self.assertEqual(row["mgr_base_inflow"], 0.5)
        self.assertEqual(row["mgr_low_inflow"], 5.0)
        self.assertEqual(row["mgr_high_inflow"], 10.0)

    def test_python(self):
        self._assert_first_row(self._first_row("python"))

    @pytest.mark.requires_rust
    def test_rust(self):
        self._assert_first_row(self._first_row("rust"))

    def _two_tables(self, backend):
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="two_tables")
        model.points["curve"] = [(0.0, 1.0), (2.0, 1.0)]
        model.points["other"] = [(0.0, 7.0), (2.0, 7.0)]
        model.converter("c").equation = sd.lookup(sd.time(), "curve")
        model.converter("o").equation = sd.lookup(sd.time(), "other")
        instance = BPTK_Py.bptk()
        instance.register_scenario_manager({"mgr": {"model": model}})
        instance.register_scenarios(scenarios={"one": {"points": {"curve": [[0.0, 10.0], [2.0, 10.0]]}}},
                                    scenario_manager="mgr")
        row = instance.run_scenarios(scenario_managers=["mgr"], scenarios=["one"], equations=["c", "o"],
                                     backend=backend).iloc[0].to_dict()
        self.assertEqual(row, {"c": 10.0, "o": 7.0})

    def test_a_scenario_overriding_one_table_keeps_the_others_on_python(self):
        """The scenario's points used to replace the model's, so every table it did not
        name was gone: 'Lookup of a table the model does not have'."""
        self._two_tables("python")

    @pytest.mark.requires_rust
    def test_a_scenario_overriding_one_table_keeps_the_others_on_rust(self):
        self._two_tables("rust")

    def test_the_registered_model_is_not_changed(self):
        model = _every_kind_model()
        self._bptk(model).run_scenarios(scenario_managers=["mgr"], scenarios=["low", "high"],
                                        equations=["inflow"])

        self.assertEqual(model.points["curve"], [(0.0, 1.0), (6.0, 4.0)])
        self.assertEqual(model.simulate(["from_constant", "inflow"]).iloc[0].to_dict(),
                         {"from_constant": 10.0, "inflow": 0.5})
