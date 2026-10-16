import math
import unittest

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
from BPTK_Py.exceptions import CyclicDependencyError
from BPTK_Py.sddsl.conveyor import Conveyor
from BPTK_Py.sddsl.element import ElementError
from BPTK_Py.sddsl.operators import OperatorError


def _cohorts(stoptime=60.0):
    """The age group 20 to 40: 100 enter a year, 2 % die and 1 % - from year 30 on 3 % -
    emigrate per year on the way."""
    model = Model(starttime=0.0, stoptime=stoptime, dt=1.0, name="cohorts")
    turning_20 = model.flow("turning_20")
    turning_20.equation = 100.0
    mortality_rate = model.constant("mortality_rate")
    mortality_rate.equation = 0.02
    emigration_rate = model.converter("emigration_rate")
    emigration_rate.equation = 0.01 + sd.step(0.02, 30)
    turning_40 = model.flow("turning_40")
    deaths = model.flow("deaths")
    emigration = model.flow("emigration")
    cohort = model.conveyor("aged_20_to_40")
    cohort.transit_time = 20
    cohort.initial_value = 1500.0
    cohort.inflows = [turning_20]
    cohort.outflows = [turning_40]
    cohort.leaks = {deaths: mortality_rate, emigration: emigration_rate}
    cohort.exponential_leak = True
    aged_40_plus = model.stock("aged_40_plus")
    aged_40_plus.inflows = [turning_40]
    return model


class TestAConveyorInAModel(unittest.TestCase):
    def test_the_age_group(self):
        model = _cohorts()

        self.assertAlmostEqual(model.evaluate_equation("turning_40", 25.0), 100.0 * 0.97 ** 20)
        self.assertAlmostEqual(model.evaluate_equation("deaths", 0.0), 30.0)
        self.assertAlmostEqual(model.evaluate_equation("emigration", 30.0) / model.evaluate_equation("emigration", 29.0), 3.0)
        self.assertAlmostEqual(model.evaluate_equation("turning_40", 60.0), 100.0 * 0.95 ** 20)
        self.assertAlmostEqual(model.evaluate_equation("aged_40_plus", 2.0),
                               model.evaluate_equation("turning_40", 0.0) + model.evaluate_equation("turning_40", 1.0))

    def test_what_enters_leaves_or_leaks(self):
        model = _cohorts(stoptime=10.0)
        for t in range(10):
            change = model.evaluate_equation("aged_20_to_40", t + 1.0) - model.evaluate_equation("aged_20_to_40", t)
            moved = 100.0 - sum(model.evaluate_equation(name, float(t))
                                for name in ("turning_40", "deaths", "emigration"))
            self.assertAlmostEqual(change, moved)

    def test_linear_leakage_is_the_default(self):
        model = Model(starttime=0.0, stoptime=20.0, dt=1.0, name="linear")
        inflow = model.flow("inflow")
        inflow.equation = 100.0
        out = model.flow("out")
        loss = model.flow("loss")
        belt = model.conveyor("belt")
        belt.transit_time = 4
        belt.initial_value = 0.0
        belt.inflows = [inflow]
        belt.outflows = [out]
        belt.leaks = {loss: 0.2}

        self.assertFalse(belt.exponential_leak)
        self.assertFalse(belt.fifo)
        self.assertEqual(belt.transit_time, 4)
        self.assertEqual(belt.inflows, [inflow])
        self.assertAlmostEqual(model.evaluate_equation("out", 10.0), 80.0)
        self.assertAlmostEqual(model.evaluate_equation("loss", 10.0), 20.0)

    def test_a_fifo_belt_speeds_up_with_a_shorter_transit_time(self):
        def outflow(fifo):
            model = Model(starttime=0.0, stoptime=16.0, dt=0.25, name="fifo")
            transit = model.converter("transit")
            transit.equation = sd.If(sd.time() < 8, 4.0, 2.0)
            inflow = model.flow("inflow")
            inflow.equation = 250.0
            out = model.flow("out")
            belt = model.conveyor("belt")
            belt.transit_time = transit
            belt.initial_value = 1000.0
            belt.inflows = [inflow]
            belt.outflows = [out]
            belt.fifo = fifo
            return [model.evaluate_equation("out", t) for t in (8.0, 10.0)]

        self.assertEqual(outflow(False), [250.0, 500.0])
        self.assertEqual(outflow(True), [500.0, 250.0])

    def test_an_initial_list_leaves_first_value_first(self):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="list")
        out = model.flow("out")
        belt = model.conveyor("belt")
        belt.transit_time = 3
        belt.initial_value = [1.0, 2.0, 3.0]
        belt.outflows = [out]

        self.assertEqual(belt.initial_value, [1.0, 2.0, 3.0])
        self.assertEqual([model.evaluate_equation("out", t) for t in range(4)], [1.0, 2.0, 3.0, 0.0])

    def test_an_initial_value_can_be_an_expression(self):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="expression")
        start = model.constant("start")
        start.equation = 30.0
        out = model.flow("out")
        belt = model.conveyor("belt")
        belt.transit_time = 3
        belt.initial_value = start * 2.0
        belt.outflows = [out]

        self.assertEqual(model.evaluate_equation("belt", 0.0), 60.0)
        self.assertEqual(model.evaluate_equation("out", 0.0), 20.0)

    def test_a_conveyor_feeding_a_conveyor(self):
        model = Model(starttime=0.0, stoptime=12.0, dt=1.0, name="chain")
        inflow = model.flow("inflow")
        inflow.equation = 10.0
        middle = model.flow("middle")
        out = model.flow("out")
        first = model.conveyor("first")
        first.transit_time = 2
        first.inflows = [inflow]
        first.outflows = [middle]
        second = model.conveyor("second")
        second.transit_time = 3
        second.inflows = [middle]
        second.outflows = [out]

        self.assertEqual([model.evaluate_equation("out", float(t)) for t in range(7)],
                         [0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 10.0])

    def test_a_conveyor_reaching_back_to_its_own_outflow_is_refused(self):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="cycle")
        out = model.flow("out")
        inflow = model.flow("inflow")
        inflow.equation = out * 0.5
        belt = model.conveyor("belt")
        belt.transit_time = 2
        belt.initial_value = 10.0
        belt.inflows = [inflow]
        belt.outflows = [out]

        with self.assertRaises(CyclicDependencyError) as context:
            model.evaluate_equation("out", 0.0)

        self.assertIn("out → inflow → out", str(context.exception))

    def test_reading_the_conveyor_does_not_create_a_cycle(self):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="reads")
        out = model.flow("out")
        belt = model.conveyor("belt")
        inflow = model.flow("inflow")
        inflow.equation = belt * 0.1
        belt.transit_time = 2
        belt.initial_value = 10.0
        belt.inflows = [inflow]
        belt.outflows = [out]

        self.assertAlmostEqual(model.evaluate_equation("belt", 1.0), 10.0 + 1.0 - 5.0)


