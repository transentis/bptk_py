import math
import unittest

import numpy as np

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
from BPTK_Py.sddsl.element import Element
from BPTK_Py.sddsl.functions import pulse, trend, smooth, delay
from BPTK_Py.sddsl.operators import OperatorError, Trend, And, Ln, Log10, Floor, Ceil, MaxOperator
from tests.helpers.stella import stella_results

class TestFunctions(unittest.TestCase):
    def test_pulse_errors(self):
        model = Model()
        for arguments in (("stringVolume", 0.0, 0.0), (1.0, "strinFirstPulse", 0.0), (1.0, 0.0, "stringInterval")):
            with self.assertRaisesRegex(TypeError, "an operand has to be an element, an expression or a number"):
                pulse(model, *arguments)

    def test_pulse_without_a_first_pulse_fires_once_at_the_start_time(self):
        # A first pulse of 0 never fired in a model starting later
        model = Model(starttime=1.0, stoptime=4.0, dt=0.5)
        stock = model.stock("stock")
        flow = model.flow("flow")
        flow.equation = sd.pulse(model, 20.0)
        stock.equation = flow
        self.assertEqual([flow(t) for t in np.arange(1.0, 4.5, 0.5)], [40.0] + [0.0] * 6)
        self.assertEqual(stock(4.0), 20.0)

    def test_trend(self):
        model = Model()

        trendOperator = trend(model=model, input_function= 1, averaging_time= 1, initial_trend = 1.0)
        self.assertIsInstance(trendOperator,Trend)

        with self.assertRaisesRegex(TypeError, "an operand has to be"):
            trend(model=model, input_function= 1, averaging_time= 1, initial_trend = "stringInitialTrend")

    def test_trend_starts_at_its_initial_trend(self):
        # XMILE: the third argument is the trend at the start, default 0
        model = Model(starttime=0, stoptime=10, dt=0.5)
        source = model.converter("source")
        source.equation = 4.0
        started = model.converter("started")
        started.equation = trend(model, source, 2.0, 0.25)
        flat = model.converter("flat")
        flat.equation = trend(model, source, 2.0)

        self.assertAlmostEqual(model.evaluate_equation("started", 0.0), 0.25)
        self.assertEqual(model.evaluate_equation("flat", 0.0), 0.0)      

    def test_smooth_error(self):
        model = Model()

        with self.assertRaisesRegex(TypeError, "an operand has to be"):
            smooth(model=model, input_function= 1, averaging_time= 1, initial_value = "stringInitialValue")

    def test_trunc_cuts_towards_zero_where_floor_rounds_down(self):
        model = Model(starttime=0, stoptime=1, dt=1)
        source = model.converter("source")
        source.equation = -2.5
        cut = model.converter("cut")
        cut.equation = sd.trunc(source)
        floored = model.converter("floored")
        floored.equation = sd.floor(source)
        positive = model.converter("positive")
        positive.equation = sd.trunc(2.5)

        self.assertEqual(model.evaluate_equation("cut", 0.0), -2.0)
        self.assertEqual(model.evaluate_equation("floored", 0.0), -3.0)
        self.assertEqual(model.evaluate_equation("positive", 0.0), 2.0)

    def test_smooth_without_initial_value_starts_at_the_input(self):
        model = Model(starttime=0, stoptime=10, dt=0.5)
        source = model.converter("source")
        source.equation = 7.0 + sd.step(10.0, 3.0)
        smoothed = model.converter("smoothed")
        smoothed.equation = smooth(model, source, 2.0)

        self.assertEqual(model.evaluate_equation("smoothed", 0.0), 7.0)
        self.assertEqual(model.evaluate_equation("smoothed", 2.5), 7.0)
        self.assertGreater(model.evaluate_equation("smoothed", 5.0), 7.0)

    def test_delay_errors(self):
        model = Model()
        inputFunction = Element(model=model,name="testElement",function_string=None)
        for arguments in (("stringInputFunction", 0.0), (inputFunction, "stringDelayDuration"),
                          (inputFunction, 0.0, "stringInitialValue")):
            with self.assertRaisesRegex(TypeError, "an operand has to be an element, an expression or a number"):
                delay(model, *arguments)

class TestXmileCascades(unittest.TestCase):
    """SMTH3/N, DELAY1/3/N, FORCST and NPV, built from stocks and biflows."""

    def _model(self, stoptime=40.0, dt=0.25):
        model = Model(starttime=0.0, stoptime=stoptime, dt=dt)
        source = model.converter("source")
        source.equation = 5.0 + sd.step(10.0, 3.0)
        return model, source

    def _values(self, model, name):
        return [model.evaluate_equation(name, t)
                for t in np.arange(model.starttime, model.stoptime + model.dt, model.dt)]

    def test_order_and_initial_value_are_checked(self):
        model, source = self._model()
        for order in (0, 256, 2.5, True):
            with self.assertRaisesRegex(OperatorError, "order must be a whole number"):
                sd.smoothn(model, source, 2.0, order)
            with self.assertRaisesRegex(OperatorError, "order must be a whole number"):
                sd.delayn(model, source, 2.0, order)
        for build in (sd.smooth3, sd.delay1, sd.delay3, sd.npv):
            with self.assertRaisesRegex(TypeError, "an operand has to be"):
                build(model, source, 2.0, "nine")
        with self.assertRaisesRegex(TypeError, "an operand has to be"):
            sd.forecast(model, source, 2.0, 5.0, "up")

    def test_without_an_initial_value_they_start_at_the_input(self):
        model, source = self._model()
        for name, build in [("s3", sd.smooth3), ("d1", sd.delay1), ("d3", sd.delay3)]:
            model.converter(name).equation = build(model, source, 2.0)
            self.assertEqual(model.evaluate_equation(name, 0.0), 5.0)

    def test_an_initial_value_is_where_they_start(self):
        model, source = self._model()
        model.converter("s3").equation = sd.smooth3(model, source, 2.0, 1.0)
        model.converter("d3").equation = sd.delay3(model, source, 2.0, 1.0)
        self.assertEqual(model.evaluate_equation("s3", 0.0), 1.0)
        self.assertAlmostEqual(model.evaluate_equation("d3", 0.0), 1.0)

    def test_with_a_constant_time_a_delay_behaves_like_the_smooth_of_its_order(self):
        model, source = self._model()
        model.converter("d1").equation = sd.delay1(model, source, 4.0)
        model.converter("s1").equation = sd.smooth(model, source, 4.0)
        model.converter("d3").equation = sd.delay3(model, source, 4.0)
        model.converter("s3").equation = sd.smooth3(model, source, 4.0)
        np.testing.assert_allclose(self._values(model, "d1"), self._values(model, "s1"))
        np.testing.assert_allclose(self._values(model, "d3"), self._values(model, "s3"))

    def test_a_material_delay_passes_on_everything_even_when_its_time_changes(self):
        model = Model(starttime=0.0, stoptime=80.0, dt=0.25)
        source = model.converter("source")
        source.equation = sd.pulse(model, 10.0, 1.0)
        delay_time = model.converter("delay_time")
        delay_time.equation = 2.0 + sd.step(6.0, 3.0)
        model.converter("d3").equation = sd.delay3(model, source, delay_time)
        model.converter("s3").equation = sd.smooth3(model, source, delay_time)

        passed_on = sum(self._values(model, "d3")) * model.dt
        smoothed = sum(self._values(model, "s3")) * model.dt
        self.assertAlmostEqual(passed_on, 10.0, places=3)
        self.assertNotAlmostEqual(smoothed, 10.0, places=1)

    def test_the_n_versions_keep_a_stage_at_least_dt_long(self):
        model, source = self._model(dt=0.25)
        model.converter("short_d").equation = sd.delayn(model, source, 1.0, 9)
        model.converter("long_d").equation = sd.delayn(model, source, 9 * 0.25, 9)
        model.converter("short_s").equation = sd.smoothn(model, source, 1.0, 9)
        model.converter("long_s").equation = sd.smoothn(model, source, 9 * 0.25, 9)
        np.testing.assert_allclose(self._values(model, "short_d"), self._values(model, "long_d"))
        np.testing.assert_allclose(self._values(model, "short_s"), self._values(model, "long_s"))

    def test_smoothn_of_order_three_is_smooth3(self):
        model, source = self._model()
        model.converter("s3").equation = sd.smooth3(model, source, 4.0)
        model.converter("sn").equation = sd.smoothn(model, source, 4.0, 3)
        np.testing.assert_allclose(self._values(model, "s3"), self._values(model, "sn"))

    def test_forecast_extrapolates_the_trend_over_the_horizon(self):
        model, source = self._model()
        model.converter("flat").equation = sd.forecast(model, source, 3.0, 10.0)
        model.converter("rising").equation = sd.forecast(model, source, 3.0, 10.0, 0.1)
        self.assertEqual(model.evaluate_equation("flat", 0.0), 5.0)
        self.assertAlmostEqual(model.evaluate_equation("rising", 0.0), 5.0 * (1 + 0.1 * 10.0))

    def test_npv_accumulates_the_discounted_input(self):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0)
        source = model.converter("source")
        source.equation = 100.0
        model.converter("undiscounted").equation = sd.npv(model, source, 0.0, 0.0)
        model.converter("discounted").equation = sd.npv(model, source, 0.1)
        self.assertEqual(model.evaluate_equation("undiscounted", 4.0), 400.0)
        # starts at the input; each step adds 100 / 1.1^(TIME - STARTTIME + DT)
        expected = 100.0 + sum(100.0 / 1.1 ** (t + 1) for t in range(4))
        self.assertAlmostEqual(model.evaluate_equation("discounted", 4.0), expected)