class TestArrayedConveyors(unittest.TestCase):
    def _regions(self):
        model = Model(starttime=0.0, stoptime=10.0, dt=0.5, name="regions")
        belt = model.conveyor("belt")
        belt.setup_named_vector({"north": 0.0, "south": 0.0})
        inflow = model.flow("inflow")
        inflow.setup_named_vector({"north": 10.0, "south": 20.0})
        return model, belt, inflow

    def test_each_cell_has_a_belt_of_its_own(self):
        model, belt, inflow = self._regions()
        rate = model.constant("rate")
        rate.equation = 0.1
        out = model.flow("out")
        loss = model.flow("loss")
        belt["north"].initial_value = [1.0, 2.0, 3.0]
        belt["south"].initial_value = 60.0
        belt.transit_time = 3
        belt.inflows = [inflow]
        belt.outflows = [out]
        belt.leaks = {loss: rate}

        self.assertEqual(model.evaluate_equation("belt[north]", 0.0), 6.0)
        self.assertEqual(model.evaluate_equation("belt[south]", 0.0), 60.0)
        self.assertAlmostEqual(model.evaluate_equation("out[north]", 10.0), 9.0)
        self.assertAlmostEqual(model.evaluate_equation("out[south]", 10.0), 18.0)
        self.assertTrue(out.arrayed)

    def test_an_initial_value_of_the_whole_applies_to_every_cell(self):
        model, belt, inflow = self._regions()
        out = model.flow("out")
        belt.initial_value = [5.0]
        belt.transit_time = 1
        belt.outflows = [out]

        self.assertEqual(model.evaluate_equation("belt[north]", 0.0), 5.0)
        self.assertEqual(model.evaluate_equation("belt[south]", 0.0), 5.0)

    def test_transit_times_and_fractions_per_cell(self):
        model, belt, inflow = self._regions()
        transit = model.constant("transit")
        transit.setup_named_vector({"north": 1.0, "south": 2.0})
        rate = model.constant("rate")
        rate.setup_named_vector({"north": 0.0, "south": 0.5})
        out = model.flow("out")
        loss = model.flow("loss")
        belt.transit_time = transit
        belt.inflows = [inflow]
        belt.outflows = [out]
        belt.leaks = {loss: rate}

        self.assertEqual(model.evaluate_equation("out[north]", 1.0), 10.0)
        self.assertEqual(model.evaluate_equation("out[south]", 1.0), 0.0)
        self.assertAlmostEqual(model.evaluate_equation("out[south]", 2.0), 10.0)

    def test_a_cell_set_after_the_whole_keeps_its_own_start(self):
        model, belt, inflow = self._regions()
        out = model.flow("out")
        belt.initial_value = [5.0]
        belt["south"].initial_value = [7.0]
        belt.transit_time = 1
        belt.outflows = [out]

        self.assertEqual(model.evaluate_equation("belt[north]", 0.0), 5.0)
        self.assertEqual(model.evaluate_equation("belt[south]", 0.0), 7.0)
        self.assertIs(belt.add_arr_empty("north"), belt["north"])

    def test_a_matrix(self):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="matrix")
        belt = model.conveyor("belt")
        belt.setup_matrix([2, 2], [[1.0, 2.0], [3.0, 4.0]])
        out = model.flow("out")
        belt.transit_time = 1
        belt.outflows = [out]

        self.assertEqual(model.evaluate_equation("out[1][0]", 0.0), 3.0)

    def test_an_arrayed_expression_needs_an_element_of_its_own(self):
        model, belt, inflow = self._regions()

        with self.assertRaises(ElementError) as context:
            belt.transit_time = inflow * 0.1

        self.assertIn("arrayed expression", str(context.exception))

    def test_elements_of_another_shape_are_refused(self):
        model, belt, inflow = self._regions()
        other = model.flow("other")
        other.setup_vector(3, [1.0, 1.0, 1.0])

        with self.assertRaises(ElementError) as context:
            belt.inflows = [other]

        self.assertIn("different shapes", str(context.exception))

    def test_agecount_per_cell(self):
        model, belt, inflow = self._regions()
        out = model.flow("out")
        belt.transit_time = 3
        belt.inflows = [inflow]
        belt.outflows = [out]
        young = model.converter("young")
        young.equation = sd.agecount(belt, 0, 1)

        self.assertAlmostEqual(model.evaluate_equation("young[north]", 5.0), 10.0)
        self.assertAlmostEqual(model.evaluate_equation("young[south]", 5.0), 20.0)