class TestStatelessXmileBuiltins(unittest.TestCase):
    """RAMP, MIN/MAX over n, SAFEDIV, ROOTN, PERCENT, PMT/FV/PV, CGROWTH, COUNTER,
    LOOKUPINV and LOOKUPAREA."""

    def _at(self, equation, t=0.0, model=None):
        model = model or Model(starttime=0.0, stoptime=20.0, dt=1.0)
        model.converter("out").equation = equation
        return model.evaluate_equation("out", t)

    def test_ramp_starts_rises_and_holds(self):
        model = Model(starttime=0.0, stoptime=20.0, dt=1.0)
        model.converter("open").equation = sd.ramp(2.0, 5.0)
        model.converter("closed").equation = sd.ramp(2.0, 5.0, 8.0)
        values = [(model.evaluate_equation("open", t), model.evaluate_equation("closed", t))
                  for t in (4.0, 5.0, 7.0, 10.0)]
        self.assertEqual(values, [(0.0, 0.0), (0.0, 0.0), (4.0, 4.0), (10.0, 6.0)])

    def test_max_and_min_take_any_number_of_arguments(self):
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0)
        x = model.converter("x")
        x.equation = 4.0
        self.assertEqual(self._at(sd.max(x, 9.0, -1.0, 3.0), model=model), 9.0)
        self.assertEqual(self._at(sd.min(x, 9.0, -1.0, 3.0), model=model), -1.0)
        # two arguments are the operator they always were
        self.assertIsInstance(sd.max(x, 1.0), MaxOperator)

    def test_safediv(self):
        self.assertEqual(self._at(sd.safediv(10.0, 4.0)), 2.5)
        self.assertEqual(self._at(sd.safediv(10.0, 0.0)), 0.0)
        self.assertEqual(self._at(sd.safediv(10.0, 0.0, -1.0)), -1.0)

    def test_rootn(self):
        self.assertEqual(self._at(sd.rootn(144.0, 2.0)), 12.0)
        self.assertAlmostEqual(self._at(sd.rootn(-27.0, 3.0)), -3.0)
        self.assertTrue(math.isnan(self._at(sd.rootn(-4.0, 2.0))))

    def test_percent(self):
        self.assertAlmostEqual(self._at(sd.percent(1.22)), 122.0)

    def test_isnan(self):
        self.assertEqual(self._at(sd.isnan(sd.nan())), 1.0)
        self.assertEqual(self._at(sd.isnan(sd.sqrt(-1.0))), 1.0)
        self.assertEqual(self._at(sd.isnan(3.0)), 0.0)

    def test_rework_sends_back_a_share_of_all_the_work(self):
        # Stella's run of `test_models/rework`: REWORK(10) is 0.0909, REWORK(50) 0.3333
        self.assertAlmostEqual(self._at(sd.rework(10.0)), 10.0 / 110.0)
        self.assertAlmostEqual(self._at(sd.rework(50.0)), 1.0 / 3.0)

    def test_logisticbound_takes_both_bounds_or_neither(self):
        with self.assertRaisesRegex(OperatorError, "x_start and x_finish together"):
            sd.logisticbound(1.0, 9.0, sd.time(), 5.0, 1.0, x_start=1.0)

    def test_the_bounded_and_soft_curves_as_stella_computes_them(self):
        """Stella's run of `test_models/stella_extras`, at every step from 0 to 12."""
        stella = stella_results("stella_extras")
        model = Model(starttime=0.0, stoptime=12.0, dt=0.5)
        t = sd.time()
        model.converter("input").equation = sd.sinwave(5.0, 6.0) + t
        expected = {
            "isnan number": sd.isnan(model.converters["input"]),
            "isnan nan": sd.isnan(sd.nan()),
            "expbound slow start": sd.expbound(1.0, 9.0, t, 2.0, 2.0, 8.0),
            "expbound linear": sd.expbound(1.0, 9.0, t, 0.0, 2.0, 8.0),
            "expbound fast start": sd.expbound(1.0, 9.0, t, -2.0, 2.0, 8.0),
            "logisticbound open": sd.logisticbound(1.0, 9.0, t, 5.0, 1.0),
            "logisticbound closed": sd.logisticbound(1.0, 9.0, t, 5.0, 1.0, 1.0, 10.0),
            "logisticbound linear": sd.logisticbound(1.0, 9.0, t, 5.0, 0.0, 1.0, 10.0),
            "maxsoft 1": sd.maxsoft(6.0 - t, 1.0, 2.0),
            "maxsoft hard": sd.maxsoft(6.0 - t, 1.0, 0.0),
            "maxsoft half": sd.maxsoft(6.0 - t, 1.0, 0.5),
            "maxsoft 5": sd.maxsoft(6.0 - t, 1.0, 5.0),
            "maxsoft equal": sd.maxsoft(t, t, 2.0),
            "minsoft 1": sd.minsoft(t, 7.0, 2.0),
            "minsoft half": sd.minsoft(t, 7.0, 0.5),
            "minsoft 5": sd.minsoft(t, 7.0, 5.0),
        }
        for column, equation in expected.items():
            name = column.replace(" ", "_")
            model.converter(name).equation = equation
            computed = [model.evaluate_equation(name, float(time)) for time in stella.index]
            np.testing.assert_allclose(computed, stella[column].values, atol=1e-9, err_msg=column)

    def test_the_financial_functions_agree_with_a_spreadsheet(self):
        self.assertAlmostEqual(self._at(sd.pmt(0.05, 10.0, 1000.0)), -129.5045749654566)
        self.assertAlmostEqual(self._at(sd.fv(0.05, 10.0, -100.0)), 1257.789253554884)
        self.assertAlmostEqual(self._at(sd.pv(0.05, 10.0, -100.0)), 772.1734929184817)
        self.assertAlmostEqual(self._at(sd.pmt(0.05, 10.0, 0.0, 1000.0)), -79.50457496545667)
        self.assertAlmostEqual(self._at(sd.fv(0.05, 10.0, 0.0, -1000.0)), 1628.894626777442)
        self.assertAlmostEqual(self._at(sd.pv(0.05, 10.0, 0.0, 1000.0)), -613.9132535407591)
        # without interest
        self.assertEqual(self._at(sd.pmt(0.0, 10.0, 1000.0)), -100.0)
        self.assertEqual(self._at(sd.fv(0.0, 10.0, -100.0, -50.0)), 1050.0)
        self.assertEqual(self._at(sd.pv(0.0, 10.0, -100.0)), 1000.0)

    def test_cgrowth_grows_a_stock_by_its_percentage_whatever_dt(self):
        for dt in (1.0, 0.25, 0.1):
            model = Model(starttime=0.0, stoptime=2.0, dt=dt)
            stock = model.stock("stock")
            stock.initial_value = 100.0
            growth = model.flow("growth")
            growth.equation = stock * sd.cgrowth(model, 10.0)
            stock.equation = growth
            self.assertAlmostEqual(model.evaluate_equation("stock", 2.0), 121.0)

    def test_counter_cycles_from_start_to_end(self):
        model = Model(starttime=1.0, stoptime=20.0, dt=1.0)
        model.converter("weekday").equation = sd.counter(model, 1.0, 8.0)
        self.assertEqual([model.evaluate_equation("weekday", t) for t in (1.0, 7.0, 8.0, 9.0)],
                         [1.0, 7.0, 1.0, 2.0])

    def test_lookupinv_finds_the_x_of_a_value(self):
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0)
        model.points["rising"] = [[0, 0], [2, 4], [4, 6]]
        falling = [[0, 10], [10, 0]]
        self.assertEqual(self._at(sd.lookupinv(5.0, "rising"), model=model), 3.0)
        self.assertEqual(self._at(sd.lookupinv(-1.0, "rising"), model=model), 0.0)
        self.assertEqual(self._at(sd.lookupinv(9.0, "rising"), model=model), 4.0)
        self.assertEqual(self._at(sd.lookupinv(2.5, falling), model=model), 7.5)
        self.assertEqual(self._at(sd.lookupinv(3.0, [[0, 3], [5, 3]]), model=model), 0.0)
        # On a table that is not monotonic a value it never reaches is NaN, as in Stella
        up_and_down = [[2, 3], [4, 5], [6, 7], [8, 6]]
        self.assertEqual(self._at(sd.lookupinv(6.5, up_and_down), model=model), 5.5)
        self.assertTrue(math.isnan(self._at(sd.lookupinv(1.0, up_and_down), model=model)))
        self.assertTrue(math.isnan(self._at(sd.lookupinv(10.0, up_and_down), model=model)))

    def test_lookuparea_integrates_the_table(self):
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0)
        model.points["table"] = [[0, 0], [2, 4], [4, 6]]
        self.assertEqual(self._at(sd.lookuparea("table"), model=model), 14.0)
        self.assertEqual(self._at(sd.lookuparea("table", 1.0, 3.0), model=model), 7.5)
        self.assertEqual(self._at(sd.lookuparea("table", 3.0, 1.0), model=model), -7.5)
        # As in Stella, nothing beyond its ends counts, though the table holds its end values there
        self.assertEqual(self._at(sd.lookuparea("table", 4.0, 6.0), model=model), 0.0)
        self.assertEqual(self._at(sd.lookuparea("table", -2.0, 6.0), model=model), 14.0)
        self.assertEqual(self._at(sd.lookuparea("table", 6.0, -2.0), model=model), -14.0)

    def _stella_tables(self):
        model = Model(starttime=0.0, stoptime=12.0, dt=0.5)
        model.points["peak"] = [(2, 0), (4, 5), (6, 20), (8, 10), (10, 0)]
        model.points["rising"] = [(0, 0), (2, 1), (4, 4), (6, 9), (8, 16)]
        model.points["steps"] = [(0, 0), (2, 1), (4, 4), (6, 9), (8, 9)]
        return model

    def _over_time(self, equation):
        model = self._stella_tables()
        model.converter("out").equation = equation
        return [round(float(model.evaluate_equation("out", float(t))), 6) for t in range(12)]

    def test_the_three_kinds_of_table_look_up_as_stella_does(self):
        """Stella's run of the same tables (`test_models/lookups`): an extrapolate table
        goes on along its end segments, a discrete one is a step function."""
        x = sd.time() * 2.0 - 3.0
        self.assertEqual(self._over_time(sd.lookup(x, "peak")),
                         [0, 0, 0, 2.5, 12.5, 15, 5, 0, 0, 0, 0, 0])
        self.assertEqual(self._over_time(sd.lookup(x, "peak", kind="extrapolate")),
                         [-12.5, -7.5, -2.5, 2.5, 12.5, 15, 5, -5, -15, -25, -35, -45])
        self.assertEqual(self._over_time(sd.lookup(x, "peak", kind="discrete")),
                         [0, 0, 0, 0, 5, 20, 10, 0, 0, 0, 0, 0])

    def test_the_inverse_and_the_area_of_each_kind_as_stella_computes_them(self):
        """Stella's run of the same tables (`test_models/lookup_kinds`): LOOKUPINV goes on
        along an extrapolate table's end segments and reads a discrete one as continuous;
        LOOKUPAREA integrates a discrete table's steps and an extrapolate table's lines
        beyond its ends."""
        self.assertEqual(self._over_time(sd.lookupinv(sd.time() * 2.0 - 2.0, "rising", kind="extrapolate")),
                         [-4, 0, 2.666667, 4, 4.8, 5.6, 6.285714, 6.857143, 7.428571, 8, 8.571429, 9.142857])
        self.assertEqual(self._over_time(sd.lookupinv(sd.time(), "steps", kind="discrete")),
                         [0, 2, 2.666667, 3.333333, 4, 4.4, 4.8, 5.2, 5.6, 6, 8, 8])
        self.assertEqual(self._over_time(sd.lookuparea("rising", -2.0, sd.time(), kind="extrapolate")),
                         [-1, -0.75, 0, 1.75, 5, 10.25, 18, 28.75, 43, 60.75, 82, 106.75])
        self.assertEqual(self._over_time(sd.lookuparea("steps", -2.0, sd.time(), kind="discrete")),
                         [0, 0, 0, 1, 2, 6, 10, 19, 28, 28, 28, 28])
        self.assertEqual(self._over_time(sd.lookuparea("steps", kind="discrete"))[0], 28)

    def test_lookup_statistics_as_stella_computes_them(self):
        """Stella's runs of the same tables (`test_models/stella_extras`).
        LOOKUPMEAN over a range ending inside a segment is the exception: Stella takes a wrong
        middle for the piece the range cuts off, the SD DSL that piece's own."""
        stella = stella_results("stella_extras")
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0)
        model.points["gf_shape"] = [(2, 0), (4, 5), (6, 20), (8, 10), (10, 0)]
        model.points["gf_const"] = [(x, 1.0) for x in (2, 4, 6, 8, 10)]
        model.points["gf_shape_from_0"] = [(0, 0), (2, 5), (4, 20), (6, 10), (8, 0)]
        cases = [
            (stella, "lookupmax 1", sd.lookupmax("gf_shape")),
            (stella, "lookupmin 1", sd.lookupmin("gf_shape")),
            (stella, "lookupmean 1", sd.lookupmean("gf_shape")),
            (stella, "lookupmax range", sd.lookupmax("gf_shape", 5.0, 3.0)),
            (stella, "lookupmin range 3 5", sd.lookupmin("gf_shape", 3.0, 5.0)),
            (stella, "lookupmean range", sd.lookupmean("gf_shape", None, 8.0)),
            (stella, "lookupmean const", sd.lookupmean("gf_const")),
            (stella, "lookupmean const 8", sd.lookupmean("gf_const", None, 8.0)),
            (stella, "lookupmean const 4", sd.lookupmean("gf_const", None, 4.0)),
            (stella, "lookupmean const 4 8", sd.lookupmean("gf_const", 8.0, 4.0)),
            (stella, "lookupmean const 6 10", sd.lookupmean("gf_const", 6.0, 10.0)),
            (stella, "lookupmean shape 4 8", sd.lookupmean("gf_shape", 4.0, 8.0)),
            (stella, "lookupmean shape 6", sd.lookupmean("gf_shape", None, 6.0)),
            (stella, "lookupmean shape from 0", sd.lookupmean("gf_shape_from_0")),
        ]
        for stella, column, equation in cases:
            self.assertAlmostEqual(self._at(equation, model=model), stella[column].iloc[0], places=9, msg=column)
        # Where the range cuts a segment, Stella's 2.75, 2.45 and 1.15
        self.assertAlmostEqual(self._at(sd.lookupmean("gf_const", 3.0, 5.0), model=model), 4.0)
        self.assertAlmostEqual(self._at(sd.lookupmean("gf_shape", 5.0, 3.0), model=model), 4.2)
        self.assertAlmostEqual(self._at(sd.lookupmean("gf_shape_from_0", 1.0, 3.0), model=model), 2.2)

    def test_lookup_statistics_at_the_edges(self):
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0)
        table = [(0, 1), (2, 3), (4, 0)]
        self.assertEqual(self._at(sd.lookupmax(table, 5.0, 9.0), model=model), 0.0)
        self.assertEqual(self._at(sd.lookupmin(table, -9.0, -5.0, kind="extrapolate"), model=model), -8.0)
        self.assertTrue(math.isnan(self._at(sd.lookupmean(table, 5.0, 9.0), model=model)))
        self.assertAlmostEqual(self._at(sd.lookupmean(table, kind="discrete"), model=model), 2.5)
        self.assertTrue(math.isnan(self._at(sd.lookupmax(table, sd.nan(), 1.0), model=model)))
        with self.assertRaisesRegex(OperatorError, "kind must be one of"):
            sd.lookupmean(table, kind="steps")

    def test_lookuprandom_draws_as_stella_does(self):
        """Stella's 10,001 draws (`test_models/random_dt_1`): mean and spread of each table."""
        stella = stella_results("random_dt_1")
        model = Model(starttime=0.0, stoptime=10000.0, dt=1.0)
        tables = {"lookuprandom 1": [(0, 0), (1, 1), (2, 2), (3, 1), (4, 0)],
                  "lookuprandom flat": [(x, 1.0) for x in range(5)],
                  "lookuprandom step": [(0, 0), (1, 0), (2, 1), (3, 1), (4, 1)]}
        for number, (column, table) in enumerate(tables.items()):
            name = "drawn_{}".format(number)
            model.converter(name).equation = sd.lookuprandom(table, seed=number)
            drawn = model.simulate([name])[name].values
            self.assertAlmostEqual(drawn.mean(), stella[column].mean(), delta=0.05, msg=column)
            self.assertAlmostEqual(drawn.std(), stella[column].std(), delta=0.03, msg=column)

    def test_normalpink_as_stella_draws_it(self):
        """Stella's 10,001 steps (`test_models/random_dt_1`): the noise starts from the mean,
        moves a fifth of the way to each new draw for a correlation time of 5, and a sample
        holds all of it. Bounds are the exception: Stella keeps a value it rejects and moves on
        from there, which pulls the mean towards the bound - 11.55 above 10, where the SD DSL
        draws again from the same value, 11.8."""
        stella = stella_results("random_dt_1")
        model = Model(starttime=0.0, stoptime=10000.0, dt=1.0)
        model.converter("pink").equation = sd.normalpink(model, 10.0, 2.0, 5.0, seed=7)
        model.converter("sampled").equation = sd.normalpink(model, 10.0, 2.0, 5.0, 7, sample=3.0)
        model.converter("bounded").equation = sd.normalpink(model, 10.0, 2.0, 5.0, 7, 10.0)
        model.converter("white").equation = sd.normalpink(model, 10.0, 2.0, 1.0, seed=7)
        model.converter("normal").equation = sd.normal(10.0, 2.0, seed=7)
        ours = model.simulate(["pink", "sampled", "bounded", "white", "normal"])
        for name, column in (("pink", "normalpink seeded"), ("sampled", "normalpink sample 3"), ("white", "normalpink corr 1")):
            x, s = ours[name].values, stella[column].values
            self.assertAlmostEqual(x.mean(), s.mean(), delta=0.15, msg=column)
            self.assertAlmostEqual(x.std(), s.std(), delta=0.1, msg=column)
            self.assertAlmostEqual(np.corrcoef(x[:-1], x[1:])[0, 1], np.corrcoef(s[:-1], s[1:])[0, 1], delta=0.03, msg=column)
        self.assertEqual(np.count_nonzero(np.diff(ours["sampled"].values)), 3333)
        self.assertEqual(list(ours["white"].values), list(ours["normal"].values))
        # The first value is a fifth of the way from the mean to the first draw
        first_draw = model.converters[[name for name in model.converters if name.endswith("normalpink_draw")][0]]
        self.assertAlmostEqual(ours["pink"].values[0], 8.0 + 0.2 * first_draw(0.0))
        self.assertGreaterEqual(ours["bounded"].min(), 10.0)
        self.assertAlmostEqual(ours["bounded"].mean(), 11.8, delta=0.1)

    def test_the_running_statistics_as_stella_computes_them(self):
        """Stella's runs (`test_models/stella_extras`), at every step."""
        stella = stella_results("stella_extras")
        model = Model(starttime=0.0, stoptime=12.0, dt=0.5)
        t = sd.time()
        source = model.converter("input")
        source.equation = sd.sinwave(5.0, 6.0) + t
        cases = [
            (stella, "runcum 1", sd.runcum(model, source)),
            (stella, "runcum as stock", sd.runcum(model, source, sd.starttime(model), t - sd.dt(model))),
            (stella, "runcum window", sd.runcum(model, source, t - 2.0, t)),
            (stella, "runmax 1", sd.runmax(model, source)),
            (stella, "runmin 1", sd.runmin(model, source)),
            (stella, "runmean 1", sd.runmean(model, source)),
            (stella, "runmean window", sd.runmean(model, source, t - 3.0, t)),
            (stella, "runmax window", sd.runmax(model, source, t - 2.0, t)),
            (stella, "runmin window", sd.runmin(model, source, t - 2.0, t)),
            (stella, "runcumtarget constant", sd.runcumtarget(model, 1.0, 6.0)),
            (stella, "runcumtarget falling", sd.runcumtarget(model, 6.0 - t, 10.0)),
            (stella, "runcumtarget never", sd.runcumtarget(model, 1.0, 100.0)),
            (stella, "runcumtarget const 7", sd.runcumtarget(model, 2.0, 7.0)),
            (stella, "runcumtarget step 10", sd.runcumtarget(model, sd.step(4.0, 3.0), 10.0)),
            (stella, "runcumtarget ramp 3", sd.runcumtarget(model, t, 3.0)),
            (stella, "runcumtarget pulse 4", sd.runcumtarget(model, sd.If(t == 2.0, 10.0, 0.0), 4.0)),
            # The negative values of the sine count with their magnitude
            (stella, "runcumtarget sin 20", sd.runcumtarget(model, source, 20.0)),
            (stella, "runcumtarget sin 30", sd.runcumtarget(model, source, 30.0)),
        ]
        for number, (stella, column, equation) in enumerate(cases):
            name = "case_{}".format(number)
            model.converter(name).equation = equation
            computed = [model.evaluate_equation(name, float(time)) for time in stella.index]
            np.testing.assert_allclose(computed, stella[column].values, atol=1e-9, err_msg=column)

    def test_a_running_statistic_of_an_empty_window_or_a_nan_bound_is_nan(self):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0)
        self.assertTrue(math.isnan(self._at(sd.runcum(model, sd.time(), 3.0, 2.0), 3.0, model)))
        self.assertTrue(math.isnan(self._at(sd.runmax(model, sd.time(), sd.nan()), 3.0, model)))
        self.assertTrue(math.isnan(self._at(sd.runcumtarget(model, sd.time(), sd.nan()), 3.0, model)))
        # A target of 0 is reached at the start, also by a stream of 0
        self.assertEqual(self._at(sd.runcumtarget(model, 0.0, 0.0), 3.0, model), 0.0)

    def test_the_edges_of_the_kinds(self):
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0)
        # One point: nothing to extrapolate along
        self.assertEqual(self._at(sd.lookup(5.0, [(3, 7)], kind="extrapolate"), model=model), 7.0)
        self.assertEqual(self._at(sd.lookup(1.0, [(3, 7)], kind="discrete"), model=model), 7.0)
        self.assertTrue(math.isnan(self._at(sd.lookup(sd.nan(), [(0, 1), (1, 2)], kind="discrete"), model=model)))
        # A flat end segment cannot be followed, so the inverse stays at the end
        flat_end = [(0, 0), (2, 4), (4, 4)]
        self.assertEqual(self._at(sd.lookupinv(9.0, flat_end, kind="extrapolate"), model=model), 4.0)
        # A falling table extrapolates at the end nearer to the value
        falling = [(0, 10), (5, 4), (10, 1)]
        self.assertAlmostEqual(self._at(sd.lookupinv(-2.0, falling, kind="extrapolate"), model=model), 15.0)
        self.assertAlmostEqual(self._at(sd.lookupinv(13.0, falling, kind="extrapolate"), model=model), -2.5)
        self.assertEqual(self._at(sd.lookuparea([(0, 1), (2, 3)], 5.0, 1.0, kind="discrete"), model=model), -1.0)
        self.assertTrue(math.isnan(self._at(sd.lookuparea([(0, 1), (2, 3)], sd.nan(), 1.0, kind="extrapolate"),
                                            model=model)))

    def test_bounds_report_what_cannot_be_met(self):
        import io, contextlib
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0)
        model.converter("reversed").equation = sd.normal(0.0, 1.0, 3, 1.0, -1.0)
        model.converter("out_of_reach").equation = sd.normal(0.0, 1.0, None, 10.0, 11.0)
        model.converter("bad_seed").equation = sd.normal(0.0, 1.0, -1, 0.0, 1.0)
        model.converter("bad_stddev").equation = sd.normal(0.0, -1.0, 3, 0.0, 1.0)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            for name in ("reversed", "out_of_reach", "bad_seed", "bad_stddev"):
                self.assertTrue(math.isnan(model.evaluate_equation(name, 0.0)), name)
        printed = output.getvalue()
        self.assertIn("normal in 'reversed' at t=0.0: minimum must not be greater than maximum "
                      "(minimum=1.0, maximum=-1.0)", printed)
        self.assertIn("normal in 'out_of_reach' at t=0.0: no draw lies within minimum and maximum "
                      "in 100 draws (minimum=10.0, maximum=11.0)", printed)
        self.assertIn("seed must be a whole number of at least 0", printed)
        self.assertIn("stddev must not be negative", printed)

    def test_a_sample_begins_at_whole_steps_counted_from_the_start(self):
        from BPTK_Py.sddsl.sddsl_builtins import sample_start
        model = Model(starttime=0.5, stoptime=10.0, dt=0.25)
        self.assertEqual([sample_start(model, t, 1.0) for t in (0.5, 1.25, 1.5, 2.25)], [0.5, 0.5, 1.5, 1.5])
        self.assertEqual([sample_start(model, t, 0.6) for t in (0.75, 1.0, 1.25)], [0.5, 1.0, 1.0])
        self.assertEqual([sample_start(model, 1.25, sample) for sample in (0.0, 0.1, 0.3, math.nan)], [1.25] * 4)

    def test_a_kind_xmile_does_not_have_is_refused_when_the_equation_is_built(self):
        for build in (lambda kind: sd.lookup(1.0, "table", kind=kind),
                      lambda kind: sd.lookupinv(1.0, "table", kind=kind),
                      lambda kind: sd.lookuparea("table", kind=kind)):
            with self.assertRaisesRegex(OperatorError, "kind must be one of continuous, extrapolate, discrete"):
                build("stepwise")


class TestBuiltinsOverThePast(unittest.TestCase):
    """INIT, PREVIOUS, HISTORY, DERIVN and IRR read what a variable was earlier."""

    def _model(self):
        model = Model(starttime=1.0, stoptime=12.0, dt=0.5)
        squared = model.converter("squared")
        squared.equation = sd.time() ** 2.0
        return model, squared

    def test_init_is_the_value_at_the_start(self):
        model, squared = self._model()
        model.converter("start").equation = sd.init(model, squared)
        model.converter("start_of_expression").equation = sd.init(model, squared * 2.0)
        self.assertEqual(model.evaluate_equation("start", 6.0), 1.0)
        self.assertEqual(model.evaluate_equation("start_of_expression", 6.0), 2.0)

    def test_previous_is_one_step_back_and_its_initial_value_at_the_start(self):
        model, squared = self._model()
        model.converter("before").equation = sd.previous(model, squared, -1.0)
        counter = model.converter("counter")
        counter.equation = sd.previous(model, counter, 0.0) + 1.0
        self.assertEqual(model.evaluate_equation("before", 1.0), -1.0)
        self.assertEqual(model.evaluate_equation("before", 4.0), 3.5 ** 2)
        self.assertEqual(model.evaluate_equation("counter", 3.0), 5.0)

    def test_history_is_the_value_at_a_time_of_the_run_so_far(self):
        model, squared = self._model()
        model.converter("at_3").equation = sd.history(model, squared, 3.0)
        model.converter("before_start").equation = sd.history(model, squared, 0.0)
        self.assertEqual(model.evaluate_equation("at_3", 2.0), 0.0)
        self.assertEqual(model.evaluate_equation("at_3", 6.0), 9.0)
        self.assertEqual(model.evaluate_equation("before_start", 6.0), 0.0)

    def test_derivn(self):
        model, squared = self._model()
        model.converter("zeroth").equation = sd.derivn(model, squared, 0)
        model.converter("second").equation = sd.derivn(model, squared, 2)
        self.assertEqual(model.evaluate_equation("zeroth", 4.0), 16.0)
        self.assertEqual(model.evaluate_equation("second", 1.5), 0.0)
        self.assertEqual(model.evaluate_equation("second", 4.0), 2.0)
        for order in (-1, 1.5, True):
            with self.assertRaisesRegex(OperatorError, "order must be a whole number"):
                sd.derivn(model, squared, order)

    def test_irr_matches_stellas_example(self):
        # -100 in the first year, 10 in each after it: 7.4 % after twenty years
        model = Model(starttime=1.0, stoptime=40.0, dt=1.0)
        stream = model.converter("stream")
        stream.equation = sd.If(sd.time() < 2.0, -100.0, 10.0)
        model.converter("rate").equation = sd.irr(model, stream)
        model.converter("rate_or_missing").equation = sd.irr(model, stream, -1.0)
        self.assertTrue(math.isnan(model.evaluate_equation("rate", 1.0)))
        self.assertEqual(model.evaluate_equation("rate_or_missing", 1.0), -1.0)
        self.assertAlmostEqual(model.evaluate_equation("rate", 20.0), 0.0744, places=4)

    def test_irr_without_a_solution_is_missing(self):
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0)
        stream = model.converter("stream")
        stream.equation = 10.0
        nothing = model.converter("nothing")
        nothing.equation = 0.0
        model.converter("rate").equation = sd.irr(model, stream, -1.0)
        model.converter("rate_of_nothing").equation = sd.irr(model, nothing, -1.0)
        self.assertEqual(model.evaluate_equation("rate", 5.0), -1.0)
        self.assertEqual(model.evaluate_equation("rate_of_nothing", 5.0), -1.0)

    def test_irr_finds_a_rate_that_falls_on_its_search_grid(self):
        # -100, then 200: exactly 100 %
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0)
        stream = model.converter("stream")
        stream.equation = sd.If(sd.time() < 1.0, -100.0, 200.0)
        model.converter("rate").equation = sd.irr(model, stream)
        self.assertAlmostEqual(model.evaluate_equation("rate", 1.0), 1.0)

    def test_irr_of_an_array_is_one_rate_per_index(self):
        model = Model(starttime=1.0, stoptime=20.0, dt=1.0)
        stream = model.converter("stream")
        stream.setup_vector(2, 0.0)
        stream[0].equation = sd.If(sd.time() < 2.0, -100.0, 10.0)
        stream[1].equation = sd.If(sd.time() < 2.0, -100.0, 20.0)
        rates = model.converter("rates")
        rates.equation = sd.irr(model, stream)
        self.assertLess(model.evaluate_equation("rates[0]", 20.0),
                        model.evaluate_equation("rates[1]", 20.0))