class TestAgecount(unittest.TestCase):
    def test_counts_the_material_by_its_time_on_the_belt(self):
        model = _cohorts()
        model.converter("youngest").equation = sd.agecount(model.stocks["aged_20_to_40"], 0, 5)
        model.converter("all").equation = sd.agecount(model.stocks["aged_20_to_40"], 0, 20)

        self.assertAlmostEqual(model.evaluate_equation("all", 25.0), model.evaluate_equation("aged_20_to_40", 25.0))
        self.assertAlmostEqual(model.evaluate_equation("youngest", 25.0),
                               sum(100.0 * 0.97 ** age for age in range(5)))

    def test_only_a_conveyor_has_ages(self):
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0, name="no_conveyor")

        with self.assertRaises(OperatorError):
            sd.agecount(model.stock("stock"), 0, 1)


class TestDrivenFlows(unittest.TestCase):
    """The outflow and the leaks of a conveyor get their values from the belt."""

    def _belt(self):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="driven")
        belt = model.conveyor("belt")
        belt.transit_time = 2
        return model, belt

    def test_a_driven_flow_takes_no_equation(self):
        model, belt = self._belt()
        out = model.flow("out")
        belt.outflows = [out]

        with self.assertRaises(ElementError) as context:
            out.equation = 1.0

        self.assertIn("driven by conveyor 'belt'", str(context.exception))

    def test_a_flow_with_an_equation_is_not_taken(self):
        model, belt = self._belt()
        loss = model.flow("loss")
        loss.equation = 1.0

        with self.assertRaises(ElementError) as context:
            belt.leaks = {loss: 0.1}

        self.assertIn("loss.equation = None", str(context.exception))

    def test_a_flow_let_go_is_an_ordinary_flow_again(self):
        model, belt = self._belt()
        out = model.flow("out")
        other = model.flow("other")
        belt.outflows = [out]
        belt.outflows = [other]

        out.equation = 3.0

        self.assertEqual(model.evaluate_equation("out", 0.0), 3.0)
        self.assertEqual(belt.outflows, [other])

    def test_a_flow_is_driven_by_one_conveyor_and_once(self):
        model, belt = self._belt()
        out = model.flow("out")
        belt.outflows = [out]

        with self.assertRaises(ElementError) as context:
            model.conveyor("second").outflows = [out]
        self.assertIn("already driven by conveyor 'belt'", str(context.exception))

        with self.assertRaises(ElementError) as context:
            belt.leaks = {out: 0.1}
        self.assertIn("named twice", str(context.exception))

    def test_the_leaks_read_back_as_given(self):
        model, belt = self._belt()
        loss = model.flow("loss")
        belt.leaks = {loss: 0.1}

        self.assertEqual(list(belt.leaks.items()), [(loss, 0.1)])


class TestWhatAConveyorRefuses(unittest.TestCase):
    def setUp(self):
        self.model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="refusals")
        self.belt = self.model.conveyor("belt")

    def refuses(self, assign, words):
        with self.assertRaises(ElementError) as context:
            assign()
        self.assertIn(words, str(context.exception))

    def test_an_equation(self):
        self.refuses(lambda: setattr(self.belt, "equation", 1.0), "has no equation")
        self.assertIsNone(self.belt.equation)

    def test_non_negative(self):
        self.assertTrue(self.belt.non_negative)
        self.refuses(lambda: setattr(self.belt, "non_negative", True), "never falls below zero")

    def test_a_biflow_or_a_converter_as_inflow(self):
        self.refuses(lambda: setattr(self.belt, "inflows", [self.model.biflow("both")]), "have to be flows")
        self.refuses(lambda: setattr(self.belt, "inflows", [self.model.converter("c")]), "have to be flows")

    def test_more_than_one_outflow_or_one_that_is_no_flow(self):
        flows = [self.model.flow("a"), self.model.flow("b")]
        self.refuses(lambda: setattr(self.belt, "outflows", flows), "one outflow")
        self.refuses(lambda: setattr(self.belt, "outflows", [self.model.biflow("both")]), "have to be flows")

    def test_leaks_that_are_no_dict_or_have_no_fraction(self):
        self.refuses(lambda: setattr(self.belt, "leaks", [self.model.flow("a")]), "are a dict")
        self.refuses(lambda: setattr(self.belt, "leaks", {self.model.flow("a"): "x"}), "leak fraction")

    def test_a_transit_time_that_is_no_value_or_not_positive(self):
        self.refuses(lambda: setattr(self.belt, "transit_time", "x"), "has to be a number")
        self.refuses(lambda: setattr(self.belt, "transit_time", 0), "greater than zero")

    def test_an_initial_value_that_is_no_value_or_a_list_of_other_things(self):
        self.refuses(lambda: setattr(self.belt, "initial_value", "x"), "has to be a number")
        self.refuses(lambda: setattr(self.belt, "initial_value", []), "has to hold numbers")
        self.refuses(lambda: setattr(self.belt, "initial_value", [1.0, "x"]), "has to hold numbers")

    def test_flags_that_are_no_booleans(self):
        self.refuses(lambda: setattr(self.belt, "fifo", 1), "True or False")
        self.refuses(lambda: setattr(self.belt, "exponential_leak", "yes"), "True or False")

    def test_a_run_without_transit_time_or_outflow(self):
        self.refuses(lambda: self.model.evaluate_equation("belt", 0.0), "no transit time")
        self.belt.transit_time = 2
        self.refuses(lambda: self.model.evaluate_equation("belt", 0.0), "no outflow")

    def test_a_transit_time_or_fraction_that_becomes_invalid(self):
        transit = self.model.converter("transit")
        transit.equation = sd.If(sd.time() < 2, 2.0, 0.0)
        rate = self.model.converter("rate")
        rate.equation = sd.If(sd.time() < 1, 0.1, -0.1)
        self.belt.transit_time = transit
        self.belt.outflows = [self.model.flow("out")]
        self.belt.leaks = {self.model.flow("loss"): rate}

        self.refuses(lambda: self.model.evaluate_equation("out", 1.0), "has to be zero or more")
        rate.equation = 0.1
        self.refuses(lambda: self.model.evaluate_equation("out", 2.0), "greater than zero")
        transit.equation = sd.nan()
        self.refuses(lambda: self.model.evaluate_equation("out", 0.0), "greater than zero")
        self.assertTrue(math.isnan(self.model.evaluate_equation("transit", 0.0)))

    def test_a_stock_of_the_same_name(self):
        self.model.stock("stock")
        with self.assertRaises(ValueError):
            self.model.conveyor("stock")
        self.assertIs(self.model.conveyor("belt"), self.belt)
        self.assertIsInstance(self.belt, Conveyor)


class TestScenarios(unittest.TestCase):
    def test_a_scenario_runs_its_own_copy(self):
        from BPTK_Py import bptk
        model = _cohorts(stoptime=10.0)
        runner = bptk()
        runner.register_model(model)
        runner.register_scenario_manager({"sm": {"model": model, "base_constants": {}}})
        runner.register_scenarios(scenario_manager="sm",
                                  scenarios={"base": {}, "deadly": {"constants": {"mortality_rate": 0.04}}})

        results = runner.plot_scenarios(scenario_managers=["sm"], scenarios=["base", "deadly"],
                                        equations=["deaths"], return_df=True)

        self.assertAlmostEqual(results["sm_base_deaths"][0.0], 30.0)
        self.assertAlmostEqual(results["sm_deadly_deaths"][0.0], 60.0)