class TestLnLog10FloorCeil(unittest.TestCase):
    """Tests for the ln, log10, floor, ceil SD DSL operators."""

    def _eval(self, equation, constant_val):
        """Helper: build a model with a constant and a converter using the equation, return converter value at t=1."""
        model = Model(starttime=1, stoptime=2, dt=1, name="test")
        c = model.constant("c")
        c.equation = constant_val
        out = model.converter("out")
        out.equation = equation(c)
        return out(1)

    def test_ln_of_e(self):
        result = self._eval(sd.ln, math.e)
        self.assertAlmostEqual(result, 1.0, places=10)

    def test_ln_of_1(self):
        result = self._eval(sd.ln, 1.0)
        self.assertAlmostEqual(result, 0.0, places=10)

    def test_ln_of_scalar(self):
        """ln should work with a scalar constant."""
        model = Model(starttime=1, stoptime=2, dt=1, name="test")
        c = model.constant("c")
        c.equation = 10.0
        out = model.converter("out")
        out.equation = sd.ln(c)
        self.assertAlmostEqual(out(1), math.log(10.0), places=10)

    def test_log10_of_100(self):
        result = self._eval(sd.log10, 100.0)
        self.assertAlmostEqual(result, 2.0, places=10)

    def test_log10_of_1(self):
        result = self._eval(sd.log10, 1.0)
        self.assertAlmostEqual(result, 0.0, places=10)

    def test_log10_of_1000(self):
        result = self._eval(sd.log10, 1000.0)
        self.assertAlmostEqual(result, 3.0, places=10)

    def test_floor_positive(self):
        result = self._eval(sd.floor, 3.7)
        self.assertAlmostEqual(result, 3.0, places=10)

    def test_floor_negative(self):
        result = self._eval(sd.floor, -2.3)
        self.assertAlmostEqual(result, -3.0, places=10)

    def test_floor_integer(self):
        result = self._eval(sd.floor, 5.0)
        self.assertAlmostEqual(result, 5.0, places=10)

    def test_ceil_positive(self):
        result = self._eval(sd.ceil, 3.2)
        self.assertAlmostEqual(result, 4.0, places=10)

    def test_ceil_negative(self):
        result = self._eval(sd.ceil, -2.7)
        self.assertAlmostEqual(result, -2.0, places=10)

    def test_ceil_integer(self):
        result = self._eval(sd.ceil, 5.0)
        self.assertAlmostEqual(result, 5.0, places=10)

    def test_ln_of_element_reference(self):
        """ln of another converter (not just a constant)."""
        model = Model(starttime=1, stoptime=5, dt=1, name="test")
        inp = model.converter("inp")
        inp.equation = sd.time()
        out = model.converter("out")
        out.equation = sd.ln(inp)
        for t in [1.0, 2.0, 3.0, 4.0, 5.0]:
            self.assertAlmostEqual(out(t), math.log(t), places=10)

    def test_composition_floor_of_ln(self):
        """floor(ln(x)) — composing two new operators."""
        model = Model(starttime=1, stoptime=2, dt=1, name="test")
        c = model.constant("c")
        c.equation = 10.0
        out = model.converter("out")
        out.equation = sd.floor(sd.ln(c))
        # ln(10) ≈ 2.302, floor → 2.0
        self.assertAlmostEqual(out(1), 2.0, places=10)

    def test_operator_classes_exist(self):
        """Verify operator classes can be instantiated directly."""
        self.assertIsInstance(Ln(1.0), Ln)
        self.assertIsInstance(Log10(1.0), Log10)
        self.assertIsInstance(Floor(1.0), Floor)
        self.assertIsInstance(Ceil(1.0), Ceil)
