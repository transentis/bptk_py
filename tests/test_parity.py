"""
Parity tests: build SD DSL models in Python, serialize via to_json(),
run in both Python and Rust engines, and compare results at every timestep.

This verifies that the Rust engine produces identical results to the
Python SD DSL for all supported features.
"""

import contextlib
import inspect
import io
import math
import numpy as np
import operator
import random
import pytest
import BPTK_Py
from BPTK_Py import CyclicDependencyError, Model
from BPTK_Py import sd_functions as sd
from BPTK_Py.sddsl import json_serializer
from BPTK_Py.sddsl import operators as ops
from BPTK_Py.util import timerange
from BPTK_Py._rust_engine import RustSdEngine
from tests.helpers.parity import run_parity, rust_time_key


# ---------------------------------------------------------------------------
# Test: Basic arithmetic (from test_equations in test_sddsl.py)
# ---------------------------------------------------------------------------

class TestParityArithmetic:
    """Test basic arithmetic operations produce identical results."""

    def test_subtraction(self):
        model = Model(starttime=1, stoptime=1, dt=1, name='sub')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = 0.1
        b.equation = 1 - a
        run_parity(model, ['a', 'b'])

    def test_addition(self):
        model = Model(starttime=1, stoptime=1, dt=1, name='add')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = 0.1
        b.equation = 1 + a
        run_parity(model, ['a', 'b'])

    def test_multiplication(self):
        model = Model(starttime=1, stoptime=1, dt=1, name='mul')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = 0.1
        b.equation = 1 * a
        run_parity(model, ['a', 'b'])

    def test_division(self):
        model = Model(starttime=1, stoptime=1, dt=1, name='div')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = 0.1
        b.equation = 1 / a
        run_parity(model, ['a', 'b'])

    def test_power(self):
        model = Model(starttime=1, stoptime=1, dt=1, name='pow')
        a = model.constant('a')
        b = model.constant('b')
        c = model.converter('c')
        a.equation = 3.0
        b.equation = 2.0
        c.equation = a ** b
        run_parity(model, ['a', 'b', 'c'])

    def test_modulo(self):
        model = Model(starttime=1, stoptime=1, dt=1, name='mod')
        a = model.constant('a')
        b = model.constant('b')
        c = model.converter('c')
        a.equation = 5.0
        b.equation = 3.0
        c.equation = a % b
        run_parity(model, ['a', 'b', 'c'])

    def test_modulo_of_a_compound_operand(self):
        """(a + b) % b - the grouping has to survive into the term."""
        model = Model(starttime=1, stoptime=1, dt=1, name='mod_compound')
        a = model.constant('a')
        b = model.constant('b')
        c = model.converter('c')
        a.equation = 7.0
        b.equation = 3.0
        c.equation = (a + b) % b
        run_parity(model, ['a', 'b', 'c'])

    def test_modulo_takes_the_sign_of_the_divisor(self):
        """Floored, as Python's % and XMILE's MOD. The engine truncated, and so gave
        -2 for (0 - 2) % 3 where Python gives 1 - only a negative operand shows it."""
        model = Model(starttime=0, stoptime=6, dt=1, name='mod_signs')
        shifted = model.converter('shifted')
        shifted.equation = (sd.time() - 2.0) % 3.0
        negative_divisor = model.converter('negative_divisor')
        negative_divisor.equation = sd.time() % -3.0
        run_parity(model, ['shifted', 'negative_divisor'])

    def test_modulo_with_a_literal_on_the_left(self):
        model = Model(starttime=1, stoptime=1, dt=1, name='mod_reflected')
        a = model.constant('a')
        c = model.converter('c')
        a.equation = 7.0
        c.equation = 10.0 % a
        run_parity(model, ['a', 'c'])

    def test_mixed_arithmetic(self):
        """a * b where a = 0.1 and b = 1/a = 10 → c = 1.0."""
        model = Model(starttime=1, stoptime=1, dt=1, name='mixed')
        a = model.converter('a')
        b = model.converter('b')
        c = model.converter('c')
        a.equation = 0.1
        b.equation = 1 / a
        c.equation = a * b
        run_parity(model, ['a', 'b', 'c'])

    def test_negation(self):
        """Test unary negation (-element)."""
        model = Model(starttime=0, stoptime=5, dt=1, name='neg')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = sd.time()
        b.equation = -a
        run_parity(model, ['a', 'b'])


# ---------------------------------------------------------------------------
# Test: Temporal functions
# ---------------------------------------------------------------------------

class TestParityTemporal:
    """Test time, dt, starttime, stoptime functions."""

    def test_time_as_flow(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='time')
        stock = model.stock("stock")
        stock.initial_value = 0.0
        inflow = model.flow("inflow")
        inflow.equation = sd.time()
        stock.equation = inflow
        run_parity(model, ['stock', 'inflow'])

    def test_dt(self):
        model = Model(starttime=5.0, stoptime=12.0, dt=0.25, name='dt')
        dt_conv = model.converter("dt_conv")
        dt_conv.equation = sd.dt(model)
        run_parity(model, ['dt_conv'])

    def test_starttime(self):
        model = Model(starttime=5, stoptime=10, dt=0.25, name='starttime')
        st = model.converter("start_val")
        st.equation = sd.starttime(model)
        run_parity(model, ['start_val'])

    def test_stoptime(self):
        model = Model(starttime=5, stoptime=10, dt=0.25, name='stoptime')
        st = model.converter("stop_val")
        st.equation = sd.stoptime(model)
        run_parity(model, ['stop_val'])


# ---------------------------------------------------------------------------
# Test: Step function
# ---------------------------------------------------------------------------

class TestParityStep:
    """Test step function parity."""

    def test_step_as_converter(self):
        model = Model(starttime=1, stoptime=10, dt=1, name='step')
        step_conv = model.converter("step_val")
        step_conv.equation = sd.step(10.0, 5.0)
        run_parity(model, ['step_val'])

    def test_step_with_addition(self):
        """step combined with constant addition: 5 + step(15, 5)."""
        model = Model(starttime=0, stoptime=10, dt=1, name='step_add')
        a = model.converter("a")
        a.equation = 5.0 + sd.step(15, 5)
        run_parity(model, ['a'])

    def test_step_on_a_time_that_dt_does_not_hit_exactly(self):
        """With dt = 0.3 the fourth step is 0.8999999999999999 unrounded; the engine
        switched a step after the Python engine, whose times sit on the rounded grid."""
        model = Model(starttime=0, stoptime=1.5, dt=0.3, name='step_odd_dt')
        a = model.converter("a")
        a.equation = sd.step(1.0, 0.9)
        run_parity(model, ['a'])


# ---------------------------------------------------------------------------
# Test: Pulse function
# ---------------------------------------------------------------------------

class TestParityPulse:
    """Test pulse function parity including stock accumulation."""

    def test_pulse_with_stock(self):
        model = Model(starttime=0, stoptime=9, dt=0.5, name='pulse')
        stock = model.stock("stock")
        stock.initial_value = 0.0
        flow = model.flow("flow")
        flow.equation = sd.pulse(model, 9.0, 1.5, 3.0)
        stock.equation = flow
        run_parity(model, ['stock', 'flow'])

    def test_pulse_without_a_first_pulse_in_a_model_not_starting_at_0(self):
        model = Model(starttime=1, stoptime=5, dt=0.5, name='pulse_start')
        stock = model.stock("stock")
        stock.initial_value = 0.0
        flow = model.flow("flow")
        flow.equation = sd.pulse(model, 20.0)
        stock.equation = flow
        run_parity(model, ['stock', 'flow'])
        assert flow.plot(return_df=True)["flow"].tolist() == [40.0] + [0.0] * 8

    def test_a_pulse_time_between_two_steps_fires_in_the_later_one(self):
        """dt = 1, a pulse every 1.5 from 2: the one at 3.5 fires at 4, as in Stella - it
        was skipped, and its volume lost."""
        model = Model(starttime=1, stoptime=6, dt=1, name='pulse_off_grid')
        stock = model.stock("stock")
        stock.initial_value = 0.0
        flow = model.flow("flow")
        flow.equation = sd.pulse(model, 20.0, 2.0, 1.5)
        stock.equation = flow
        run_parity(model, ['stock', 'flow'])
        assert flow.plot(return_df=True)["flow"].tolist() == [0.0, 20.0, 0.0, 20.0, 20.0, 0.0]
        assert stock(6) == 60.0

    def test_pulse_whose_times_dt_does_not_hit_exactly(self):
        """dt = 0.1, a pulse every 0.3 from 0.2: 0.8 - 0.2 is not exactly 2 * 0.3, and the
        Python engine compared exactly and skipped that pulse."""
        model = Model(starttime=0, stoptime=1, dt=0.1, name='pulse_odd_dt')
        flow = model.converter("p")
        flow.equation = sd.pulse(model, 1.0, 0.2, 0.3)
        run_parity(model, ['p'])
        values = flow.plot(return_df=True)["p"]
        assert [round(t, 2) for t, v in values.items() if v] == [0.2, 0.5, 0.8]


# ---------------------------------------------------------------------------
# Test: Math functions
# ---------------------------------------------------------------------------

class TestParityMathFunctions:
    """Test abs, sqrt, exp, round, pi as converters."""

    def test_abs(self):
        model = Model(starttime=0.0, stoptime=10.0, dt=0.25, name='abs')
        inp = model.converter("input_val")
        inp.equation = sd.time() - 5
        abs_val = model.converter("abs_val")
        abs_val.equation = sd.abs(inp)
        run_parity(model, ['input_val', 'abs_val'])

    def test_sqrt(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='sqrt')
        f = model.converter("sqrt_val")
        f.equation = sd.sqrt(sd.time())
        run_parity(model, ['sqrt_val'])

    def test_exp(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='exp')
        growth_rate = model.constant("growth_rate")
        growth_rate.equation = 0.0  # ln(1) = 0
        exp_val = model.converter("exp_val")
        exp_val.equation = sd.exp(growth_rate * sd.time())
        run_parity(model, ['growth_rate', 'exp_val'])

    def test_exp_with_growth(self):
        model = Model(starttime=0, stoptime=5, dt=1, name='exp_growth')
        rate = model.constant("rate")
        rate.equation = 0.5
        exp_val = model.converter("exp_val")
        exp_val.equation = sd.exp(rate * sd.time())
        run_parity(model, ['exp_val'])

    def test_round_away_from_half(self):
        """round() for values that do not land on a half."""
        model = Model(starttime=0, stoptime=5, dt=1, name='round')
        f = model.converter("round_val")
        f.equation = sd.round(sd.time() + 0.3, 0)
        run_parity(model, ['round_val'])

    def test_round_halves_away_from_zero_on_both(self):
        """A half rounds away from zero, as a spreadsheet rounds: 2.5 -> 3, -2.5 -> -3.

        The Python engine used Python's round(), which rounds half to even (2.5 -> 2),
        and the two engines gave different numbers for the same model at every half.
        """
        model = Model(starttime=-4, stoptime=4, dt=0.5, name='round_half')
        f = model.converter("round_val")
        f.equation = sd.round(sd.time(), 0)
        g = model.converter("round_digits")
        g.equation = sd.round(sd.time() * 0.05, 1)
        run_parity(model, ['round_val', 'round_digits'])

        values = f.plot(return_df=True)["round_val"]
        assert values[2.5] == 3.0 and values[-2.5] == -3.0 and values[0.5] == 1.0

    def test_pi(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='pi')
        p = model.converter("pi_val")
        p.equation = sd.pi()
        run_parity(model, ['pi_val'])


# ---------------------------------------------------------------------------
# Test: Trig functions as converters (no flow non-negativity)
# ---------------------------------------------------------------------------

class TestParityTrigConverters:
    """Test trig functions as converters — raw values, no clamping."""

    def test_sin(self):
        model = Model(starttime=0.0, stoptime=6.0, dt=1.0, name='sin')
        s = model.converter("sin_val")
        s.equation = sd.sin(sd.time())
        run_parity(model, ['sin_val'])

    def test_cos(self):
        model = Model(starttime=0.0, stoptime=6.0, dt=1.0, name='cos')
        c = model.converter("cos_val")
        c.equation = sd.cos(sd.time())
        run_parity(model, ['cos_val'])

    def test_tan(self):
        model = Model(starttime=0.0, stoptime=6.0, dt=1.0, name='tan')
        t = model.converter("tan_val")
        t.equation = sd.tan(sd.time())
        run_parity(model, ['tan_val'])

    def test_arcsin(self):
        model = Model(starttime=0.0, stoptime=1.0, dt=0.25, name='arcsin')
        a = model.converter("arcsin_val")
        a.equation = sd.arcsin(sd.time())
        run_parity(model, ['arcsin_val'])

    def test_arccos(self):
        model = Model(starttime=0.0, stoptime=1.0, dt=0.25, name='arccos')
        a = model.converter("arccos_val")
        a.equation = sd.arccos(sd.time())
        run_parity(model, ['arccos_val'])

    def test_arctan(self):
        model = Model(starttime=0.0, stoptime=6.0, dt=1.0, name='arctan')
        a = model.converter("arctan_val")
        a.equation = sd.arctan(sd.time())
        run_parity(model, ['arctan_val'])


# ---------------------------------------------------------------------------
# Test: Trig functions as flows (with non-negativity clamping)
# ---------------------------------------------------------------------------

class TestParityTrigFlows:
    """Test trig functions as flows — max(0, val) applied."""

    def test_sin_cos_as_flows(self):
        model = Model(starttime=0.0, stoptime=10.0, dt=0.5, name='trig_flow')
        sin_flow = model.flow("sin_flow")
        cos_flow = model.flow("cos_flow")
        sin_flow.equation = sd.sin(sd.time())
        cos_flow.equation = sd.cos(sd.time())
        run_parity(model, ['sin_flow', 'cos_flow'])

    def test_arcsin_arccos_as_flows(self):
        model = Model(starttime=0.0, stoptime=1.0, dt=0.25, name='arcs_flow')
        arcsin_flow = model.flow("arcsin_flow")
        arccos_flow = model.flow("arccos_flow")
        arcsin_flow.equation = sd.arcsin(sd.time())
        arccos_flow.equation = sd.arccos(sd.time())
        run_parity(model, ['arcsin_flow', 'arccos_flow'])


# ---------------------------------------------------------------------------
# Test: Wave functions
# ---------------------------------------------------------------------------

class TestParityWaves:
    """Test sinwave and coswave as flows (with non-negativity)."""

    def test_sinwave_coswave_as_flows(self):
        model = Model(starttime=0.0, stoptime=10.0, dt=0.5, name='waves')
        sinw = model.flow("sinwave_flow")
        cosw = model.flow("coswave_flow")
        sinw.equation = sd.sinwave(amplitude=2, period=4)
        cosw.equation = sd.coswave(amplitude=8, period=16)
        run_parity(model, ['sinwave_flow', 'coswave_flow'])

    def test_sinwave_as_converter(self):
        """Sinwave as converter — no clamping."""
        model = Model(starttime=0.0, stoptime=10.0, dt=0.5, name='sinw_conv')
        sinw = model.converter("sinwave_conv")
        sinw.equation = sd.sinwave(amplitude=3, period=5)
        run_parity(model, ['sinwave_conv'])


# ---------------------------------------------------------------------------
# Test: Max / Min
# ---------------------------------------------------------------------------

class TestParityMaxMin:
    """Test max and min functions."""

    def test_max(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='max')
        a = model.converter("a")
        a.equation = 5.0 + sd.step(15, 5)
        b = model.converter("b")
        b.equation = 10 - sd.step(2, 5)
        c = model.converter("c")
        c.equation = sd.max(a, b)
        run_parity(model, ['a', 'b', 'c'])

    def test_min(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='min')
        a = model.converter("a")
        a.equation = 5.0 + sd.step(15, 5)
        b = model.converter("b")
        b.equation = 10 - sd.step(2, 5)
        c = model.converter("c")
        c.equation = sd.min(a, b)
        run_parity(model, ['a', 'b', 'c'])


# ---------------------------------------------------------------------------
# Test: Comparison operators with If
# ---------------------------------------------------------------------------

class TestParityComparisons:
    """Test comparison operators combined with If."""

    def _build_comparison_model(self, op_func):
        """Build model: converter x = If(time() <op> 5, 1, 0)."""
        model = Model(starttime=0, stoptime=10, dt=1, name='cmp')
        t = model.converter("t_val")
        t.equation = sd.time()
        x = model.converter("x")
        x.equation = sd.If(op_func(t, 5), 1, 0)
        return model

    def test_gt(self):
        model = self._build_comparison_model(lambda a, b: a > b)
        run_parity(model, ['t_val', 'x'])

    def test_lt(self):
        model = self._build_comparison_model(lambda a, b: a < b)
        run_parity(model, ['t_val', 'x'])

    def test_gte(self):
        model = self._build_comparison_model(lambda a, b: a >= b)
        run_parity(model, ['t_val', 'x'])

    def test_lte(self):
        model = self._build_comparison_model(lambda a, b: a <= b)
        run_parity(model, ['t_val', 'x'])

    def test_eq(self):
        model = self._build_comparison_model(lambda a, b: a == b)
        run_parity(model, ['t_val', 'x'])

    def test_neq(self):
        model = self._build_comparison_model(lambda a, b: a != b)
        run_parity(model, ['t_val', 'x'])


# ---------------------------------------------------------------------------
# Test: Logical operators (And, Or, Not)
# ---------------------------------------------------------------------------

class TestParityLogical:
    """Test logical operators with growing stocks (from test_sddsl.py)."""

    def test_and_or_not(self):
        model = Model(starttime=0.0, stoptime=10.0, dt=1.0, name='logical')
        stock1 = model.stock("stock1")
        stock2 = model.stock("stock2")
        inflow1 = model.flow("inflow1")
        inflow2 = model.flow("inflow2")
        stock1.initial_value = 1.0
        stock2.initial_value = 1.0
        inflow1.equation = 1.0 * stock1
        inflow2.equation = 2.0 * stock2
        stock1.equation = inflow1
        stock2.equation = inflow2

        x = model.converter("x")
        x.equation = sd.If(sd.And(stock1 > 4, stock2 > 4), 1, 0)
        y = model.converter("y")
        y.equation = sd.If(sd.Or(stock1 > 4, stock2 > 4), 1, 0)
        z = model.converter("z")
        z.equation = sd.If(sd.Not(sd.And(stock1 > 4, stock2 > 4)), 1, 0)

        run_parity(model, ['stock1', 'stock2', 'inflow1', 'inflow2', 'x', 'y', 'z'])


# ---------------------------------------------------------------------------
# Test: Lookup function
# ---------------------------------------------------------------------------

class TestParityLookup:
    """Test graphical function / lookup table interpolation."""

    def test_lookup_basic(self):
        model = Model(starttime=0.0, stoptime=10.0, dt=0.25, name='lookup')
        input_val = model.converter("input_val")
        input_val.equation = sd.time() * 0.25

        model.points["my_table"] = [
            [0, 0], [0.5, 1], [1.0, 3], [1.5, 2],
            [2.0, 4], [2.5, 5],
        ]

        output = model.converter("output")
        output.equation = sd.lookup(input_val, "my_table")
        run_parity(model, ['input_val', 'output'])


    def test_points_in_any_order_describe_the_same_curve(self):
        """Both engines read the first point as the left edge; an unsorted table used to
        give the same nonsense on both."""
        model = Model(starttime=0.0, stoptime=12.0, dt=0.5, name='lookup_unsorted')
        model.points["line"] = [[10, 100], [0, 0], [5, 50]]
        output = model.converter("output")
        output.equation = sd.lookup(sd.time(), "line")
        run_parity(model, ['output'])
        assert model.evaluate_equation("output", 2.5) == 25.0

    def test_two_points_at_one_x_are_refused_by_both(self):
        """The engines used to pick different values at that x."""
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0, name='lookup_duplicate')
        model.points["tab"] = [[0, 0], [5, 10], [5, 90], [10, 100]]
        output = model.converter("output")
        output.equation = sd.lookup(5.0, "tab")
        with pytest.raises(ValueError, match="Lookup table 'tab' has two points at x=5.0"):
            model.evaluate_equation("output", 0.0)
        with pytest.raises(ValueError, match="Lookup table 'tab' has two points at x=5.0"):
            RustSdEngine().load_model(model.to_json())

    def test_a_table_the_model_does_not_have_is_refused_by_both(self):
        """Rust used to read 0.0, Python raised a bare KeyError."""
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0, name='lookup_missing')
        output = model.converter("output")
        output.equation = sd.lookup(5.0, "missing")
        message = "Lookup of a table the model does not have: 'missing'"
        with pytest.raises(ValueError, match=message):
            model.evaluate_equation("output", 0.0)
        with pytest.raises(ValueError, match=message):
            RustSdEngine().load_model(model.to_json())


class TestParityLookupInverseAndArea:
    """LOOKUPINV and LOOKUPAREA, including what lies beyond the table's ends."""

    def test_lookupinv(self):
        model = Model(starttime=0.0, stoptime=12.0, dt=0.5, name='lookupinv_par')
        model.points["rising"] = [[0, 1], [2, 3], [4, 6]]
        expressions = {
            'named': sd.lookupinv(sd.time(), "rising"),
            'inline_falling': sd.lookupinv(sd.time() * 0.5, [[0, 10], [5, 0]]),
            'flat_segment': sd.lookupinv(2.0, [[0, 0], [1, 2], [3, 2], [4, 5]]),
            'not_monotonic': sd.lookupinv(sd.time(), [[0, 0], [1, 5], [2, 1]]),
            'below': sd.lookupinv(-3.0, "rising"),
        }
        for name, expression in expressions.items():
            model.converter(name).equation = expression
        run_parity(model, list(expressions), atol=1e-12)

    def test_lookuparea(self):
        model = Model(starttime=0.0, stoptime=12.0, dt=0.5, name='lookuparea_par')
        model.points["rising"] = [[0, 1], [2, 3], [4, 6]]
        expressions = {
            'whole': sd.lookuparea("rising"),
            'to_time': sd.lookuparea("rising", None, sd.time()),
            'from_time': sd.lookuparea([[0, 0], [10, 10]], sd.time()),
            'reversed': sd.lookuparea("rising", sd.time(), 1.0),
            'beyond_both_ends': sd.lookuparea("rising", -5.0, 50.0),
            'outside': sd.lookuparea("rising", 5.0, 9.0),
            'nan': sd.lookuparea("rising", sd.nan(), 2.0),
        }
        for name, expression in expressions.items():
            model.converter(name).equation = expression
        run_parity(model, list(expressions), atol=1e-12)

    def test_lookupmax_lookupmin_lookupmean(self):
        model = Model(starttime=0.0, stoptime=12.0, dt=0.5, name='lookup_statistics_par')
        model.points["peak"] = [[2, 0], [4, 5], [6, 20], [8, 10], [10, 0]]
        expressions = {}
        for name, function in (("max", sd.lookupmax), ("min", sd.lookupmin), ("mean", sd.lookupmean)):
            expressions.update({
                name + '_whole': function("peak"),
                name + '_to_time': function("peak", None, sd.time()),
                name + '_from_time': function("peak", sd.time()),
                name + '_reversed': function("peak", sd.time(), 3.0),
                name + '_beyond_both_ends': function("peak", -5.0, 50.0),
                name + '_outside': function("peak", 11.0, 13.0),
                name + '_nan': function("peak", sd.nan(), 2.0),
                name + '_inline': function([[0, 1], [5, 2], [7, 0]], 1.0, sd.time()),
            })
        for name, expression in expressions.items():
            model.converter(name).equation = expression
        run_parity(model, list(expressions), atol=1e-12)

    def test_a_table_set_after_the_equation(self):
        """Without from and to, the area spans the table as it is when the model runs."""
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name='lookuparea_late_par')
        model.converter('area').equation = sd.lookuparea("late")
        model.points["late"] = [[0, 2], [3, 2]]
        run_parity(model, ['area'], atol=1e-12)


class TestParityLookupKinds:
    """XMILE's three types of graphical function, in lookup, LOOKUPINV and LOOKUPAREA."""

    def test_every_kind_in_every_lookup(self):
        model = Model(starttime=0.0, stoptime=12.0, dt=0.5, name='lookup_kinds_par')
        model.points["peak"] = [[2, 0], [4, 5], [6, 20], [8, 10], [10, 0]]
        model.points["rising"] = [[0, 0], [2, 1], [4, 4], [6, 9], [8, 16]]
        model.points["falling"] = [[0, 10], [5, 4], [10, 1]]
        x = sd.time() * 2.0 - 3.0
        expressions = {}
        for kind in ("continuous", "extrapolate", "discrete"):
            expressions.update({
                kind + '_lookup': sd.lookup(x, "peak", kind=kind),
                kind + '_inline': sd.lookup(x, [[0, 1], [5, 2], [7, 0]], kind=kind),
                kind + '_inverse': sd.lookupinv(x, "rising", kind=kind),
                kind + '_inverse_falling': sd.lookupinv(x, "falling", kind=kind),
                kind + '_area': sd.lookuparea("rising", -2.0, sd.time(), kind=kind),
                kind + '_area_reversed': sd.lookuparea("rising", sd.time() + 3.0, -1.0, kind=kind),
                kind + '_area_whole': sd.lookuparea("peak", kind=kind),
                kind + '_max': sd.lookupmax("peak", sd.time() - 2.0, sd.time(), kind=kind),
                kind + '_min': sd.lookupmin("peak", sd.time() - 2.0, sd.time(), kind=kind),
                kind + '_mean': sd.lookupmean("peak", -2.0, sd.time() + 1.0, kind=kind),
            })
        for name, expression in expressions.items():
            model.converter(name).equation = expression
        run_parity(model, list(expressions), atol=1e-12)


class TestParityIrr:
    """IRR over the history of a stream: no rate at the first step, one where the stream
    has turned, the one nearest zero where there are several, and `missing` where there is
    none."""

    def test_irr(self):
        model = Model(starttime=1, stoptime=40, dt=1, name='irr_par')
        cash = model.converter('cash')
        cash.equation = sd.If(sd.time() <= 3, -100.0, 25.0 + sd.time())
        twice = model.converter('twice')
        twice.equation = sd.If(sd.time() <= 1, -100.0, sd.If(sd.time() <= 6, 230.0, -132.0))
        only_in = model.converter('only_in')
        only_in.equation = 10.0 + sd.time()
        zeros = model.converter('zeros')
        zeros.equation = 0.0
        expressions = {
            'rate': sd.irr(model, cash),
            'with_missing': sd.irr(model, cash, -1.0),
            'several_rates': sd.irr(model, twice, -7.0),
            'no_rate': sd.irr(model, only_in, sd.time() * 2.0),
            'of_zeros': sd.irr(model, zeros, -3.0),
            'expression': sd.irr(model, cash * 2.0 + 1.0),
        }
        for name, expression in expressions.items():
            model.converter(name).equation = expression
        run_parity(model, list(expressions), atol=1e-9)

    def test_irr_with_a_fractional_dt_and_a_late_start(self):
        model = Model(starttime=2.5, stoptime=12.0, dt=0.25, name='irr_dt_par')
        cash = model.converter('cash')
        cash.equation = sd.If(sd.time() < 4.0, -50.0, 12.0)
        model.converter('rate').equation = sd.irr(model, cash, 0.0)
        run_parity(model, ['rate'], atol=1e-9)

    def test_irr_in_a_stock(self):
        """Written into a stock, the stream is read up to the step before."""
        model = Model(starttime=0, stoptime=20, dt=1, name='irr_stock_par')
        cash = model.converter('cash')
        cash.equation = sd.If(sd.time() <= 2, -100.0, 30.0)
        stock = model.stock('rates')
        stock.initial_value = 0.0
        stock.equation = sd.irr(model, cash, 0.0)
        run_parity(model, ['rates'], atol=1e-9)

    def test_irr_of_a_stock(self):
        model = Model(starttime=0, stoptime=20, dt=1, name='irr_of_stock_par')
        account = model.stock('account')
        account.initial_value = -100.0
        flow = model.flow('payments')
        flow.equation = 15.0
        account.equation = flow
        model.converter('rate').equation = sd.irr(model, account, 0.0)
        run_parity(model, ['rate'], atol=1e-9)


# ---------------------------------------------------------------------------
# Test: Inline lookup points
# ---------------------------------------------------------------------------

class TestParityInlineLookup:
    """Test inline lookup points (auto-generated table names)."""

    def test_inline_lookup_basic(self):
        model = Model(starttime=0.0, stoptime=10.0, dt=0.25, name='inline_lookup')
        input_val = model.converter("input_val")
        input_val.equation = sd.time() * 0.5

        output = model.converter("output")
        output.equation = sd.lookup(input_val, [(0, 0), (1, 2), (2, 6), (3, 4), (4, 8), (5, 10)])
        run_parity(model, ['input_val', 'output'])

    def test_inline_lookup_boundary(self):
        """Input outside point range — verify both engines clamp identically."""
        model = Model(starttime=0.0, stoptime=10.0, dt=1.0, name='inline_boundary')
        input_val = model.converter("input_val")
        # Goes from -2 to 8, exceeding the table range [0, 5]
        input_val.equation = sd.time() - 2.0

        output = model.converter("output")
        output.equation = sd.lookup(input_val, [(0, 0), (5, 10)])
        run_parity(model, ['input_val', 'output'])

    def test_mixed_inline_and_named_lookup(self):
        """Model with both inline points and named tables."""
        model = Model(starttime=0.0, stoptime=10.0, dt=0.5, name='mixed_lookup')
        input_val = model.converter("input_val")
        input_val.equation = sd.time() * 0.5

        # Named lookup table
        model.points["named_table"] = [[0, 0], [2, 4], [5, 10]]
        named_out = model.converter("named_out")
        named_out.equation = sd.lookup(input_val, "named_table")

        # Inline lookup
        inline_out = model.converter("inline_out")
        inline_out.equation = sd.lookup(input_val, [(0, 1), (2, 5), (5, 8)])

        run_parity(model, ['input_val', 'named_out', 'inline_out'])


# ---------------------------------------------------------------------------
# Test: Linear growth (stock + constant inflow)
# ---------------------------------------------------------------------------

class TestParityLinearGrowth:
    """Test simple stock with constant inflow."""

    def test_linear_growth(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='linear')
        stock = model.stock("stock")
        stock.initial_value = 0.0
        inflow = model.flow("inflow")
        inflow.equation = 5.0
        stock.equation = inflow
        run_parity(model, ['stock', 'inflow'])


# ---------------------------------------------------------------------------
# Test: Exponential growth (stock with feedback)
# ---------------------------------------------------------------------------

class TestParityExponentialGrowth:
    """Test stock with feedback loop (exponential growth)."""

    def test_exponential_growth(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='exp_growth')
        stock = model.stock("population")
        stock.initial_value = 100.0
        growth = model.flow("growth")
        rate = model.constant("rate")
        rate.equation = 0.1
        growth.equation = stock * rate
        stock.equation = growth
        run_parity(model, ['population', 'growth', 'rate'], atol=1e-6)


# ---------------------------------------------------------------------------
# Test: Flow non-negativity
# ---------------------------------------------------------------------------

class TestParityFlowNonNegativity:
    """Flows clamp to max(0, val) — verify Rust matches."""

    def test_flow_clamps_negative(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='nonneg')
        stock = model.stock("stock")
        stock.initial_value = 5.0
        outflow = model.flow("outflow")
        outflow.equation = sd.time() - 7  # negative for t < 7
        stock.equation = -outflow
        run_parity(model, ['stock', 'outflow'])


# ---------------------------------------------------------------------------
# Test: Non-zero start time
# ---------------------------------------------------------------------------

class TestParityNonZeroStartTime:
    """Verify Rust handles non-zero start time correctly."""

    def test_nonzero_start(self):
        model = Model(starttime=5, stoptime=15, dt=1, name='nonzero')
        stock = model.stock("stock")
        stock.initial_value = 10.0
        inflow = model.flow("inflow")
        inflow.equation = sd.time()
        stock.equation = inflow
        run_parity(model, ['stock', 'inflow'])


# ---------------------------------------------------------------------------
# Test: Fractional dt
# ---------------------------------------------------------------------------

class TestParityFractionalDt:
    """Verify Rust handles fractional dt (0.25) correctly."""

    def test_dt_quarter(self):
        model = Model(starttime=0, stoptime=5, dt=0.25, name='frac_dt')
        stock = model.stock("stock")
        stock.initial_value = 0.0
        inflow = model.flow("inflow")
        inflow.equation = 1.0
        stock.equation = inflow
        run_parity(model, ['stock', 'inflow'])

    def test_dt_half(self):
        model = Model(starttime=0, stoptime=5, dt=0.5, name='half_dt')
        stock = model.stock("stock")
        stock.initial_value = 100.0
        outflow = model.flow("outflow")
        rate = model.constant("rate")
        rate.equation = 0.05
        outflow.equation = stock * rate
        stock.equation = -outflow
        run_parity(model, ['stock', 'outflow'], atol=1e-6)


# ---------------------------------------------------------------------------
# Test: Simple Project Management model (from test_sddsl.py test_spm)
# ---------------------------------------------------------------------------

class TestParitySPM:
    """
    Full parity test of the Simple Project Management model.
    3 stocks, 1 flow, 4 converters, 4 constants, 1 lookup table.
    """

    def test_spm_full(self):
        model = Model(starttime=0.0, stoptime=120.0, dt=1.0,
                      name='SimpleProjectManagement')

        openTasks = model.stock("openTasks")
        closedTasks = model.stock("closedTasks")
        staff = model.stock("staff")
        completionRate = model.flow("completionRate")
        currentTime = model.converter("currentTime")
        remainingTime = model.converter("remainingTime")
        schedulePressure = model.converter("schedulePressure")
        productivity = model.converter("productivity")
        deadline = model.constant("deadline")
        effortPerTask = model.constant("effortPerTask")
        initialStaff = model.constant("initialStaff")
        initialOpenTasks = model.constant("initialOpenTasks")

        closedTasks.initial_value = 0.0
        staff.initial_value = initialStaff
        openTasks.initial_value = initialOpenTasks
        deadline.equation = 100.0
        effortPerTask.equation = 1.0
        initialStaff.equation = 1.0
        initialOpenTasks.equation = 100.0

        currentTime.equation = sd.time()
        remainingTime.equation = deadline - currentTime
        openTasks.equation = -completionRate
        closedTasks.equation = completionRate

        schedulePressure.equation = sd.min(
            (openTasks * effortPerTask) / (staff * sd.max(remainingTime, 1)), 2.5)

        model.points["productivity"] = [
            [0, 0.4],
            [0.25, 0.444],
            [0.5, 0.506],
            [0.75, 0.594],
            [1, 1],
            [1.25, 1.119],
            [1.5, 1.1625],
            [1.75, 1.2125],
            [2, 1.2375],
            [2.25, 1.245],
            [2.5, 1.25]
        ]

        productivity.equation = sd.lookup(schedulePressure, "productivity")
        completionRate.equation = sd.max(0.0, sd.min(
            openTasks, staff * (productivity / effortPerTask)))

        run_parity(
            model,
            ['openTasks', 'closedTasks', 'staff', 'completionRate',
             'currentTime', 'remainingTime', 'schedulePressure', 'productivity'],
            atol=1e-6,
        )


# ---------------------------------------------------------------------------
# Test: SIR epidemic model
# ---------------------------------------------------------------------------

class TestParitySIR:
    """
    Full SIR model parity: 3 stocks, 2 flows, 3 constants.
    dt=0.25, 40 time units = 160 timesteps.
    """

    def test_sir_full(self):
        model = Model(starttime=0.0, stoptime=40.0, dt=0.25, name='SIR')

        susceptible = model.stock("susceptible")
        infected = model.stock("infected")
        recovered = model.stock("recovered")
        infection = model.flow("infection")
        recovery = model.flow("recovery")
        total_population = model.constant("total_population")
        infection_rate = model.constant("infection_rate")
        recovery_rate = model.constant("recovery_rate")

        total_population.equation = 1000.0
        infection_rate.equation = 0.3
        recovery_rate.equation = 0.1

        susceptible.initial_value = 990.0
        infected.initial_value = 10.0
        recovered.initial_value = 0.0

        infection.equation = (infection_rate * susceptible * infected) / total_population
        recovery.equation = recovery_rate * infected

        susceptible.equation = -infection
        infected.equation = infection - recovery
        recovered.equation = recovery

        run_parity(
            model,
            ['susceptible', 'infected', 'recovered', 'infection', 'recovery'],
            atol=1e-6,
        )


# ---------------------------------------------------------------------------
# Test: Constant-only model
# ---------------------------------------------------------------------------

class TestParityConstant:
    """Verify that a constant has the same value at all timesteps."""

    def test_single_constant(self):
        model = Model(starttime=0, stoptime=5, dt=1, name='const')
        c = model.constant("my_const")
        c.equation = 42.0
        run_parity(model, ['my_const'])


# ---------------------------------------------------------------------------
# Test: Stock with initial value from constant
# ---------------------------------------------------------------------------

class TestParityStockInitFromConstant:
    """Verify stock initial_value from a constant reference."""

    def test_stock_init_from_constant(self):
        model = Model(starttime=0, stoptime=5, dt=1, name='init_const')
        init_val = model.constant("init_val")
        init_val.equation = 50.0
        stock = model.stock("stock")
        stock.initial_value = init_val
        inflow = model.flow("inflow")
        inflow.equation = 2.0
        stock.equation = inflow
        run_parity(model, ['stock', 'inflow', 'init_val'])

    def test_initial_values_reading_each_other_through_a_converter(self):
        model = Model(starttime=0, stoptime=3, dt=1, name='init_chain')
        first = model.stock("first")
        second = model.stock("second")
        twice = model.converter("twice")
        size = model.constant("size")
        size.equation = 25.0
        twice.equation = second * 2.0
        first.initial_value = twice
        second.initial_value = size
        run_parity(model, ['first', 'second', 'twice'])

    @pytest.mark.allow_rust_unused
    def test_an_initial_value_reading_its_own_stock_is_a_cycle_on_both(self):
        model = Model(starttime=0, stoptime=3, dt=1, name='init_cycle')
        level = model.stock("level")
        reading = model.converter("reading")
        reading.equation = level + 1.0
        level.initial_value = reading
        message = "Cyclic dependency among non-stock entities: level → reading → level"
        with pytest.raises(CyclicDependencyError) as caught:
            model.simulate(["level"])
        assert str(caught.value) == message
        with pytest.raises(BPTK_Py.RustBackendError) as caught:
            model.simulate(["level"], backend="rust")
        assert str(caught.value).endswith(message)


# ---------------------------------------------------------------------------
# Test: Multiple interacting converters
# ---------------------------------------------------------------------------

class TestParityConverterChain:
    """Test a chain of converters referencing each other."""

    def test_converter_chain(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='chain')
        a = model.converter("a")
        b = model.converter("b")
        c = model.converter("c")
        d = model.converter("d")
        a.equation = sd.time()
        b.equation = a * 2
        c.equation = b + 3
        d.equation = c / (a + 1)
        run_parity(model, ['a', 'b', 'c', 'd'])


# ---------------------------------------------------------------------------
# Test: Complex expression (nested operations)
# ---------------------------------------------------------------------------

class TestParityComplexExpressions:
    """Test complex nested expressions."""

    def test_nested_if(self):
        """Nested If: If(t > 5, If(t > 8, 3, 2), 1)."""
        model = Model(starttime=0, stoptime=10, dt=1, name='nested_if')
        t_val = model.converter("t_val")
        t_val.equation = sd.time()
        x = model.converter("x")
        x.equation = sd.If(t_val > 5, sd.If(t_val > 8, 3, 2), 1)
        run_parity(model, ['t_val', 'x'])

    def test_compound_expression(self):
        """abs(sin(time()) * 10) + max(time() - 5, 0)."""
        model = Model(starttime=0, stoptime=10, dt=1, name='compound')
        x = model.converter("x")
        x.equation = sd.abs(sd.sin(sd.time()) * 10) + sd.max(sd.time() - 5, 0)
        run_parity(model, ['x'])


# ---------------------------------------------------------------------------
# Test: Combinatorial & special functions
# ---------------------------------------------------------------------------

class TestParityCombinatorialFunctions:
    """Test combinatorial and special functions."""

    def test_factorial(self):
        model = Model(starttime=0, stoptime=5, dt=1, name='factorial')
        x = model.converter("x")
        x.equation = sd.factorial(sd.time())
        run_parity(model, ['x'])

    def test_factorial_zero(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='factorial_zero')
        x = model.converter("x")
        x.equation = sd.factorial(0)
        run_parity(model, ['x'])

    def test_combinations(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='combinations')
        x = model.converter("x")
        x.equation = sd.combinations(10, 3)
        run_parity(model, ['x'])

    def test_combinations_edge(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='comb_edge')
        x = model.converter("x")
        x.equation = sd.combinations(5, 0)
        run_parity(model, ['x'])

    def test_combinations_n_less_than_r(self):
        """combinations(2, 5) should return 0 when n < r."""
        model = Model(starttime=0, stoptime=1, dt=1, name='comb_n_lt_r')
        x = model.converter("x")
        x.equation = sd.combinations(2, 5)
        py, _ = run_parity(model, ['x'])
        assert set(py['x'].values()) == {0.0}

    def test_permutations(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='permutations')
        x = model.converter("x")
        x.equation = sd.permutations(5, 2)
        run_parity(model, ['x'])

    def test_permutations_n_less_than_r(self):
        """permutations(2, 5) should return 0 when n < r."""
        model = Model(starttime=0, stoptime=1, dt=1, name='perm_n_lt_r')
        x = model.converter("x")
        x.equation = sd.permutations(2, 5)
        run_parity(model, ['x'])

    def test_factorial_negative(self):
        """factorial(-5) should return 0 for negative input."""
        model = Model(starttime=0, stoptime=1, dt=1, name='factorial_neg')
        x = model.converter("x")
        x.equation = sd.factorial(-5)
        run_parity(model, ['x'])

    def test_gammaln(self):
        model = Model(starttime=1, stoptime=5, dt=1, name='gammaln')
        x = model.converter("x")
        x.equation = sd.gammaln(sd.time())
        run_parity(model, ['x'])

    def test_gammaln_one(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='gammaln_one')
        x = model.converter("x")
        x.equation = sd.gammaln(1)
        run_parity(model, ['x'])

    def test_round_with_digits(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='round_digits')
        x = model.converter("x")
        x.equation = sd.round(3.14159, 2)
        run_parity(model, ['x'])


# ---------------------------------------------------------------------------
# Test: Inf and Nan
# ---------------------------------------------------------------------------

class TestParityInfNan:
    """Test Inf and Nan special values."""

    def test_inf(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='inf_test')
        x = model.converter("x")
        x.equation = sd.Inf()
        py_results, rust_results = run_parity(model, ['x'])

    def test_nan(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='nan_test')
        x = model.converter("x")
        x.equation = sd.nan()
        # NaN != NaN, so run_parity's approx check won't work.
        # Run manually and check with math.isnan.
        from BPTK_Py.util import timerange
        from BPTK_Py._rust_engine import RustSdEngine
        times = timerange(model.starttime, model.stoptime, model.dt, exclusive=False)

        # Python results
        for t in times:
            assert math.isnan(x(t)), f"Python nan at t={t}"

        # Rust results
        engine = RustSdEngine()
        json_str = model.to_json()
        rust_model = engine.load_model(json_str)
        rust_results = rust_model.simulate(["x"])
        for t in times:
            key = f"{t:.1f}" if t == int(t) else str(t)
            assert math.isnan(rust_results["x"][key]), f"Rust nan at t={t}"

    def test_inf_in_min(self):
        """min(time(), Inf()) should equal time()."""
        model = Model(starttime=0, stoptime=5, dt=1, name='inf_min')
        t_val = model.converter("t_val")
        t_val.equation = sd.time()
        x = model.converter("x")
        x.equation = sd.min(t_val, sd.Inf())
        run_parity(model, ['t_val', 'x'])

    def test_inf_in_max(self):
        """max(time(), -Inf()) — not directly available, use If to test Inf comparison."""
        model = Model(starttime=0, stoptime=5, dt=1, name='inf_max')
        x = model.converter("x")
        x.equation = sd.max(sd.time(), 0 - sd.Inf())
        run_parity(model, ['x'])


# ---------------------------------------------------------------------------
# Test: Biflow parity (serializer coverage)
# ---------------------------------------------------------------------------

class TestParityBiflow:
    """Test biflow serialization through the parity (to_json) path."""

    @pytest.mark.parametrize("dt, start", [(0.25, 1.0), (0.1, 10.0)])
    def test_biflow_oscillator(self, dt, start):
        """Biflow allows negative values — simple oscillator."""
        model = Model(starttime=0, stoptime=10, dt=dt, name='biflow_osc')
        position = model.stock("position")
        position.initial_value = start
        velocity = model.biflow("velocity")
        velocity.equation = -position
        position.equation = velocity
        _, rust = run_parity(model, ['position', 'velocity'])

        assert min(rust['velocity'].values()) < 0, "a biflow is not clamped at zero"

    def test_biflow_constant_negative(self):
        model = Model(starttime=0, stoptime=5, dt=1, name='biflow_const_neg_par')
        stock = model.stock("stock")
        bf = model.biflow("bf")
        stock.initial_value = 100.0
        stock.equation = bf
        bf.equation = -10.0
        run_parity(model, ['stock', 'bf'])

    def test_biflow_vs_flow_clamping(self):
        """The same negative equation: a flow clamps to 0, a biflow does not."""
        model = Model(starttime=0, stoptime=3, dt=1, name='flow_vs_biflow_par')
        stock_f = model.stock("stock_flow")
        stock_bf = model.stock("stock_biflow")
        f = model.flow("regular_flow")
        bf = model.biflow("bi_flow")
        stock_f.initial_value = 100.0
        stock_bf.initial_value = 100.0
        stock_f.equation = f
        stock_bf.equation = bf
        f.equation = -10.0
        bf.equation = -10.0
        run_parity(model, ['stock_flow', 'stock_biflow', 'regular_flow', 'bi_flow'])

    def test_biflow_spring_mass_oscillator(self):
        """Two stocks, a small dt: the classic biflow system."""
        model = Model(starttime=0, stoptime=10, dt=0.01, name='spring_mass_par')
        position = model.stock("position")
        velocity = model.stock("velocity")
        dp = model.biflow("change_in_position")
        dv = model.biflow("change_in_velocity")
        position.initial_value = 1.0
        velocity.initial_value = 0.0
        position.equation = dp
        velocity.equation = dv
        dp.equation = velocity
        dv.equation = -position
        run_parity(model, ['position', 'velocity'], atol=1e-9)


# ---------------------------------------------------------------------------
# Test: Serializer error handling
# ---------------------------------------------------------------------------

class TestSerializerErrors:
    """Test that json_serializer raises clear errors for unsupported features."""

    def test_nary_operator_raises(self):
        """Custom NaryOperator functions cannot be serialized."""
        from BPTK_Py.sddsl.operators import NaryOperator
        from BPTK_Py.sddsl.json_serializer import model_to_json

        model = Model(starttime=0, stoptime=1, dt=1, name='nary_err')
        x = model.converter("x")
        x.equation = NaryOperator("my_custom_fn", 1.0, 2.0)

        with pytest.raises(ValueError, match="Custom function"):
            model_to_json(model)

    def test_unsupported_operator_raises(self):
        """Unknown operator types raise a clear error."""
        from BPTK_Py.sddsl.operators import Function
        from BPTK_Py.sddsl.json_serializer import model_to_json

        class UnknownOp(Function):
            def term(self, time="t"):
                return "0"

        model = Model(starttime=0, stoptime=1, dt=1, name='unknown_err')
        x = model.converter("x")
        x.equation = UnknownOp()

        with pytest.raises(ValueError, match="Cannot serialize"):
            model_to_json(model)


# ---------------------------------------------------------------------------
# Test: Statistical functions
# ---------------------------------------------------------------------------

class TestParityDeterministicStatistical:
    """Test invnorm and normalcdf — deterministic, exact parity possible."""

    def test_invnorm_standard(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='invnorm_std')
        x = model.converter("x")
        x.equation = sd.invnorm(0.975, 0, 1)
        run_parity(model, ['x'], atol=1e-6)

    def test_invnorm_custom(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='invnorm_custom')
        x = model.converter("x")
        x.equation = sd.invnorm(0.5, 100, 15)
        run_parity(model, ['x'], atol=1e-6)

    def test_normalcdf(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='normalcdf')
        x = model.converter("x")
        x.equation = sd.normalcdf(-1, 1, 0, 1)
        run_parity(model, ['x'], atol=1e-6)

    def test_normalcdf_wide(self):
        model = Model(starttime=0, stoptime=1, dt=1, name='normalcdf_wide')
        x = model.converter("x")
        x.equation = sd.normalcdf(-3, 3, 0, 1)
        run_parity(model, ['x'], atol=1e-6)


# ---------------------------------------------------------------------------
# Stochastic parity: Python and Rust use different RNGs, so exact parity is
# impossible.  Instead, verify that both backends produce samples whose mean
# and variance converge to the known theoretical values.
# ---------------------------------------------------------------------------

N_SAMPLES = 5000  # stoptime with dt=1 gives N_SAMPLES+1 data points


def _run_stochastic_parity(equation, theoretical_mean, theoretical_var,
                           mean_tol=None, var_tol=None, name="stoch", dt=1):
    """
    Run a stochastic equation through both Python and Rust backends,
    then check that sample mean and variance are within tolerance of
    the theoretical values for each backend.

    Default tolerances are 20% of the theoretical value (min 0.5).
    """
    if mean_tol is None:
        mean_tol = max(0.5, abs(theoretical_mean) * 0.20)
    if var_tol is None:
        var_tol = max(1.0, abs(theoretical_var) * 0.30)

    results = {}
    for backend_label in ("python", "rust"):
        model = Model(starttime=0, stoptime=N_SAMPLES * dt, dt=dt,
                       name=f"{name}_{backend_label}")
        x = model.converter("x")
        x.equation = equation

        times = timerange(model.starttime, model.stoptime, model.dt,
                          exclusive=False)

        if backend_label == "python":
            # Seed the global RNG so the Python draws are deterministic, mirroring
            # the fixed seed the Rust backend uses below. Without this the sample
            # moments vary run-to-run and heavy-tailed distributions (lognormal,
            # pareto) intermittently exceed the tolerance — a long-standing flake.
            np.random.seed(42)
            elem = model.converters["x"]
            values = [elem(t) for t in times]
        else:
            json_str = model.to_json()
            engine = RustSdEngine()
            rust_model = engine.load_model(json_str)
            raw = rust_model.simulate(["x"], seed=42)
            values = [raw["x"][rust_time_key(t)] for t in times]

        arr = np.array(values)
        sample_mean = float(arr.mean())
        sample_var = float(arr.var(ddof=1))
        results[backend_label] = (sample_mean, sample_var, arr)

    # Assert both backends converge to theoretical moments
    for label, (smean, svar, _) in results.items():
        assert abs(smean - theoretical_mean) < mean_tol, \
            f"{label} mean {smean:.4f} too far from theoretical {theoretical_mean}"
        assert abs(svar - theoretical_var) < var_tol, \
            f"{label} variance {svar:.4f} too far from theoretical {theoretical_var}"

    return results


class TestParityStochastic:
    """Stochastic distribution parity: both Python and Rust backends must
    produce samples with mean and variance matching theoretical values."""

    def test_normal(self):
        # normal(mean=100, stddev=10): mean=100, var=100
        _run_stochastic_parity(sd.normal(100, 10), 100.0, 100.0, name="normal")

    def test_uniform(self):
        # uniform(0, 1): mean=0.5, var=1/12≈0.0833
        _run_stochastic_parity(sd.random(0, 1), 0.5, 1.0 / 12.0,
                               mean_tol=0.05, var_tol=0.02, name="uniform")

    def test_beta(self):
        # beta(a=2, b=5): mean=2/7≈0.286, var=10/294≈0.034
        a, b = 2.0, 5.0
        _run_stochastic_parity(sd.beta(a, b),
                               a / (a + b),
                               a * b / ((a + b) ** 2 * (a + b + 1)),
                               mean_tol=0.05, var_tol=0.02, name="beta")

    def test_binomial(self):
        # binomial(n=20, p=0.3): mean=6, var=4.2
        _run_stochastic_parity(sd.binomial(20, 0.3), 6.0, 4.2, name="binomial")

    def test_negbinomial(self):
        # negbinomial(n=5, p=0.4): mean=n*(1-p)/p=7.5, var=n*(1-p)/p²=18.75
        _run_stochastic_parity(sd.negbinomial(5, 0.4), 7.5, 18.75, name="negbinomial")

    def test_exprnd(self):
        # exprnd(scale=5): mean=5, var=25
        _run_stochastic_parity(sd.exprnd(5), 5.0, 25.0, name="exprnd")

    def test_gamma(self):
        # gamma(shape=2, scale=3): mean=6, var=18
        _run_stochastic_parity(sd.gamma(2, 3), 6.0, 18.0, name="gamma")

    def test_geometric(self):
        # geometric(p=0.3): mean=(1-p)/p≈2.333, var=(1-p)/p²≈7.778
        # Note: numpy geometric returns number of trials (incl. success),
        # rand_distr::Geometric returns number of failures before first success.
        # The Python SD DSL uses np.random.geometric which has mean=1/p.
        # But geometric class has boundary check returning 1 for invalid p.
        p = 0.3
        _run_stochastic_parity(sd.geometric(p), 1.0 / p, (1 - p) / (p ** 2),
                               mean_tol=1.0, var_tol=3.0, name="geometric")

    def test_lognormal(self):
        # XMILE: the arguments are the mean and stddev of the lognormal distribution itself
        _run_stochastic_parity(sd.lognormal(2.0, 1.0), 2.0, 1.0,
                               mean_tol=0.3, var_tol=1.0, name="lognormal")

    def test_poisson(self):
        # poisson(mu=5): mean=5, var=5
        _run_stochastic_parity(sd.poisson(5), 5.0, 5.0, name="poisson")

    def test_poisson_has_a_mean_per_time_unit(self):
        # As in XMILE and Stella: with dt = 0.25 a step draws a quarter of the mean
        _run_stochastic_parity(sd.poisson(4), 1.0, 1.0, mean_tol=0.1, var_tol=0.2,
                               name="poisson_dt", dt=0.25)

    def test_triangular(self):
        # triangular(1, 5, 10): mean=(1+5+10)/3≈5.333, var=(1²+5²+10²-1*5-1*10-5*10)/18≈4.056
        a, c, b = 1.0, 5.0, 10.0
        _run_stochastic_parity(sd.triangular(a, c, b),
                               (a + c + b) / 3.0,
                               (a ** 2 + c ** 2 + b ** 2 - a * c - a * b - c * b) / 18.0,
                               name="triangular")

    def test_weibull(self):
        # weibull(shape=2, scale=5): mean=scale*Γ(1+1/shape), var=scale²*(Γ(1+2/shape)-Γ(1+1/shape)²)
        import math
        k, lam = 2.0, 5.0
        _run_stochastic_parity(sd.weibull(k, lam),
                               lam * math.gamma(1 + 1 / k),
                               lam ** 2 * (math.gamma(1 + 2 / k) - math.gamma(1 + 1 / k) ** 2),
                               name="weibull")

    def test_pareto(self):
        # The classic Pareto of Stella's help, starting at scale:
        # mean = shape * scale / (shape - 1), var = scale² * shape / ((shape-1)² * (shape-2))
        # Using shape=5 so kurtosis is finite (requires shape>4), which makes
        # sample variance converge reliably with N=5000.
        alpha, xm = 5.0, 1.0
        _run_stochastic_parity(sd.pareto(alpha, xm),
                               alpha * xm / (alpha - 1),
                               xm ** 2 * alpha / ((alpha - 1) ** 2 * (alpha - 2)),
                               mean_tol=0.1, var_tol=0.15, name="pareto")

    def test_lookuprandom(self):
        # The table read as a density, each segment uniform and weighted by its area -
        # the distribution Stella draws from (`test_models/random_dt_1`)
        _run_stochastic_parity(sd.lookuprandom([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [3.0, 1.0], [4.0, 0.0]]), 2.0, 5.0 / 6.0,
                               mean_tol=0.05, var_tol=0.05, name="lookuprandom")

    def test_logistic(self):
        # logistic(mean=10, scale=2): mean=10, var=π²*scale²/3≈13.159
        import math
        mu, s = 10.0, 2.0
        _run_stochastic_parity(sd.logistic(mu, s),
                               mu,
                               (math.pi ** 2 * s ** 2) / 3.0,
                               name="logistic")


class TestParityNormalPink:
    """NORMALPINK is built from PREVIOUS and NORMAL: the same process on both engines, from
    different numbers."""

    def _series(self, build, backend, stoptime=10000):
        model = Model(starttime=0, stoptime=stoptime, dt=1, name="pink_" + backend)
        model.converter("x").equation = build(model)
        return model.simulate(["x"], backend=backend)["x"].values

    @pytest.mark.parametrize("backend", ["python", "rust"])
    def test_mean_spread_and_correlation(self, backend):
        # The lag-1 correlation is 1 - DT / correlation time, 0.8 here
        x = self._series(lambda model: sd.normalpink(model, 10.0, 2.0, 5.0, seed=7), backend)
        assert abs(x.mean() - 10.0) < 0.15 and abs(x.std() - 2.0) < 0.1
        assert abs(np.corrcoef(x[:-1], x[1:])[0, 1] - 0.8) < 0.03

    @pytest.mark.parametrize("backend", ["python", "rust"])
    def test_bounds_hold_the_noise_and_a_sample_holds_the_whole_process(self, backend):
        bounded = self._series(lambda model: sd.normalpink(model, 10.0, 2.0, 5.0, 7, 10.0, 20.0), backend)
        assert bounded.min() >= 10.0 and bounded.max() <= 20.0
        # Drawn again from the same value: a mean of 11.8, where Stella's 11.55 moves on
        # from each value it rejects
        assert abs(bounded.mean() - 11.8) < 0.15
        sampled = self._series(lambda model: sd.normalpink(model, 10.0, 2.0, 5.0, 7, sample=3.0), backend)
        assert np.count_nonzero(np.diff(sampled)) == 3333

    @pytest.mark.parametrize("backend", ["python", "rust"])
    def test_a_correlation_time_up_to_dt_is_the_normal_draw_itself(self, backend):
        pink = self._series(lambda model: sd.normalpink(model, 10.0, 2.0, 0.75, 7), backend, 50)
        plain = self._series(lambda model: sd.normal(10.0, 2.0, 7), backend, 50)
        assert np.allclose(pink, plain, rtol=0, atol=1e-12)

    def test_a_correlation_time_of_0_is_nan_and_reported_alike(self):
        model = Model(starttime=0, stoptime=3, dt=1, name="pink_zero")
        model.converter("x").equation = sd.normalpink(model, 10.0, 2.0, 0.0, 7)
        python, python_errors = _error_lines(lambda: model.simulate(["x"]))
        rust, rust_errors = _error_lines(lambda: model.simulate(["x"], backend="rust"))
        assert python["x"].isna().all() and rust["x"].isna().all()
        assert python_errors and sorted(python_errors) == sorted(rust_errors)


class TestParitySeeded:
    """A seeded draw: the engines draw different numbers for the same seed, and the same
    distribution - and each engine draws the same numbers on every run."""

    @pytest.mark.parametrize("build, mean, var, mean_tol, var_tol", [
        (lambda seed: sd.normal(100, 10, seed=seed), 100.0, 100.0, None, None),
        (lambda seed: sd.random(0, 1, seed), 0.5, 1.0 / 12.0, 0.05, 0.02),
        (lambda seed: sd.beta(2.0, 5.0, seed=seed), 2.0 / 7.0, 10.0 / 392.0, 0.05, 0.02),
        (lambda seed: sd.binomial(20, 0.3, seed=seed), 6.0, 4.2, None, None),
        (lambda seed: sd.negbinomial(5, 0.4, seed=seed), 7.5, 18.75, None, None),
        (lambda seed: sd.exprnd(5, seed=seed), 5.0, 25.0, None, None),
        (lambda seed: sd.gamma(2, 3, seed=seed), 6.0, 18.0, None, None),
        (lambda seed: sd.geometric(0.3, seed=seed), 1.0 / 0.3, 0.7 / 0.09, 1.0, 3.0),
        (lambda seed: sd.lognormal(2.0, 1.0, seed=seed), 2.0, 1.0, 0.3, 1.0),
        (lambda seed: sd.logistic(10.0, 2.0, seed=seed), 10.0, math.pi ** 2 * 4.0 / 3.0, None, None),
        (lambda seed: sd.montecarlo(50.0, seed=seed), 0.5, 0.25, 0.05, 0.05),
        (lambda seed: sd.poisson(5, seed=seed), 5.0, 5.0, None, None),
        (lambda seed: sd.triangular(1.0, 5.0, 10.0, seed=seed), 16.0 / 3.0, 73.0 / 18.0, None, None),
        (lambda seed: sd.weibull(2.0, 5.0, seed=seed), 5.0 * math.gamma(1.5),
         25.0 * (math.gamma(2.0) - math.gamma(1.5) ** 2), None, None),
        (lambda seed: sd.pareto(5.0, 1.0, seed=seed), 1.25, 5.0 / 48.0, 0.1, 0.15),
        # Each segment uniform, weighted by its area: 1/8, 3/8, 3/8, 1/8
        (lambda seed: sd.lookuprandom([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [3.0, 1.0], [4.0, 0.0]], seed=seed), 2.0, 5.0 / 6.0, 0.05, 0.05),
    ], ids=["normal", "uniform", "beta", "binomial", "negbinomial", "exprnd", "gamma", "geometric",
            "lognormal", "logistic", "montecarlo", "poisson", "triangular", "weibull", "pareto", "lookuprandom"])
    def test_the_same_distribution_on_both_engines(self, build, mean, var, mean_tol, var_tol):
        _run_stochastic_parity(build(7), mean, var, mean_tol, var_tol, name="seeded")

    def test_each_engine_draws_the_same_numbers_on_every_run_whatever_the_run_seed(self):
        def run(run_seed):
            model = Model(starttime=0, stoptime=30, dt=1, name="seeded_runs")
            model.converter("x").equation = sd.normal(0.0, 1.0, seed=3)
            raw = RustSdEngine().load_model(model.to_json()).simulate(["x"], seed=run_seed)
            return [value for _, value in sorted(raw["x"].items())]
        assert run(1) == run(2) == run(None)

    def test_a_seeded_draw_leaves_the_unseeded_ones_alone(self):
        def run(with_seeded):
            model = Model(starttime=0, stoptime=30, dt=1, name="seeded_beside")
            model.converter("free").equation = sd.normal(0.0, 1.0)
            if with_seeded:
                model.converter("fixed").equation = sd.normal(0.0, 1.0, seed=3)
            raw = RustSdEngine().load_model(model.to_json()).simulate(["free"], seed=5)
            return [value for _, value in sorted(raw["free"].items())]
        assert run(False) == run(True)

    def test_the_cells_of_an_array_draw_apart(self):
        model = Model(starttime=0, stoptime=200, dt=1, name="seeded_cells")
        mean = model.constant("mean")
        mean.setup_named_vector({"a": 0.0, "b": 0.0, "c": 0.0})
        model.converter("d").equation = sd.normal(mean, 1.0, seed=3)
        raw = RustSdEngine().load_model(model.to_json()).simulate(["d[a]", "d[b]", "d[c]"])
        series = [np.array([value for _, value in sorted(raw[name].items())]) for name in ("d[a]", "d[b]", "d[c]")]
        assert abs(np.corrcoef(series[0], series[1])[0, 1]) < 0.2
        assert not np.array_equal(series[1], series[2])

    def test_a_seed_that_is_no_whole_number_of_at_least_0(self):
        for seed in (-1, 2.5):
            _run_nan_parity(sd.normal(0.0, 1.0, seed=seed), "bad_seed")


def _truncated_normal_moments(mean, stddev, lower, upper):
    from scipy.stats import truncnorm
    distribution = truncnorm((lower - mean) / stddev, (upper - mean) / stddev, loc=mean, scale=stddev)
    return distribution.mean(), distribution.var()


class TestParityBoundsAndSample:
    """A random function's minimum, maximum and sample, as Stella reads them: drawn again
    until a value lies within the bounds - NaN and a report after 100 draws - and held
    from the start of each sample, which is cut down to whole steps."""

    @pytest.mark.parametrize("build, mean, var", [
        (lambda seed: sd.normal(0, 1, seed, -1, 1), *_truncated_normal_moments(0, 1, -1, 1)),
        (lambda seed: sd.normal(10, 2, seed, 9), *_truncated_normal_moments(10, 2, 9, math.inf)),
        (lambda seed: sd.uniform(0, 10, seed, 2, 4), 3.0, 1.0 / 3.0),
        (lambda seed: sd.gamma(2, 3, seed, 4, 8), None, None),
        (lambda seed: sd.poisson(4, seed, 2, 5), None, None),
    ], ids=["normal", "normal_minimum_only", "uniform", "gamma", "poisson"])
    @pytest.mark.parametrize("seeded", [True, False], ids=["seeded", "unseeded"])
    def test_a_bounded_draw_on_both_engines(self, build, mean, var, seeded):
        if mean is None:
            # The moments of the bounded distribution, measured on the Python engine: both
            # engines have to stay inside the bounds and agree with it
            model = Model(starttime=0, stoptime=N_SAMPLES, dt=1, name="bounded_reference")
            model.converter("x").equation = build(11)
            values = np.array([model.evaluate_equation("x", float(t)) for t in range(N_SAMPLES + 1)])
            mean, var = float(values.mean()), float(values.var())
        _run_stochastic_parity(build(7 if seeded else None), mean, var,
                               max(0.05, abs(mean) * 0.05), max(0.05, var * 0.2), name="bounded")

    def test_bounds_on_both_engines_alike(self):
        model = Model(starttime=0, stoptime=200, dt=1, name="bounds_par")
        expressions = {
            'equal': sd.normal(0, 1, 3, 0.5, 0.5),
            'equal_discrete': sd.poisson(4, 3, 3, 3),
            'nan_bounds': sd.uniform(0, 1, 3, sd.nan(), sd.nan()),
            'discrete_inclusive': sd.binomial(10, 0.3, 4, 2, 4),
            'montecarlo_bounded': sd.montecarlo(50, 5, 1, 1),
        }
        for name, expression in expressions.items():
            model.converter(name).equation = expression
        times = timerange(model.starttime, model.stoptime, model.dt, exclusive=False)
        raw = RustSdEngine().load_model(model.to_json()).simulate(list(expressions))
        for name in expressions:
            python = [model.evaluate_equation(name, t) for t in times]
            rust = [raw[name][rust_time_key(t)] for t in times]
            assert set(python) == set(rust) or name in ("nan_bounds", "discrete_inclusive"), name
        assert {model.evaluate_equation('discrete_inclusive', t) for t in times} == {2, 3, 4}
        assert {raw['discrete_inclusive'][rust_time_key(t)] for t in times} == {2.0, 3.0, 4.0}

    @pytest.mark.parametrize("build", [
        lambda: sd.normal(0.0, 1.0, 3, 1.0, -1.0),
        lambda: sd.normal(0.0, 1.0, 3, 10.0, 11.0),
        lambda: sd.normal(0.0, 1.0, None, 10.0, 11.0),
        lambda: sd.poisson(4.0, 3, 5.0, 2.0),
    ], ids=["reversed", "out_of_reach", "out_of_reach_unseeded", "reversed_discrete"])
    def test_bounds_that_cannot_be_met(self, build):
        _run_nan_parity(build(), "unmet_bounds")

    @pytest.mark.parametrize("sample, changes", [
        (1.0, [1.5, 2.5, 3.5]),
        (0.6, [1.0, 1.5, 2.0]),
        (0.75, [1.25, 2.0, 2.75]),
        (0.3, [0.75, 1.0, 1.25]),
        (0.0, [0.75, 1.0, 1.25]),
    ])
    @pytest.mark.parametrize("seed", [31, None], ids=["seeded", "unseeded"])
    def test_a_sample_holds_on_both_engines(self, sample, changes, seed):
        """Stella's run (`random_dt_quarter`): from 0.5 at DT 0.25 the sample is cut down to
        whole steps and counted from the start."""
        model = Model(starttime=0.5, stoptime=5.0, dt=0.25, name="sample_par")
        expressions = {'plain': sd.normal(0.0, 1.0, seed, sample=sample),
                       'bounded': sd.normal(0.0, 1.0, seed, -1.0, 1.0, sample=sample),
                       'montecarlo': sd.montecarlo(50, seed, sample=sample),
                       'of_an_element': sd.uniform(0.0, sd.time() + 1.0, seed, sample=sample)}
        for name, expression in expressions.items():
            model.converter(name).equation = expression
        times = timerange(model.starttime, model.stoptime, model.dt, exclusive=False)
        raw = RustSdEngine().load_model(model.to_json()).simulate(list(expressions))
        for name in ('plain', 'bounded', 'of_an_element'):
            for values in ([model.evaluate_equation(name, t) for t in times],
                           [raw[name][rust_time_key(t)] for t in times]):
                changed = [t for t, before, after in zip(times[1:], values, values[1:]) if after != before]
                assert changed[:3] == changes, name
        # A held MONTECARLO changes only where a sample begins - where the normal draw changes
        starts = {t for t, before, after in zip(times[1:], [model.evaluate_equation('plain', t) for t in times],
                                                [model.evaluate_equation('plain', t) for t in times][1:])
                  if after != before}
        for values in ([model.evaluate_equation('montecarlo', t) for t in times],
                       [raw['montecarlo'][rust_time_key(t)] for t in times]):
            assert {t for t, before, after in zip(times[1:], values, values[1:]) if after != before} <= starts

    def test_a_held_draw_is_drawn_again_after_a_reset(self):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="held_reset")
        model.converter("x").equation = sd.normal(0.0, 1.0, sample=2)
        first = [model.evaluate_equation("x", float(t)) for t in range(5)]
        model.reset_cache()
        second = [model.evaluate_equation("x", float(t)) for t in range(5)]
        assert first[0] == first[1] and second[0] == second[1] and first != second




# ---------------------------------------------------------------------------
# Test: Stochastic function guards (invalid params → NaN)
# ---------------------------------------------------------------------------

def _error_lines(run):
    """Call `run` and return the `[ERROR]` lines it printed, without their timestamps -
    `log` prints every error, whatever the configured modes."""
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        result = run()
    lines = [line.split(", ", 1)[1] for line in output.getvalue().splitlines()
             if "[ERROR]" in line]
    return result, lines


def _run_nan_parity(equation, name):
    """Build a model with the given equation, verify both backends return NaN and report
    it once, in the same words, however many steps are invalid."""
    model = Model(starttime=0, stoptime=1, dt=1, name=name)
    x = model.converter("x")
    x.equation = equation
    times = timerange(model.starttime, model.stoptime, model.dt, exclusive=False)

    # Python results
    values, python_errors = _error_lines(lambda: [x(t) for t in times])
    for t, val in zip(times, values):
        assert math.isnan(val), f"Python {name} at t={t}: expected NaN, got {val}"

    # Rust results
    engine = RustSdEngine()
    json_str = model.to_json()
    rust_model = engine.load_model(json_str)
    rust_results, rust_errors = _error_lines(lambda: rust_model.simulate(["x"]))
    for t in times:
        key = rust_time_key(t)
        val = rust_results["x"][key]
        assert math.isnan(val), f"Rust {name} at t={t}: expected NaN, got {val}"

    assert len(python_errors) == 1, python_errors
    assert rust_errors == python_errors
    assert " in 'x' at t=0.0: " in python_errors[0]


def _non_negative_store(dt=1.0, order=("sales", "scrap"), stoptime=12.0):
    """A store of 10 with a delivery of 3 and two outflows that want more than there is."""
    model = Model(starttime=0, stoptime=stoptime, dt=dt, name="non_negative_par")
    store = model.stock("store")
    store.initial_value = 10.0
    delivery = model.flow("delivery")
    delivery.equation = 3.0 + sd.step(4.0, 6.0)
    flows = {"sales": 8.0, "scrap": 5.0}
    outflows = []
    for name in order:
        flow = model.flow(name)
        flow.equation = flows[name] + 0.5 * sd.time()
        outflows.append(flow)
    store.inflows = [delivery]
    store.outflows = outflows
    store.non_negative = True
    return model


class TestParityNonNegativeStocks:
    """A non-negative stock's outflows, cut back in the order of their list, and the biflows
    among its flows - the serializer writes the cut back out, the engine computes it."""

    @pytest.mark.parametrize("dt", [1.0, 0.5])
    @pytest.mark.parametrize("order", [("sales", "scrap"), ("scrap", "sales")])
    def test_outflows_in_the_order_of_their_list(self, dt, order):
        run_parity(_non_negative_store(dt=dt, order=order), ["store", "delivery", "sales", "scrap"])

    @pytest.mark.parametrize("biflow_place, rate", [
        ("inflow", -5.0), ("inflow", 5.0), ("outflow", 5.0), ("outflow", -5.0)])
    def test_a_biflow_in_either_list(self, biflow_place, rate):
        model = Model(starttime=0, stoptime=8, dt=1, name="biflow_par")
        stock = model.stock("stock")
        stock.initial_value = 2.0
        exchange = model.biflow("exchange")
        exchange.equation = rate * sd.If(sd.time() < 4, 1.0, -0.5)
        outflow = model.flow("outflow")
        outflow.equation = 1.0 + 0.25 * sd.time()
        if biflow_place == "inflow":
            stock.inflows = [exchange]
            stock.outflows = [outflow]
        else:
            stock.outflows = [outflow, exchange]
        stock.non_negative = True
        run_parity(model, ["stock", "exchange", "outflow"])

    @pytest.mark.parametrize("returns_rate, transfer_rate", [(-4.0, 2.0), (2.0, -3.0), (-1.0, -6.0)])
    def test_biflows_in_both_lists(self, returns_rate, transfer_rate):
        model = Model(starttime=0, stoptime=10, dt=1, name="both_lists_par")
        store = model.stock("store")
        supply = model.flow("supply")
        supply.equation = 5.0
        returns = model.biflow("returns")
        returns.equation = returns_rate
        sales = model.flow("sales")
        sales.equation = 3.0
        transfer = model.biflow("transfer")
        transfer.equation = transfer_rate
        store.inflows = [supply, returns]
        store.outflows = [sales, transfer]
        store.non_negative = True
        run_parity(model, ["store", "supply", "returns", "sales", "transfer"])

    def test_two_inflows_running_backwards_and_one_depending_on_an_outflow(self):
        model = Model(starttime=0, stoptime=6, dt=1, name="backwards_par")
        stock = model.stock("stock")
        stock.initial_value = 3.0
        first = model.biflow("first")
        first.equation = -2.0
        second = model.biflow("second")
        second.equation = -2.0
        outflow = model.flow("outflow")
        outflow.equation = 1.0
        refill = model.flow("refill")
        refill.equation = outflow * 2.0
        stock.inflows = [refill, first, second]
        stock.outflows = [outflow]
        stock.non_negative = True
        run_parity(model, ["stock", "first", "second", "outflow", "refill"])

    def test_arrays(self):
        model = Model(starttime=0, stoptime=6, dt=1, name="arrayed_par")
        stock = model.stock("stock")
        stock.setup_named_vector({"north": 10.0, "south": 1.0})
        inflow = model.flow("inflow")
        inflow.setup_named_vector({"north": 3.0, "south": 1.0})
        first = model.flow("first")
        first.setup_named_vector({"north": 8.0, "south": 1.0})
        second = model.flow("second")
        second.setup_named_vector({"north": 9.0, "south": 5.0})
        exchange = model.biflow("exchange")
        exchange.setup_named_vector({"north": -1.0, "south": 2.0})
        stock.inflows = [inflow, exchange]
        stock.outflows = [first, second]
        stock.non_negative = True
        names = ["{}[{}]".format(element, cell) for element in ("stock", "first", "second", "exchange")
                 for cell in ("north", "south")]
        run_parity(model, names)

    def test_a_matrix(self):
        model = Model(starttime=0, stoptime=4, dt=1, name="matrix_par")
        stock = model.stock("stock")
        stock.setup_matrix([2, 2], [[10.0, 1.0], [0.0, 4.0]])
        outflow = model.flow("outflow")
        outflow.setup_matrix([2, 2], [[4.0, 4.0], [4.0, 4.0]])
        stock.outflows = [outflow]
        stock.non_negative = True
        names = ["{}[{}][{}]".format(element, row, column) for element in ("stock", "outflow")
                 for row in (0, 1) for column in (0, 1)]
        run_parity(model, names)

    @pytest.mark.allow_rust_unused
    def test_an_outflow_depending_on_a_later_one_is_refused_alike(self):
        """The order check is the Python engine's own, run by the serializer."""
        model = _non_negative_store()
        model.flows["sales"].equation = model.flows["scrap"] * 1.0
        with pytest.raises(Exception) as python:
            model.simulate(["store"])
        with pytest.raises(Exception) as rust:
            model.simulate(["store"], backend="rust")
        assert "depends on it" in str(python.value)
        assert str(rust.value) == str(python.value)


def _belt_model(fifo=False, exponential=False, fractions=(), initial=1000.0, transit=4.0,
                inflow=250.0, dt=0.25, stoptime=50.0):
    """The belt scenarios of `tests/unittests/test_belt.py` as a model: dt 0.25, transit 4,
    250 entering per time unit. `transit` and each fraction may be a function of the model
    returning an expression."""
    model = Model(starttime=0.0, stoptime=stoptime, dt=dt, name="belt_par")
    entering = model.flow("entering")
    entering.equation = inflow
    leaving = model.flow("leaving")
    belt = model.conveyor("belt")
    belt.transit_time = transit(model) if callable(transit) else transit
    belt.initial_value = initial
    belt.inflows = [entering]
    belt.outflows = [leaving]
    leaks = {}
    for k, fraction in enumerate(fractions):
        leaks[model.flow("leak_{}".format(k))] = fraction(model) if callable(fraction) else fraction
    belt.leaks = leaks
    belt.fifo = fifo
    belt.exponential_leak = exponential
    names = ["belt", "leaving"] + ["leak_{}".format(k) for k in range(len(fractions))]
    return model, names


def _later(switch, before, after):
    return lambda model: sd.If(sd.time() < switch, before, after)


class TestParityConveyors:
    """Every case of `test_belt.py` and `test_conveyor.py` that runs a model, on both engines."""

    @pytest.mark.parametrize("fifo", [False, True], ids=["traditional", "fifo"])
    @pytest.mark.parametrize("case", [
        dict(),
        dict(initial=0.0),
        dict(fractions=[0.2]),
        dict(exponential=True, fractions=[0.1]),
        dict(exponential=True, fractions=[0.1, 0.1]),
        dict(fractions=[_later(4, 0.2, 0.4)]),
        dict(fractions=[0.2], transit=_later(2, 4.0, 2.0), stoptime=100.0),
        dict(transit=_later(8, 4.0, 2.0), stoptime=24.0),
        dict(transit=_later(8, 4.0, 8.0), stoptime=24.0),
        dict(initial=0.0, transit=1.1, stoptime=3.0),
        dict(fractions=[0.2], initial=0.0, transit=1.1, stoptime=10.0),
        dict(fractions=[0.7, 0.7]),
        dict(exponential=True, fractions=[5.0, 5.0]),
        dict(initial=[1.0, 2.0, 3.0, 4.0], inflow=0.0, stoptime=4.0),
        dict(initial=[float(value) for value in range(16)], inflow=0.0, stoptime=4.0),
        dict(initial=[1.0, 2.0], inflow=0.0, stoptime=4.0),
        dict(initial=[1.0, 2.0, 3.0, 4.0, 5.0], inflow=0.0, stoptime=4.0),
        dict(fractions=[1.0, 1.0], initial=100.0, stoptime=5.0),
        dict(fractions=[0.1], initial=[1.0, 2.0, 3.0, 4.0], stoptime=5.0),
    ], ids=["steady", "empty", "linear", "exponential", "two_exponential", "switching_fraction",
            "shrinking_transit", "shorter_transit", "longer_transit", "transit_between_slats",
            "partly_leaving", "linear_beyond_content", "exponential_beyond_content", "list_per_unit",
            "list_per_slat", "short_list", "long_list", "leak_empties_slats", "list_with_leak"])
    def test_the_belt(self, fifo, case):
        model, names = _belt_model(fifo=fifo, **case)
        run_parity(model, names)

    def test_agecount_by_time_on_the_belt(self):
        model, names = _belt_model(initial=[1.0, 2.0, 3.0, 4.0], inflow=9.0, dt=1.0, stoptime=6.0)
        belt = model.stocks["belt"]
        model.converter("age_0").equation = sd.agecount(belt, 0.0, 1.0)
        model.converter("age_0_1").equation = sd.agecount(belt, 0.0, 2.0)
        model.converter("age_3").equation = sd.agecount(belt, 3.0, 4.0)
        model.converter("age_1").equation = sd.agecount(belt, 1.0, 1.0)
        model.converter("from_1").equation = sd.agecount(belt, 1.0)
        run_parity(model, names + ["age_0", "age_0_1", "age_3", "age_1", "from_1"])

    @pytest.mark.parametrize("dt", [1.0, 0.25])
    def test_agecount_with_equal_bounds_and_without_a_maximum(self, dt):
        model, names = _belt_model(initial=0.0, inflow=10.0, dt=dt, stoptime=8.0)
        belt = model.stocks["belt"]
        model.converter("aged_2").equation = sd.agecount(belt, 2, 2)
        model.converter("older").equation = sd.agecount(belt, 1)
        run_parity(model, names + ["aged_2", "older"])

    def test_the_age_group(self):
        model = Model(starttime=0.0, stoptime=60.0, dt=1.0, name="cohorts_par")
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
        model.converter("youngest").equation = sd.agecount(cohort, 0, 5)
        run_parity(model, ["aged_20_to_40", "turning_40", "deaths", "emigration", "aged_40_plus", "youngest"])

    def test_an_initial_value_that_is_an_expression_and_a_chain(self):
        model = Model(starttime=0.0, stoptime=12.0, dt=1.0, name="chain_par")
        start = model.constant("start")
        start.equation = 30.0
        inflow = model.flow("inflow")
        inflow.equation = 10.0
        middle = model.flow("middle")
        out = model.flow("out")
        first = model.conveyor("first")
        first.transit_time = 2
        first.initial_value = start * 2.0
        first.inflows = [inflow]
        first.outflows = [middle]
        second = model.conveyor("second")
        second.transit_time = 3
        second.inflows = [middle]
        second.outflows = [out]
        run_parity(model, ["first", "middle", "second", "out"])

    def test_an_inflow_reading_the_conveyor(self):
        model = Model(starttime=0.0, stoptime=6.0, dt=1.0, name="reads_par")
        out = model.flow("out")
        belt = model.conveyor("belt")
        inflow = model.flow("inflow")
        inflow.equation = belt * 0.1
        belt.transit_time = 2
        belt.initial_value = 10.0
        belt.inflows = [inflow]
        belt.outflows = [out]
        run_parity(model, ["belt", "inflow", "out"])

    @pytest.mark.allow_rust_unused
    def test_an_inflow_reading_the_outflow_is_a_cycle_on_both(self):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="cycle_par")
        out = model.flow("out")
        inflow = model.flow("inflow")
        inflow.equation = out * 0.5
        belt = model.conveyor("belt")
        belt.transit_time = 2
        belt.initial_value = 10.0
        belt.inflows = [inflow]
        belt.outflows = [out]
        with pytest.raises(Exception, match="Cyclic dependency"):
            model.simulate(["out"])
        with pytest.raises(Exception, match="Cyclic dependency"):
            model.simulate(["out"], backend="rust")

    def _regions(self):
        model = Model(starttime=0.0, stoptime=10.0, dt=0.5, name="regions_par")
        belt = model.conveyor("belt")
        belt.setup_named_vector({"north": 0.0, "south": 0.0})
        inflow = model.flow("inflow")
        inflow.setup_named_vector({"north": 10.0, "south": 20.0})
        return model, belt, inflow

    @staticmethod
    def _cells(*elements):
        return ["{}[{}]".format(element, cell) for element in elements for cell in ("north", "south")]

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
        model.converter("young").equation = sd.agecount(belt, 0, 1)
        model.converter("aged_1").equation = sd.agecount(belt, 1, 1)
        model.converter("older").equation = sd.agecount(belt, 1)
        run_parity(model, self._cells("belt", "out", "loss", "young", "aged_1", "older"))

    def test_starts_of_the_whole_and_of_a_cell(self):
        model, belt, inflow = self._regions()
        out = model.flow("out")
        belt.initial_value = [5.0]
        belt["south"].initial_value = [7.0]
        belt.transit_time = 1
        belt.outflows = [out]
        run_parity(model, self._cells("belt", "out"))

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
        run_parity(model, self._cells("belt", "out", "loss"))

    def test_a_matrix(self):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="matrix_belt_par")
        belt = model.conveyor("belt")
        belt.setup_matrix([2, 2], [[1.0, 2.0], [3.0, 4.0]])
        out = model.flow("out")
        belt.transit_time = 1
        belt.outflows = [out]
        run_parity(model, ["{}[{}][{}]".format(element, row, column) for element in ("belt", "out")
                           for row in (0, 1) for column in (0, 1)])

    @pytest.mark.allow_rust_unused
    def test_a_run_without_transit_time_or_outflow_is_refused_alike(self):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="incomplete_par")
        belt = model.conveyor("belt")
        for missing in ("no transit time", "no outflow"):
            with pytest.raises(Exception) as python:
                model.simulate(["belt"])
            with pytest.raises(Exception) as rust:
                model.simulate(["belt"], backend="rust")
            assert missing in str(python.value) and str(rust.value) == str(python.value)
            belt.transit_time = 2

    @pytest.mark.parametrize("transit, rate, message", [
        (_later(2, 2.0, 0.0), 0.1, "greater than zero"),
        (lambda model: sd.nan(), 0.1, "greater than zero"),
        (lambda model: 2.0, _later(1, 0.1, -0.1), "has to be zero or more"),
    ])
    def test_a_transit_time_or_fraction_that_becomes_invalid_is_refused_alike(self, transit, rate, message):
        model, _ = _belt_model(transit=transit, fractions=[rate], dt=1.0, stoptime=6.0)
        with pytest.raises(Exception) as python:
            model.simulate(["leaving"])
        with pytest.raises(Exception) as rust:
            model.simulate(["leaving"], backend="rust")
        assert message in str(python.value)
        assert str(python.value).strip("\"'") in str(rust.value)

    def test_a_scenario_runs_its_own_copy(self):
        model, names = _belt_model(fractions=[lambda model: model.constant("rate")], dt=1.0, stoptime=10.0)
        model.constants["rate"].equation = 0.1
        results = {}
        for backend in ("python", "rust"):
            runner = BPTK_Py.bptk()
            runner.register_scenario_manager({"sm": {"model": model}})
            runner.register_scenarios(scenario_manager="sm",
                                      scenarios={"base": {}, "leaky": {"constants": {"rate": 0.3}}})
            results[backend] = runner.run_scenarios(scenario_managers=["sm"], scenarios=["base", "leaky"],
                                                    equations=["leak_0"], backend=backend, return_format="df")
        assert np.allclose(results["python"].values, results["rust"].values)


class TestParityInteractionsAfter340:
    """The constructs that reached the engine in 3.5.0, meeting each other, at a late start
    and a fine dt, in stocks and arrays."""

    def test_a_non_negative_stock_with_a_late_start_and_a_turning_biflow(self):
        model = Model(starttime=3.0, stoptime=12.0, dt=0.25, name="late_non_negative")
        stock = model.stock("stock")
        stock.initial_value = 4.0
        exchange = model.biflow("exchange")
        exchange.equation = 3.0 * sd.sin(sd.time())
        outflow = model.flow("outflow")
        outflow.equation = 2.0
        stock.inflows = [exchange]
        stock.outflows = [outflow]
        stock.non_negative = True
        run_parity(model, ["stock", "exchange", "outflow"])

    def test_an_unnamed_vector_of_non_negative_stocks(self):
        model = Model(starttime=0, stoptime=6, dt=1, name="vector_non_negative")
        stock = model.stock("stock")
        stock.setup_vector(3, [5.0, 1.0, 0.0])
        outflow = model.flow("outflow")
        outflow.setup_vector(3, [2.0, 2.0, 2.0])
        stock.outflows = [outflow]
        stock.non_negative = True
        run_parity(model, ["{}[{}]".format(name, cell) for name in ("stock", "outflow") for cell in range(3)])

    def test_a_non_negative_stock_feeding_a_conveyor_feeding_one(self):
        model = Model(starttime=1.0, stoptime=15.0, dt=0.5, name="chain_non_negative")
        source = model.stock("source")
        source.initial_value = 20.0
        release = model.flow("release")
        release.equation = 6.0
        source.outflows = [release]
        source.non_negative = True
        arriving = model.flow("arriving")
        belt = model.conveyor("belt")
        belt.transit_time = 2.0
        belt.inflows = [release]
        belt.outflows = [arriving]
        sink = model.stock("sink")
        sales = model.flow("sales")
        sales.equation = 4.0 + 0.0 / sd.max(sd.time() - 5.0, 0.0)
        sink.inflows = [arriving]
        sink.outflows = [sales]
        sink.non_negative = True
        run_parity(model, ["source", "release", "belt", "arriving", "sink", "sales"])

    def test_arrayed_conveyors_into_arrayed_non_negative_stocks(self):
        model = Model(starttime=0, stoptime=8, dt=1, name="arrayed_chain")
        entering = model.flow("entering")
        entering.setup_vector(2, [3.0, 1.0])
        arriving = model.flow("arriving")
        belt = model.conveyor("belt")
        belt.setup_vector(2, [0.0, 0.0])
        belt.transit_time = 2
        belt.inflows = [entering]
        belt.outflows = [arriving]
        sink = model.stock("sink")
        sink.setup_vector(2, [0.0, 0.0])
        sales = model.flow("sales")
        sales.setup_vector(2, [2.0, 2.0])
        sink.inflows = [arriving]
        sink.outflows = [sales]
        sink.non_negative = True
        run_parity(model, ["{}[{}]".format(name, cell) for name in ("belt", "arriving", "sink", "sales") for cell in (0, 1)])

    def test_two_conveyors_in_a_row_at_a_late_start_and_agecount_in_a_stock(self):
        model = Model(starttime=1.0, stoptime=12.0, dt=0.5, name="two_belts_late")
        entering = model.flow("entering")
        entering.equation = 10.0 + sd.time()
        middle = model.flow("middle")
        out = model.flow("out")
        loss = model.flow("loss")
        first = model.conveyor("first")
        first.transit_time = 1.5
        first.initial_value = [1.0, 2.0]
        first.inflows = [entering]
        first.outflows = [middle]
        first.fifo = True
        second = model.conveyor("second")
        second.transit_time = 2.0
        second.inflows = [middle]
        second.outflows = [out]
        second.leaks = {loss: 0.2}
        second.exponential_leak = True
        tally = model.stock("tally")
        tally.equation = sd.agecount(second, 0, 1) + first * 0.01
        run_parity(model, ["first", "middle", "second", "out", "loss", "tally"])

    def test_nan_and_infinity_flowing_into_a_non_negative_stock(self):
        model = Model(starttime=0, stoptime=5, dt=1, name="nan_into_non_negative")
        stock = model.stock("stock")
        stock.initial_value = 3.0
        bad = model.flow("bad")
        bad.equation = sd.If(sd.time() >= 2, sd.nan(), 1.0)
        huge = model.flow("huge")
        huge.equation = sd.If(sd.time() >= 3, sd.Inf(), 0.0)
        outflow = model.flow("outflow")
        outflow.equation = 2.0 / sd.If(sd.time() >= 1, 0.0, 1.0)
        stock.inflows = [bad, huge]
        stock.outflows = [outflow]
        stock.non_negative = True
        run_parity(model, ["stock", "bad", "huge", "outflow"])

    def test_array_methods_over_an_array_that_changes_inside_a_stock(self):
        model = Model(starttime=0, stoptime=8, dt=0.5, name="array_methods_stock")
        values = model.converter("values")
        values.setup_vector(4, [0.0] * 4)
        for cell, slope in enumerate([1.0, -1.0, 0.5, 0.0]):
            values[cell].equation = 3.0 + slope * sd.time()
        stock = model.stock("stock")
        stock.equation = values.arr_rank(2) + values.arr_largest(2) + values.arr_interpolate(0.4)
        run_parity(model, ["stock"])

    def test_seeded_draws_in_an_array_inside_a_stock(self):
        model = Model(starttime=0, stoptime=400, dt=0.5, name="seeded_array_stock")
        mean = model.constant("mean")
        mean.setup_vector(2, [1.0, 2.0])
        draw = model.converter("draw")
        draw.equation = sd.normal(mean, 1.0, seed=8)
        stock = model.stock("stock")
        stock.setup_vector(2, [0.0, 0.0])
        stock.equation = draw
        model.converter("poisson").equation = sd.poisson(4.0, seed=2)
        python = model.simulate(["draw[0]", "draw[1]", "poisson"])
        rust = model.simulate(["draw[0]", "draw[1]", "poisson"], backend="rust")
        for name, expected in (("draw[0]", 1.0), ("draw[1]", 2.0), ("poisson", 2.0)):
            assert abs(python[name].mean() - expected) < 0.15 and abs(rust[name].mean() - expected) < 0.15
        assert not np.allclose(rust["draw[0]"].values - 1.0, rust["draw[1]"].values - 2.0)


class TestParityScenariosAfter340:
    """run_scenarios with scenario overrides reaching the constructs of 3.5.0."""

    def _compare(self, model, scenarios, equations):
        results = {}
        for backend in ("python", "rust"):
            runner = BPTK_Py.bptk()
            runner.register_scenario_manager({"sm": {"model": model}})
            runner.register_scenarios(scenario_manager="sm", scenarios=scenarios)
            results[backend] = runner.run_scenarios(scenario_managers=["sm"], scenarios=list(scenarios),
                                                    equations=equations, backend=backend, return_format="df")
        assert np.allclose(results["python"].values, results["rust"].values, equal_nan=True)

    def test_a_conveyor_transit_time_and_a_non_negative_outflow(self):
        model, names = _belt_model(dt=1.0, stoptime=12.0, transit=lambda model: model.constant("transit"))
        model.constants["transit"].equation = 4.0
        sink = model.stock("sink")
        sales = model.flow("sales")
        rate = model.constant("rate")
        rate.equation = 100.0
        sales.equation = rate
        sink.inflows = [model.flows["leaving"]]
        sink.outflows = [sales]
        sink.non_negative = True
        self._compare(model, {"base": {}, "fast": {"constants": {"transit": 2.0, "rate": 400.0}}},
                      ["belt", "leaving", "sink", "sales"])

    def test_an_array_cell_and_lookup_tables(self):
        model = Model(starttime=0, stoptime=6, dt=1, name="scenario_cells")
        values = model.constant("values")
        values.setup_vector(3, [1.0, 5.0, 3.0])
        model.points["tab"] = [[0, 1], [5, 3]]
        model.converter("position").equation = values.arr_rank(1)
        model.converter("largest").equation = values.arr_largest(1)
        model.converter("backward").equation = sd.lookupinv(sd.time(), "tab")
        model.converter("whole").equation = sd.lookuparea("tab")
        self._compare(model, {"base": {}, "other": {"constants": {"values[1]": -2.0},
                                                    "points": {"tab": [[0, 0], [2, 4], [10, 4]]}}},
                      ["position", "largest", "backward", "whole"])


class TestParityDivisionByZero:
    """A division by zero gives NaN and one `[ERROR]` per element, in the same words, on both
    engines - for `/`, `%` and 0 to a negative power, from the step it happens on."""

    def _compare(self, model, equations):
        python_values, python_errors = _error_lines(
            lambda: model.simulate(equations).sort_index(axis=1))
        rust_values, rust_errors = _error_lines(
            lambda: model.simulate(equations, backend="rust").sort_index(axis=1))
        assert np.array_equal(python_values.values, rust_values.values, equal_nan=True)
        assert sorted(python_errors) == sorted(rust_errors)
        return python_values, python_errors

    def _model(self):
        model = Model(starttime=0, stoptime=5, dt=1, name="by_zero")
        divisor = model.converter("divisor")
        divisor.equation = sd.If(sd.time() >= 2, 0.0, 1.0)
        return model, divisor

    def test_divide_modulo_and_power(self):
        model, divisor = self._model()
        model.converter("quotient").equation = 10.0 / divisor
        model.converter("remainder").equation = 5.0 % divisor
        model.converter("reciprocal").equation = divisor ** -1.0
        values, errors = self._compare(model, ["quotient", "remainder", "reciprocal"])
        assert list(values["quotient"][:2]) == [10.0, 10.0] and values["quotient"][2:].isna().all()
        assert len(errors) == 3
        assert "[ERROR] division by zero in 'quotient' at t=2.0." in sorted(errors)[0]

    def test_in_a_stock(self):
        model, divisor = self._model()
        stock = model.stock("level")
        stock.initial_value = 0.0
        stock.equation = 1.0 / divisor
        self._compare(model, ["level"])

    def test_a_divisor_that_is_a_stock_started_above_zero(self):
        """The start evaluates the stock before what reads it, on both engines."""
        model = Model(starttime=0, stoptime=3, dt=1, name="stock_divisor")
        level = model.stock("level")
        level.initial_value = 10.0
        model.converter("share").equation = 1.0 / level
        values, errors = self._compare(model, ["share"])
        assert errors == [] and list(values["share"]) == [0.1] * 4

    def test_a_draw_of_zero(self):
        """A numpy number divided by zero gave inf without a word on the Python engine."""
        model = Model(starttime=0, stoptime=3, dt=1, name="draw_zero")
        model.converter("ratio").equation = 1.0 / sd.poisson(0.0)
        values, errors = self._compare(model, ["ratio"])
        assert values["ratio"].isna().all() and len(errors) == 1

    def test_an_invalid_percentile_is_reported_alike(self):
        model = Model(starttime=0, stoptime=3, dt=1, name="percentile_errors")
        values = model.constant("values")
        values.setup_vector(3, [1.0, 5.0, 3.0])
        weights = model.constant("weights")
        weights.setup_vector(3, [1.0, -1.0, 2.0])
        model.converter("too_high").equation = values.arr_percentile(sd.time() * 50.0)
        model.converter("negative_weight").equation = values.arr_percentile(50.0, 0.0, weights)
        values_seen, errors = self._compare(model, ["too_high", "negative_weight"])
        assert len(errors) == 2 and values_seen["too_high"][:3].notna().all()
        assert any("percentile and lower must lie between 0 and 100" in error for error in errors)

    def test_mathematical_functions_outside_their_domain_are_reported(self):
        """NaN and an `[ERROR]` for a finite argument outside the domain; ln of 0 is minus
        infinity and an infinite argument is left to the function, both unreported."""
        model = Model(starttime=0, stoptime=1, dt=1, name="domains")
        cases = {"sqrt": sd.sqrt(-4.0), "ln": sd.ln(-1.0), "log10": sd.log10(-2.0), "arcsin": sd.arcsin(2.0),
                 "arccos": sd.arccos(-1.5), "ln_0": sd.ln(0.0), "sqrt_inf": sd.sqrt(math.inf),
                 "sqrt_minus_inf": sd.sqrt(-math.inf), "ln_inf": sd.ln(math.inf), "fine": sd.arccos(0.5)}
        for name, expression in cases.items():
            model.converter(name).equation = expression
        python, python_errors = _error_lines(lambda: model.simulate(list(cases)).sort_index(axis=1))
        rust, rust_errors = _error_lines(lambda: model.simulate(list(cases), backend="rust").sort_index(axis=1))
        assert np.allclose(python.values, rust.values, equal_nan=True)
        assert sorted(python_errors) == sorted(rust_errors) and len(python_errors) == 5
        row = python.iloc[0]
        assert row["ln_0"] == -math.inf and row["sqrt_inf"] == math.inf and math.isnan(row["sqrt_minus_inf"])

    def test_gammaln_is_the_log_of_gamma_itself(self):
        """As Stella: NaN for every argument of 0 and below, the log above."""
        model = Model(starttime=0, stoptime=1, dt=1, name="gammaln_negative")
        cases = {"negative_gamma": -2.5, "pole": -2.0, "positive_gamma": -1.5, "half": 0.5}
        for name, x in cases.items():
            model.converter(name).equation = sd.gammaln(x)
        python, errors = _error_lines(lambda: model.simulate(list(cases)).sort_index(axis=1))
        rust = model.simulate(list(cases), backend="rust").sort_index(axis=1)
        assert np.allclose(python.values, rust.values, rtol=1e-12, equal_nan=True)
        row = python.iloc[0]
        assert math.isnan(row["negative_gamma"]) and math.isnan(row["pole"]) and errors == []
        assert math.isnan(row["positive_gamma"])
        assert row["half"] == pytest.approx(math.log(math.sqrt(math.pi)))

    def test_round_to_more_digits_than_a_float_holds(self):
        """Not division by zero, but the same edge of a float: too many digits leave the
        value, too few give 0, and a value that overflows when scaled stays as it is."""
        model = Model(starttime=0, stoptime=1, dt=1, name="round_edges")
        cases = {"many": sd.round(2.345, 400.0), "few": sd.round(5.0, -400.0),
                 "scaled_over": sd.round(1e300, 100.0), "plain": sd.round(-2.5, 0.0)}
        for name, expression in cases.items():
            model.converter(name).equation = expression
        values, errors = self._compare(model, list(cases))
        assert values.iloc[0].to_dict() == {"few": 0.0, "many": 2.345, "plain": -3.0, "scaled_over": 1e300}

    def test_a_negative_base_to_a_fractional_power_is_nan(self):
        """No division by zero, and nothing reported - Python gave a complex number."""
        model, divisor = self._model()
        model.converter("root").equation = (divisor - 9.0) ** (1.0 / 3.0)
        values, errors = self._compare(model, ["root"])
        assert values["root"].isna().all() and errors == []

    def test_arrayed(self):
        model = Model(starttime=0, stoptime=3, dt=1, name="by_zero_arrayed")
        divisor = model.converter("divisor")
        divisor.setup_vector(2, [1.0, 0.0])
        top = model.converter("top")
        top.setup_vector(2, [4.0, 4.0])
        model.converter("share").equation = top / divisor
        values, errors = self._compare(model, ["share[0]", "share[1]"])
        assert list(values["share[0]"]) == [4.0] * 4 and values["share[1]"].isna().all()
        assert len(errors) == 1 and "'share[1]'" in errors[0]


class TestParityStochasticGuards:
    """Invalid parameters should return NaN in both backends."""

    @pytest.mark.parametrize("equation, name", [
        pytest.param(sd.normal(0, -1), "normal_neg_std", id="normal_negative_stddev"),
        pytest.param(sd.beta(-1, 2), "beta_neg_a", id="beta_negative_a"),
        pytest.param(sd.beta(2, 0), "beta_zero_b", id="beta_zero_b"),
        pytest.param(sd.binomial(-5, 0.5), "binom_neg_n", id="binomial_negative_n"),
        pytest.param(sd.negbinomial(-5, 0.5), "negbinom_neg_n", id="negbinomial_negative_n"),
        pytest.param(sd.poisson(-5), "poisson_neg_mu", id="poisson_negative_mu"),
        pytest.param(sd.gamma(-1, 2), "gamma_neg_shape", id="gamma_negative_shape"),
        pytest.param(sd.gamma(2, 0), "gamma_zero_scale", id="gamma_zero_scale"),
        pytest.param(sd.exprnd(-1), "exprnd_neg", id="exprnd_negative_scale"),
        pytest.param(sd.exprnd(0), "exprnd_zero", id="exprnd_zero_scale"),
        pytest.param(sd.lognormal(1, -1), "lognorm_neg_std", id="lognormal_negative_stddev"),
        pytest.param(sd.lognormal(0, 1), "lognorm_zero_mean", id="lognormal_zero_mean"),
        pytest.param(sd.logistic(0, -1), "logistic_neg_scale", id="logistic_negative_scale"),
        pytest.param(sd.triangular(10, 5, 1), "tri_lower_gt_upper", id="triangular_lower_gt_upper"),
        pytest.param(sd.triangular(0, 15, 10), "tri_mode_gt_upper", id="triangular_mode_gt_upper"),
        pytest.param(sd.triangular(5, 2, 10), "tri_mode_lt_lower", id="triangular_mode_lt_lower"),
        pytest.param(sd.weibull(-1, 2), "weibull_neg_shape", id="weibull_negative_shape"),
        pytest.param(sd.weibull(2, 0), "weibull_zero_scale", id="weibull_zero_scale"),
        pytest.param(sd.binomial(10, -0.1), "binom_p_neg", id="binomial_p_negative"),
        pytest.param(sd.binomial(10, 1.1), "binom_p_gt1", id="binomial_p_gt_one"),
        pytest.param(sd.negbinomial(0, 0.5), "negbinom_zero_n", id="negbinomial_zero_n"),
        pytest.param(sd.negbinomial(5, -0.1), "negbinom_p_neg", id="negbinomial_p_negative"),
        pytest.param(sd.negbinomial(5, 1.1), "negbinom_p_gt1", id="negbinomial_p_gt_one"),
        pytest.param(sd.triangular(5, 3, 5), "tri_leq_u_m_diff", id="triangular_lower_eq_upper_mode_differs"),
        pytest.param(sd.pareto(-1, 1), "pareto_neg_shape", id="pareto_negative_shape"),
        pytest.param(sd.pareto(0, 1), "pareto_zero_shape", id="pareto_zero_shape"),
        pytest.param(sd.pareto(1, -1), "pareto_neg_scale", id="pareto_negative_scale"),
        pytest.param(sd.pareto(1, 0), "pareto_zero_scale", id="pareto_zero_scale"),
        pytest.param(sd.invnorm(-0.5, 0, 1), "invnorm_p_neg", id="invnorm_p_negative"),
        pytest.param(sd.invnorm(1.5, 0, 1), "invnorm_p_gt1", id="invnorm_p_gt_one"),
        pytest.param(sd.invnorm(0.5, 0, -1), "invnorm_neg_std", id="invnorm_negative_stddev"),
        pytest.param(sd.normalcdf(-1, 1, 0, -1), "ncdf_neg_std", id="normalcdf_negative_stddev"),
        pytest.param(sd.normalcdf(-1, 1, 0, 0), "ncdf_zero_std", id="normalcdf_zero_stddev"),
        pytest.param(sd.invnorm(0.5, 7, 0), "invnorm_zero_std", id="invnorm_zero_stddev"),
        pytest.param(sd.geometric(1.5), "geometric_p_gt_one", id="geometric_p_gt_one"),
        pytest.param(sd.lookuprandom([[0, 1], [1, -1], [2, 1]]), "lookuprandom_negative", id="lookuprandom_negative_table"),
        pytest.param(sd.lookuprandom([[0, 0], [1, 0]]), "lookuprandom_flat_zero", id="lookuprandom_without_area"),
        pytest.param(sd.binomial(1e300, 0.5), "binomial_too_large", id="a_binomial_count_too_large_to_draw"),
        pytest.param(sd.negbinomial(1e300, 0.5), "negbinomial_too_large", id="a_negbinomial_count_too_large_to_draw"),
    ])
    def test_invalid_arguments_give_nan_on_both_engines(self, equation, name):
        _run_nan_parity(equation, name)


    def test_uniform_min_greater_than_max(self):
        """Python used to swap the bounds without a word."""
        _run_nan_parity(sd.uniform(5, 1), "uniform_min_gt_max")

    def test_geometric_p_zero(self):
        """Both engines used to answer 1."""
        _run_nan_parity(sd.geometric(0), "geometric_p_zero")

    def test_negbinomial_p_zero(self):
        """Undefined; Rust used to answer inf."""
        _run_nan_parity(sd.negbinomial(5, 0), "negbinom_p_zero")

    def test_a_poisson_rate_too_large_to_draw(self):
        """Python raised, Rust never returned."""
        _run_nan_parity(sd.poisson(1e300), "poisson_too_large")

    @pytest.mark.parametrize("equation", [
        sd.uniform(0, sd.Inf()), sd.normal(0, sd.Inf()), sd.beta(sd.Inf(), 1),
        sd.binomial(sd.Inf(), 0.5), sd.negbinomial(sd.Inf(), 0.5), sd.gamma(sd.Inf(), 1),
        sd.lognormal(sd.Inf(), 1), sd.poisson(sd.Inf()), sd.triangular(0, 1, sd.Inf()),
        sd.weibull(sd.Inf(), 1), sd.pareto(sd.Inf(), 1), sd.exprnd(sd.Inf()),
        sd.geometric(sd.Inf()), sd.logistic(0, sd.Inf()), sd.invnorm(0.5, sd.Inf(), 1),
        sd.normalcdf(0, 1, 0, sd.Inf()),
    ])
    def test_an_infinite_argument_gives_nan_without_a_report(self, equation):
        """Infinity comes from upstream like NaN. Python raised for some, returned inf
        or a number for others, and Rust never returned for poisson."""
        model = Model(starttime=0, stoptime=1, dt=1, name="inf_argument")
        x = model.converter("x")
        x.equation = equation
        values, python_errors = _error_lines(lambda: [x(0), x(1)])
        rust = RustSdEngine().load_model(model.to_json())
        results, rust_errors = _error_lines(lambda: rust.simulate(["x"]))
        assert all(math.isnan(v) for v in values + list(results["x"].values()))
        assert python_errors == [] and rust_errors == []

    def test_the_report_names_the_rule_and_the_values(self):
        model = Model(starttime=0, stoptime=1, dt=1, name="report_words")
        x = model.converter("x")
        x.equation = sd.normal(10, -1)
        _, errors = _error_lines(lambda: x(0))
        assert errors == [
            "[ERROR] normal in 'x' at t=0.0: stddev must not be negative "
            "(mean=10.0, stddev=-1.0). The result is NaN wherever the arguments are "
            "invalid; later occurrences in 'x' are not reported."]

    def test_a_nan_argument_gives_nan_without_a_report(self):
        """It comes from upstream; the builtin did nothing wrong with it."""
        model = Model(starttime=0, stoptime=1, dt=1, name="nan_argument")
        x = model.converter("x")
        x.equation = sd.normal(sd.nan(), 1)
        values, python_errors = _error_lines(lambda: [x(0), x(1)])
        rust = RustSdEngine().load_model(model.to_json())
        results, rust_errors = _error_lines(lambda: rust.simulate(["x"]))
        assert all(math.isnan(v) for v in values + list(results["x"].values()))
        assert python_errors == [] and rust_errors == []

    def test_a_run_of_invalid_steps_is_reported_once_at_its_first_step(self):
        """The bounds cross at t=3 and stay crossed; one line, naming t=3."""
        model = Model(starttime=0, stoptime=20, dt=1, name="crossing")
        lower = model.converter("lower")
        lower.equation = sd.time()
        x = model.converter("x")
        x.equation = sd.uniform(lower, 2.5)
        times = timerange(0, 20, 1, exclusive=False)
        _, python_errors = _error_lines(lambda: [x(t) for t in times])
        rust = RustSdEngine().load_model(model.to_json())
        _, rust_errors = _error_lines(lambda: rust.simulate(["x"]))
        assert len(python_errors) == 1
        assert " in 'x' at t=3.0: " in python_errors[0]
        assert rust_errors == python_errors

    def test_each_element_is_reported_on_its_own(self):
        model = Model(starttime=0, stoptime=3, dt=1, name="two_elements")
        model.converter("a").equation = sd.exprnd(0)
        model.converter("b").equation = sd.exprnd(-1)
        _, python_errors = _error_lines(
            lambda: [model.evaluate_equation(name, t) for name in "ab" for t in range(4)])
        rust = RustSdEngine().load_model(model.to_json())
        _, rust_errors = _error_lines(lambda: rust.simulate(["a", "b"]))
        assert sorted(python_errors) == sorted(rust_errors)
        assert [" in 'a' at " in e or " in 'b' at " in e for e in python_errors] == [True, True]

    def test_reset_cache_reports_again(self):
        """Once per element until the cache is reset - a new run is a new report."""
        model = Model(starttime=0, stoptime=1, dt=1, name="reset_reports")
        x = model.converter("x")
        x.equation = sd.poisson(-1)
        _, first = _error_lines(lambda: x(0))
        model.reset_cache()
        _, second = _error_lines(lambda: x(0))
        assert len(first) == 1 and second == first

    def test_step_mode_reports_once_across_steps(self):
        model = Model(starttime=0, stoptime=3, dt=1, name="stepped_reports")
        model.converter("x").equation = sd.beta(0, 1)
        rust = RustSdEngine().load_model(model.to_json())
        _, errors = _error_lines(
            lambda: [rust.init(["x"])] + [rust.step() for _ in range(3)])
        assert len(errors) == 1 and " in 'x' at t=0.0: " in errors[0]

    def test_an_invalid_argument_inside_a_stock_names_the_stock(self):
        model = Model(starttime=0, stoptime=3, dt=1, name="stock_report")
        level = model.stock("level")
        level.initial_value = 0.0
        level.equation = sd.weibull(-1, 1)
        _, python_errors = _error_lines(lambda: level(3))
        rust = RustSdEngine().load_model(model.to_json())
        _, rust_errors = _error_lines(lambda: rust.simulate(["level"]))
        assert len(python_errors) == 1 and " in 'level' at t=0.0: " in python_errors[0]
        assert rust_errors == python_errors


class TestParityInvnormDefaults:
    """Either parameter of invnorm may be left out on its own, and the other applies."""

    def test_stddev_without_a_mean(self):
        """Python dropped the stddev, Rust read it as the mean."""
        _run_constant_parity(sd.invnorm(0.9, stddev=2), 2 * 1.2815515655446004,
                             "invnorm_stddev_only")

    def test_mean_without_a_stddev(self):
        _run_constant_parity(sd.invnorm(0.9, mean=10), 10 + 1.2815515655446004,
                             "invnorm_mean_only")


# ---------------------------------------------------------------------------
# Test: Stochastic boundary values (valid edge cases)
# ---------------------------------------------------------------------------

def _run_constant_parity(equation, expected, name):
    """Verify both backends return the expected constant value."""
    model = Model(starttime=0, stoptime=1, dt=1, name=name)
    x = model.converter("x")
    x.equation = equation
    times = timerange(model.starttime, model.stoptime, model.dt, exclusive=False)

    # Python
    values, python_errors = _error_lines(lambda: [x(t) for t in times])
    for t, val in zip(times, values):
        assert abs(val - expected) < 1e-10, f"Python {name} at t={t}: expected {expected}, got {val}"

    # Rust
    engine = RustSdEngine()
    rust_model = engine.load_model(model.to_json())
    rust_results, rust_errors = _error_lines(lambda: rust_model.simulate(["x"]))
    # A boundary value is a valid argument, and nothing is reported for it.
    assert python_errors == [] and rust_errors == []
    for t in times:
        key = rust_time_key(t)
        val = rust_results["x"][key]
        assert abs(val - expected) < 1e-10, f"Rust {name} at t={t}: expected {expected}, got {val}"


class TestParityStochasticBoundary:
    """Valid boundary values should work in both backends."""

    @pytest.mark.parametrize("equation, expected, name", [
        pytest.param(sd.normal(5, 0), 5.0, "normal_zero_std", id="normal_zero_stddev"),
        pytest.param(sd.lognormal(2, 0), 2.0, "lognorm_zero_std", id="lognormal_zero_stddev"),
        pytest.param(sd.logistic(5, 0), 5.0, "logistic_zero_scale", id="logistic_zero_scale"),
        pytest.param(sd.binomial(0, 0.5), 0.0, "binom_zero_n", id="binomial_zero_n"),
        pytest.param(sd.binomial(10, 0), 0.0, "binom_p_zero", id="binomial_p_zero"),
        pytest.param(sd.binomial(10, 1), 10.0, "binom_p_one", id="binomial_p_one"),
        pytest.param(sd.poisson(0), 0.0, "poisson_zero_mu", id="poisson_zero_mu"),
        pytest.param(sd.triangular(5, 5, 5), 5.0, "tri_all_equal", id="triangular_all_equal"),
        pytest.param(sd.invnorm(0.5, 0, 1), 0.0, "invnorm_valid", id="invnorm_valid"),
    ])
    def test_a_boundary_value_gives_a_constant_on_both_engines(self, equation, expected, name):
        _run_constant_parity(equation, expected, name)



# ---------------------------------------------------------------------------
# Parity: Stateful functions (smooth / trend / delay) at the engine level.
# test_rust_engine.py already compares Rust to expected analytical values; here
# we use the strictest comparison: Python lambda vs Rust engine.
# ---------------------------------------------------------------------------

class TestParitySmooth:
    """sd.smooth — exponential smoothing of an input."""

    @pytest.mark.parametrize("starttime, dt", [(0, 0.25), (1, 0.1)])
    def test_smooth_step_input(self, starttime, dt):
        model = Model(starttime=starttime, stoptime=10, dt=dt, name='smooth_step_par')
        inp = model.converter('input')
        inp.equation = sd.step(10.0, 3.0)
        out = model.converter('out')
        out.equation = sd.smooth(model, inp, 1.0, 0.0)
        run_parity(model, ['out'], atol=1e-9)

    @pytest.mark.parametrize("stoptime, dt, height, at, averaging_time", [
        (20, 0.5, 100.0, 5.0, 10.0),    # a long averaging time: the output moves slowly
        (5, 0.01, 1.0, 1.0, 0.5),       # a very small dt: five hundred steps
    ], ids=["large_averaging_time", "small_dt"])
    def test_smooth_of_a_step(self, stoptime, dt, height, at, averaging_time):
        model = Model(starttime=0, stoptime=stoptime, dt=dt, name='smooth_of_step_par')
        inp = model.converter('input')
        inp.equation = sd.step(height, at)
        out = model.converter('out')
        out.equation = sd.smooth(model, inp, averaging_time, 0.0)
        run_parity(model, ['out'], atol=1e-9)

    def test_smooth_ramp_input(self):
        model = Model(starttime=0, stoptime=10, dt=0.25, name='smooth_ramp_par')
        inp = model.converter('input')
        inp.equation = sd.time()
        out = model.converter('out')
        out.equation = sd.smooth(model, inp, 2.0, 0.0)
        run_parity(model, ['out'], atol=1e-9)

    def test_smooth_without_initial_value(self):
        """The average starts at the input, as XMILE's SMTH1 does."""
        model = Model(starttime=1, stoptime=10, dt=0.25, name='smooth_no_initial_par')
        inp = model.converter('input')
        inp.equation = 5.0 + sd.step(10.0, 3.0)
        out = model.converter('out')
        out.equation = sd.smooth(model, inp, 2.0)
        run_parity(model, ['out'], atol=1e-9)

    def test_smooth_matched_initial(self):
        """Constant input matched to the initial value — output stays constant."""
        model = Model(starttime=0, stoptime=5, dt=0.5, name='smooth_matched_par')
        inp = model.converter('input')
        inp.equation = 42.0
        out = model.converter('out')
        out.equation = sd.smooth(model, inp, 1.0, 42.0)
        run_parity(model, ['out'], atol=1e-10)


class TestParityTrend:
    """sd.trend — fractional rate of change."""

    @pytest.mark.parametrize("dt", [0.25, 0.1])
    def test_trend_step_input(self, dt):
        model = Model(starttime=1, stoptime=10, dt=dt, name='trend_step_par')
        inp = model.converter('input')
        inp.equation = 5.0 + sd.step(10.0, 3.0)
        out = model.converter('out')
        out.equation = sd.trend(model, inp, 2.0, 0.1)
        run_parity(model, ['out'], atol=1e-9)

    def test_trend_is_0_while_the_average_is_0(self):
        """As in Stella: an input of 0 gives a trend of 0 rather than a division by zero, and
        FORCST built on it reads the input."""
        model = Model(starttime=0, stoptime=6, dt=0.25, name='trend_zero_par')
        inp = model.converter('input')
        inp.equation = sd.step(10.0, 2.0)
        out = model.converter('out')
        out.equation = sd.trend(model, inp, 4.0)
        ahead = model.converter('ahead')
        ahead.equation = sd.forecast(model, inp, 4.0, 3.0)
        run_parity(model, ['out', 'ahead'], atol=1e-9)
        trend = out.plot(return_df=True)["out"]
        assert list(trend[trend.index <= 2.0]) == [0.0] * 9
        assert trend[2.25] == pytest.approx(3.75)

    def test_trend_large_averaging_time(self):
        """Slow response to a step."""
        model = Model(starttime=0, stoptime=20, dt=0.5, name='trend_slow_par')
        inp = model.converter('input')
        inp.equation = 5.0 + sd.step(10.0, 5.0)
        out = model.converter('out')
        out.equation = sd.trend(model, inp, 8.0, 0.1)
        run_parity(model, ['out'], atol=1e-9)

    def test_trend_linear_input(self):
        model = Model(starttime=1, stoptime=10, dt=0.25, name='trend_linear_par')
        inp = model.converter('input')
        inp.equation = sd.time()
        out = model.converter('out')
        out.equation = sd.trend(model, inp, 1.0, 1.0)
        run_parity(model, ['out'], atol=1e-9)

    @pytest.mark.parametrize("dt", [0.5, 0.1])
    def test_trend_constant_input(self, dt):
        """Constant input — trend should converge to zero."""
        model = Model(starttime=0, stoptime=10, dt=dt, name='trend_const_par')
        inp = model.converter('input')
        inp.equation = 5.0
        out = model.converter('out')
        out.equation = sd.trend(model, inp, 1.0, 5.0)
        run_parity(model, ['out'], atol=1e-10)


class TestParityFallingInput:
    """smooth and trend follow an input that falls - their internal change may be
    negative, which a flow, never below zero, used to swallow on both engines."""

    @pytest.mark.parametrize("build", [
        lambda m, x: sd.smooth(m, x, 2.0),
        lambda m, x: sd.trend(m, x, 2.0),
        lambda m, x: sd.smooth3(m, x, 2.0),
        lambda m, x: sd.delay3(m, x, 2.0),
    ], ids=["smooth", "trend", "smooth3", "delay3"])
    def test_a_falling_input_is_followed(self, build):
        model = Model(starttime=0, stoptime=10, dt=0.25, name='falling_par')
        inp = model.converter('input')
        inp.equation = 10.0 - sd.step(8.0, 2.0)
        out = model.converter('out')
        out.equation = build(model, inp)
        run_parity(model, ['out'], atol=1e-9)
        assert model.evaluate_equation('out', 10.0) != model.evaluate_equation('out', 0.0)


# XMILE's cascades, each built from stocks and biflows, so they reach the engine as they are
CASCADES = {
    "smooth3": lambda m, x: sd.smooth3(m, x, 4.0),
    "smooth3_initial": lambda m, x: sd.smooth3(m, x, 4.0, 2.0),
    "smoothn": lambda m, x: sd.smoothn(m, x, 4.0, 5),
    "smoothn_floored": lambda m, x: sd.smoothn(m, x, 1.0, 9),
    "delay1": lambda m, x: sd.delay1(m, x, 4.0),
    "delay1_initial": lambda m, x: sd.delay1(m, x, 4.0, 2.0),
    "delay3": lambda m, x: sd.delay3(m, x, 4.0),
    "delayn": lambda m, x: sd.delayn(m, x, 4.0, 5),
    "delayn_floored": lambda m, x: sd.delayn(m, x, 1.0, 9),
    "forecast": lambda m, x: sd.forecast(m, x, 3.0, 5.0),
    "forecast_initial": lambda m, x: sd.forecast(m, x, 3.0, 5.0, 0.1),
    "npv": lambda m, x: sd.npv(m, x, 0.1),
    "npv_initial": lambda m, x: sd.npv(m, x, 0.1, 0.0),
}


class TestParityCascades:

    @pytest.mark.parametrize("name", sorted(CASCADES))
    def test_a_step_input(self, name):
        model = Model(starttime=1, stoptime=15, dt=0.25, name='cascade_par')
        inp = model.converter('input')
        inp.equation = 5.0 + sd.step(10.0, 3.0)
        out = model.converter('out')
        out.equation = CASCADES[name](model, inp)
        run_parity(model, ['out'], atol=1e-9)

    def test_a_delay_time_that_changes(self):
        """The material delays read their delay time every step."""
        model = Model(starttime=0, stoptime=15, dt=0.25, name='cascade_varying_par')
        inp = model.converter('input')
        inp.equation = 5.0 + sd.step(10.0, 3.0)
        delay_time = model.converter('delay_time')
        delay_time.equation = 2.0 + sd.step(4.0, 6.0)
        for name, build in [("d1", sd.delay1), ("d3", sd.delay3)]:
            out = model.converter(name)
            out.equation = build(model, inp, delay_time)
        run_parity(model, ['d1', 'd3'], atol=1e-9)


class TestParityStatelessBuiltins:
    """RAMP, MIN/MAX over n, SAFEDIV, ROOTN, PERCENT, PMT/FV/PV, CGROWTH, COUNTER, ISNAN,
    REWORK, EXPBOUND, LOGISTICBOUND, MAXSOFT and MINSOFT are built from existing operators,
    so they reach the engine unchanged."""

    def test_each_matches(self):
        model = Model(starttime=1, stoptime=15, dt=0.5, name='stateless_par')
        x = model.converter('x')
        x.equation = sd.time() - 8.0
        rate = model.converter('rate')
        rate.equation = sd.If(sd.time() > 5.0, 0.04, 0.0)
        expressions = {
            'ramp': sd.ramp(2.0, 4.0),
            'ramp_end': sd.ramp(x, 4.0, 9.0),
            'max': sd.max(x, 1.0, -3.0, 2.5),
            'min': sd.min(x, 1.0, -3.0, 2.5),
            'safediv': sd.safediv(10.0, x, -1.0),
            'rootn': sd.rootn(x, 3.0),
            'rootn_even': sd.rootn(x, 2.0),
            'percent': sd.percent(x),
            'pmt': sd.pmt(rate, 10.0, 1000.0, 100.0),
            'fv': sd.fv(rate, 10.0, -100.0, -50.0),
            'pv': sd.pv(rate, 10.0, -100.0, 50.0),
            'cgrowth': sd.cgrowth(model, x),
            'counter': sd.counter(model, 2.0, 5.0),
            'isnan': sd.isnan(sd.sqrt(x)),
            'rework': sd.rework(sd.time()),
            'expbound': sd.expbound(1.0, 9.0, x, 2.0, -4.0, 4.0),
            'expbound_linear': sd.expbound(1.0, 9.0, x, 0.0, -4.0, 4.0),
            'logisticbound': sd.logisticbound(1.0, 9.0, x, 0.0, 1.0),
            'logisticbound_closed': sd.logisticbound(1.0, 9.0, x, 0.0, 1.0, -5.0, 5.0),
            'maxsoft': sd.maxsoft(x, 1.0, 2.0),
            'maxsoft_hard': sd.maxsoft(x, 1.0, 0.0),
            'minsoft': sd.minsoft(x, 1.0, 2.0),
        }
        for name, expression in expressions.items():
            model.converter(name).equation = expression
        run_parity(model, list(expressions), atol=1e-9)


class TestParityThePast:
    """INIT, PREVIOUS, HISTORY and DERIVN are built from DELAY; the RUN statistics read the
    stored past of their variable on both engines."""

    def test_each_matches(self):
        model = Model(starttime=1, stoptime=12, dt=0.5, name='past_par')
        x = model.converter('x')
        x.equation = sd.time() ** 2.0 + sd.step(5.0, 6.0)
        counter = model.converter('counter')
        counter.equation = sd.previous(model, counter, 0.0) + 1.0
        expressions = {
            'init': sd.init(model, x),
            'init_expression': sd.init(model, x * 2.0),
            'previous': sd.previous(model, x, -1.0),
            'history': sd.history(model, x, 3.0),
            'history_now': sd.history(model, x, sd.time()),
            'history_moving': sd.history(model, x, sd.time() - 2.0),
            'derivn_1': sd.derivn(model, x, 1),
            'derivn_3': sd.derivn(model, x, 3),
            'runcum': sd.runcum(model, x),
            'runcum_window': sd.runcum(model, x, sd.time() - 2.0, sd.time()),
            'runcum_as_a_stock': sd.runcum(model, x, sd.starttime(model), sd.time() - sd.dt(model)),
            'runmax': sd.runmax(model, -x),
            'runmin_window': sd.runmin(model, x * 2.0, sd.time() - 1.5),
            'runmean': sd.runmean(model, x, 3.0, 8.0),
            'runcumtarget': sd.runcumtarget(model, x - 20.0, 60.0),
        }
        for name, expression in expressions.items():
            model.converter(name).equation = expression
        run_parity(model, list(expressions) + ['counter'], atol=1e-9)


class TestParityRunSpecsChangedLater:
    def test_dt_and_starttime_are_read_when_the_model_runs(self):
        """The Python terms of DT, STARTTIME, STOPTIME, PULSE and DELAY used to carry the
        values of the moment the equation was written, so run specs set afterwards - as a
        scenario's are - did not reach them."""
        model = Model(starttime=0, stoptime=4, dt=1, name='runspecs_later_par')
        source = model.converter('source')
        source.equation = sd.time()
        names = {'dt': sd.dt(model), 'start': sd.starttime(model), 'stop': sd.stoptime(model),
                 'pulse': sd.pulse(model, 1.0, 2.0),
                 'delayed': sd.delay(model, source, 1.0)}
        for name, equation in names.items():
            model.converter(name).equation = equation
        model.run_specs(1.0, 6.0, 0.5)
        run_parity(model, list(names), atol=1e-10)
        assert model.evaluate_equation('dt', 1.0) == 0.5


class TestParityLookupInAStock:
    def test_a_lookup_written_into_a_stock_reads_the_step_before(self):
        model = Model(starttime=0, stoptime=6, dt=1, name='lookup_stock_par')
        x = model.converter('x')
        x.equation = sd.time()
        stock = model.stock('stock')
        stock.initial_value = 0.0
        stock.equation = sd.lookup(x, [[0, 0], [10, 10]])
        run_parity(model, ['stock'], atol=1e-10)
        assert model.evaluate_equation('stock', 2.0) == 1.0


class TestParityPrecedence:
    """A compound operand keeps its own precedence. The Python engine rendered
    a - (b + c) as a - b + c and (1 + r) ** (t - s) as 1 + r ** t - s."""

    def test_compound_operands(self):
        model = Model(starttime=0, stoptime=3, dt=1, name='precedence_par')
        a = model.converter('a')
        a.equation = 8.0 + sd.time()
        b = model.converter('b')
        b.equation = 3.0
        c = model.converter('c')
        c.equation = 2.0
        expressions = {
            'sub_sum': a - (b + c),
            'sub_sub': a - (b - c),
            'literal_sub_sum': 10.0 - (b + c),
            'pow_base': (a - b) ** c,
            'pow_exponent': c ** (b - c),
            'pow_both': (1.0 + c) ** (a - b),
        }
        for name, expression in expressions.items():
            model.converter(name).equation = expression
        run_parity(model, list(expressions), atol=1e-9)
        assert model.evaluate_equation('sub_sum', 0.0) == 3.0
        assert model.evaluate_equation('pow_both', 0.0) == 243.0


class TestParityDelay:
    """sd.delay — memo lookback."""

    def test_delay_time_input(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='delay_time_par')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = sd.time()
        b.equation = sd.delay(model, a, 3.0, 0.0)
        _, rust = run_parity(model, ['a', 'b'], atol=1e-10)

        # The initial value until the duration has passed, then a(t - 3)
        assert [rust['b'][rust_time_key(t)] for t in range(6)] == [0.0, 0.0, 0.0, 0.0, 1.0, 2.0]

    def test_delay_step_input(self):
        """The step comes out shifted by the duration."""
        model = Model(starttime=0, stoptime=10, dt=0.5, name='delay_step_par')
        inp = model.converter('input')
        inp.equation = sd.step(5.0, 3.0)
        delayed = model.converter('delayed')
        delayed.equation = sd.delay(model, inp, 2.0, 0.0)
        run_parity(model, ['delayed'], atol=1e-10)

    def test_delay_zero_duration(self):
        """A duration of 0 returns the current value."""
        model = Model(starttime=0, stoptime=5, dt=1, name='delay_zero_par')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = sd.time()
        b.equation = sd.delay(model, a, 0.0, 0.0)
        run_parity(model, ['a', 'b'], atol=1e-10)

    @pytest.mark.parametrize("dt, durations", [
        (1.0, [0.3, 0.5, 0.7, 1.5, 2.5]),
        (0.25, [0.1, 0.125, 0.2, 0.3, 0.375]),
    ])
    def test_a_delay_shorter_than_dt_or_between_two_steps(self, dt, durations):
        """The duration is rounded to whole steps, half a step up: under half a step the
        delay reads its input at the same step."""
        model = Model(starttime=0.0, stoptime=6.0, dt=dt, name="short_delays")
        a = model.converter("a")
        a.equation = 2.0 + sd.time()
        names = []
        for k, duration in enumerate(durations):
            name = "delayed_{}".format(k)
            model.converter(name).equation = sd.delay(model, a, duration, 1.0)
            names.append(name)
        run_parity(model, names)

    def test_a_negative_delay_duration_is_refused_alike(self):
        model = Model(starttime=0, stoptime=3, dt=1, name="negative_delay")
        a = model.converter("a")
        a.equation = 2.0 + sd.time()
        model.converter("x").equation = sd.delay(model, a, -1.0, 1.0)
        python, python_errors = _error_lines(lambda: model.simulate(["x"]))
        rust, rust_errors = _error_lines(lambda: model.simulate(["x"], backend="rust"))
        assert python["x"].isna().all() and rust["x"].isna().all()
        assert python_errors == rust_errors and "delay_duration must not be negative" in python_errors[0]

    def test_delay_without_an_initial_value_starts_from_the_input_at_the_start(self):
        """XMILE's DELAY and the Python engine hold the input's value at the start time
        until the delay has passed. The Rust engine read the input of the current step,
        so a rising input came out rising from the first step on."""
        model = Model(starttime=0, stoptime=6, dt=1, name='delay_default_par')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = 10.0 * sd.time() + 5.0
        b.equation = sd.delay(model, a, 3.0)
        run_parity(model, ['a', 'b'], atol=1e-10)

    def test_delay_fractional_dt(self):
        model = Model(starttime=0, stoptime=8, dt=0.5, name='delay_frac_par')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = sd.time()
        b.equation = sd.delay(model, a, 2.0, -1.0)
        run_parity(model, ['a', 'b'], atol=1e-10)

    def test_delay_with_a_duration_that_varies(self):
        """The two engines described different systems here.

        Python rendered the duration with `starttime`, so its variation had no effect at
        all, while the Rust engine read it at every step.
        """
        model = Model(starttime=1, stoptime=10, dt=1, name='delay_varying_par')
        duration = model.converter('duration')
        duration.equation = sd.If(sd.time() < 6.0, 1.0, 3.0)
        a = model.converter('a')
        a.equation = sd.time() * 10.0
        b = model.converter('b')
        b.equation = sd.delay(model, a, duration, 0.0)
        run_parity(model, ['a', 'b', 'duration'], atol=1e-10)

    def test_delay_with_stock(self):
        """Delay reading from an integrated stock — interaction with Euler."""
        model = Model(starttime=0, stoptime=10, dt=1, name='delay_stock_par')
        level = model.stock('level')
        inflow = model.flow('inflow')
        delayed = model.converter('delayed_level')
        level.initial_value = 0.0
        level.equation = inflow
        inflow.equation = 5.0
        delayed.equation = sd.delay(model, level, 3.0, 0.0)
        run_parity(model, ['level', 'delayed_level'], atol=1e-10)


# ---------------------------------------------------------------------------
# Parity: ln / log10 / floor / ceil
# ---------------------------------------------------------------------------

class TestParityLnLog10:
    def test_ln(self):
        model = Model(starttime=1, stoptime=10, dt=1, name='ln_par')
        inp = model.converter('input')
        inp.equation = sd.time()
        out = model.converter('out')
        out.equation = sd.ln(inp)
        run_parity(model, ['out'], atol=1e-10)

    def test_log10(self):
        model = Model(starttime=1, stoptime=10, dt=1, name='log10_par')
        inp = model.converter('input')
        inp.equation = sd.time()
        out = model.converter('out')
        out.equation = sd.log10(inp)
        run_parity(model, ['out'], atol=1e-10)

    def test_ln_exp_composition(self):
        """ln(exp(x)) = x — identity check across both engines."""
        model = Model(starttime=0, stoptime=5, dt=1, name='ln_exp_par')
        x = model.converter('x')
        x.equation = sd.time() * 0.5
        out = model.converter('out')
        out.equation = sd.ln(sd.exp(x))
        run_parity(model, ['out'], atol=1e-10)


class TestParityFloorCeil:
    def test_floor(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='floor_par')
        inp = model.converter('input')
        inp.equation = sd.time() * 1.7 - 3.0
        out = model.converter('out')
        out.equation = sd.floor(inp)
        run_parity(model, ['out'], atol=1e-10)

    def test_ceil(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='ceil_par')
        inp = model.converter('input')
        inp.equation = sd.time() * 1.7 - 3.0
        out = model.converter('out')
        out.equation = sd.ceil(inp)
        run_parity(model, ['out'], atol=1e-10)

    def test_floor_ceil_negative_values(self):
        """floor/ceil with negative input — Rust and Python must round the same way."""
        model = Model(starttime=0, stoptime=5, dt=1, name='floor_ceil_neg_par')
        inp = model.converter('input')
        inp.equation = -sd.time() * 0.7 - 1.3
        f = model.converter('f')
        f.equation = sd.floor(inp)
        c = model.converter('c')
        c.equation = sd.ceil(inp)
        run_parity(model, ['f', 'c'], atol=1e-10)

    def test_trunc_on_both_signs(self):
        """trunc cuts towards zero on both sides of it."""
        model = Model(starttime=0, stoptime=10, dt=1, name='trunc_par')
        inp = model.converter('input')
        inp.equation = sd.time() * 1.7 - 8.5
        out = model.converter('out')
        out.equation = sd.trunc(inp)
        run_parity(model, ['out'], atol=1e-10)


# ---------------------------------------------------------------------------
# Test: feedback loops and the topological sort
#
# The engine evaluates non-stock entities eagerly, once per timestep, in an order
# computed by a topological sort at load time. Loops must therefore be broken by
# something that reads a *past* value: a stock (integrated in the previous step)
# or a `delay` (reads memo[step - delay_steps]). These tests pin down which
# shapes must load and which must stay rejected.
# ---------------------------------------------------------------------------

def assert_both_engines_reject(model, equation, message):
    """Both engines refuse the model and name the loop in the same words: Rust when it
    loads the model, Python when it is first asked for `equation`."""
    with pytest.raises(ValueError) as rust:
        RustSdEngine().load_model(model.to_json())
    with pytest.raises(ValueError) as python:
        model.evaluate_equation(equation, model.starttime)
    assert str(rust.value) == message
    assert str(python.value) == message


class TestParityFeedbackLoops:

    def test_loop_closed_by_stock(self):
        """Loop broken by a stock — the classic SD case, must keep working."""
        model = Model(starttime=1, stoptime=6, dt=1, name='loop_stock_par')
        level = model.stock('level')
        inflow = model.flow('inflow')
        rate = model.converter('rate')

        level.initial_value = 10.0
        level.equation = inflow
        inflow.equation = rate
        rate.equation = level * 0.1

        run_parity(model, ['level', 'inflow', 'rate'], atol=1e-10)

    def test_loop_closed_by_delay(self):
        """Loop broken only by a one-step delay — Python resolves it, so must Rust."""
        model = Model(starttime=1, stoptime=5, dt=1, name='loop_delay_par')
        a = model.converter('a')
        b = model.converter('b')
        c = model.converter('c')
        d = model.converter('d')

        a.equation = d + 1.0
        b.equation = a * 2.0
        c.equation = b + 1.0
        d.equation = sd.delay(model, c, 1.0, 0.0)

        run_parity(model, ['a', 'b', 'c', 'd'], atol=1e-10)

    def test_loop_closed_by_multi_step_delay(self):
        """Same loop, delay of two timesteps."""
        model = Model(starttime=0, stoptime=8, dt=1, name='loop_delay2_par')
        a = model.converter('a')
        d = model.converter('d')

        a.equation = d + 2.0
        d.equation = sd.delay(model, a, 2.0, 1.0)

        run_parity(model, ['a', 'd'], atol=1e-10)

    def test_loop_closed_by_delay_fractional_dt(self):
        """Loop broken by a delay with dt < 1, so delay_steps > 1 for a duration of 1."""
        model = Model(starttime=0, stoptime=4, dt=0.25, name='loop_delay_frac_par')
        a = model.converter('a')
        d = model.converter('d')

        a.equation = d * 1.5 + 1.0
        d.equation = sd.delay(model, a, 1.0, 0.5)

        run_parity(model, ['a', 'd'], atol=1e-10)

    def test_loop_closed_by_delay_with_entity_duration(self):
        """The delay duration is an entity rather than a literal — the shape of the
        beergame's orderDelay. Its value is unknown at load time, so breaking the loop
        requires assuming a non-literal duration is at least one dt.

        The table is constant-valued, like every orderDelay / deliveryDelay in the
        beergame. A *time-varying* duration is a separate, pre-existing Python/Rust
        divergence and deliberately not covered here.
        """
        model = Model(starttime=1, stoptime=6, dt=1, name='loop_delay_dyn_par')
        duration = model.converter('duration')
        a = model.converter('a')
        d = model.converter('d')

        model.points['delay_table'] = [(float(t), 1.0) for t in range(1, 7)]
        duration.equation = sd.lookup(sd.time(), 'delay_table')
        a.equation = d + 3.0
        d.equation = sd.delay(model, a, duration, 0.0)

        run_parity(model, ['a', 'd', 'duration'], atol=1e-10)

    def test_beergame_shaped_ordering_loop(self):
        """The shape that blocked the beergame integration: an ordering policy whose only time
        offset is the order delay, with floor() and a lookup-driven duration."""
        model = Model(starttime=1, stoptime=8, dt=1, name='ordering_loop_par')

        outgoingOrders = model.stock('outgoingOrders')
        incomingOrders = model.stock('incomingOrders')
        orderDelay = model.converter('orderDelay')
        incomingOrder = model.converter('incomingOrder')
        orderDecision = model.converter('orderDecision')
        makingOrders = model.flow('makingOrders')
        sendingOrders = model.flow('sendingOrders')
        orderFromOrderLine = model.converter('orderFromOrderLine')
        actualOrder = model.converter('actualOrder')
        outgoingOrdersIn = model.flow('outgoingOrdersIn')
        totalOutgoingOrders = model.converter('totalOutgoingOrders')
        totalIncomingOrders = model.converter('totalIncomingOrders')
        targetSupplyLine = model.constant('targetSupplyLine')
        stockAdjustmentTime = model.constant('stockAdjustmentTime')

        outgoingOrders.initial_value = 100.0
        incomingOrders.initial_value = 0.0
        targetSupplyLine.equation = 400.0
        stockAdjustmentTime.equation = 7.0

        model.points['order_delay_table'] = [(float(t), 1.0) for t in range(1, 9)]
        orderDelay.equation = sd.lookup(sd.time(), 'order_delay_table')
        incomingOrder.equation = 100.0 + 300.0 * sd.step(1.0, 3.0)

        # the loop: decision → makingOrders → delay → sendingOrders → actualOrder
        #           → outgoingOrdersIn → totalOutgoingOrders → decision
        orderDecision.equation = sd.max(
            incomingOrder + sd.floor(
                (targetSupplyLine + totalIncomingOrders - totalOutgoingOrders)
                / stockAdjustmentTime),
            0.0)
        makingOrders.equation = orderDecision
        sendingOrders.equation = sd.delay(model, makingOrders, orderDelay, 100.0)
        orderFromOrderLine.equation = sendingOrders
        actualOrder.equation = orderFromOrderLine
        outgoingOrdersIn.equation = actualOrder
        outgoingOrders.equation = outgoingOrdersIn
        totalOutgoingOrders.equation = outgoingOrdersIn + outgoingOrders
        incomingOrders.equation = incomingOrder
        totalIncomingOrders.equation = incomingOrders + incomingOrder

        run_parity(model, ['orderDecision', 'sendingOrders', 'actualOrder',
                           'totalOutgoingOrders', 'outgoingOrders'], atol=1e-10)

    def test_algebraic_loop_is_rejected(self):
        """A loop with no time offset anywhere cannot be evaluated in one pass, and the
        error names the equations that form it, in the same words on both engines."""
        model = Model(starttime=1, stoptime=5, dt=1, name='loop_algebraic_par')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = b + 1.0
        b.equation = a * 2.0

        assert_both_engines_reject(
            model, 'b', "Cyclic dependency among non-stock entities: a → b → a")

    def test_cycle_error_names_dotted_module_equations(self):
        """The names are reported verbatim, including Module namespacing — this is what
        the beergame's ordering policy would have looked like without its delay."""
        model = Model(starttime=1, stoptime=5, dt=1, name='loop_named_par')
        decision = model.converter('wholesaler.orderDecision')
        making = model.flow('wholesaler.makingOrders')
        sending = model.flow('wholesaler.sendingOrders')
        decision.equation = sending + 1.0
        making.equation = decision
        sending.equation = making

        assert_both_engines_reject(model, 'wholesaler.orderDecision', (
            "Cyclic dependency among non-stock entities: "
            "wholesaler.makingOrders → wholesaler.orderDecision → "
            "wholesaler.sendingOrders → wholesaler.makingOrders"))

    def test_loop_closed_by_zero_duration_delay_is_rejected(self):
        """delay(x, 0) reads the *current* step, so it breaks no loop."""
        model = Model(starttime=1, stoptime=5, dt=1, name='loop_delay_zero_par')
        a = model.converter('a')
        d = model.converter('d')
        a.equation = d + 1.0
        d.equation = sd.delay(model, a, 0.0, 0.0)

        assert_both_engines_reject(
            model, 'a', "Cyclic dependency among non-stock entities: a → d → a")

    def test_a_delay_that_shrinks_below_half_a_step_inside_its_loop_stops_both(self):
        """From t=3 the delay reads the step it is in, and the loop has no order there:
        Python meets it as a cycle, Rust as a delay reading what is not computed yet."""
        model = Model(starttime=0, stoptime=6, dt=1, name='loop_short_delay_par')
        a = model.converter('a')
        d = model.converter('d')
        duration = model.converter('duration')
        duration.equation = sd.If(sd.time() >= 3, 0.2, 1.0)
        a.equation = d + 1.0
        d.equation = sd.delay(model, a, duration, 0.0)

        assert [model.evaluate_equation('a', t) for t in range(3)] == [1.0, 2.0, 3.0]
        with pytest.raises(ValueError, match="Cyclic dependency among non-stock entities"):
            model.evaluate_equation('a', 3)
        with pytest.raises(RuntimeError,
                           match="Cyclic dependency among non-stock entities at t=3.0"):
            RustSdEngine().load_model(model.to_json()).simulate(['a'])

    def test_sub_elements_of_one_array_reading_each_other_are_rejected(self):
        """Arrays reach the engine one entity per sub-element, and a loop between two
        of them is a loop like any other."""
        model = Model(starttime=0, stoptime=3, dt=1, name='loop_array_par')
        a = model.converter('a')
        a.setup_vector(2, 0.0)
        a[0].equation = a[1] + 1.0
        a[1].equation = a[0] * 2.0

        assert_both_engines_reject(
            model, 'a[1]', "Cyclic dependency among non-stock entities: a[0] → a[1] → a[0]")

    def test_sub_element_reading_its_neighbour_runs(self):
        """The same two sub-elements with the dependency in one direction only."""
        model = Model(starttime=0, stoptime=3, dt=1, name='chain_array_par')
        a = model.converter('a')
        a.setup_vector(2, 0.0)
        a[0].equation = 5.0
        a[1].equation = a[0] + 1.0

        run_parity(model, ['a[0]', 'a[1]'], atol=1e-10)


# ---------------------------------------------------------------------------
# Compound operands in every argument position - TestParityCompoundOperands
# ---------------------------------------------------------------------------

COMPOUND_MODEL = object()      # the position takes the model
COMPOUND_FIXED = "fixed"       # a position that stays as it is: a constant the function needs
COMPOUND_WHOLE = "whole"       # a whole number: filled, but without growing with time
COMPOUND_ELEMENT = "element"   # a model element: the function takes no plain number there

COMPOUND_SLOPE = 0.01

# Every function, with arguments it accepts. A tuple is (value, kind).
COMPOUND_BASE = {
    "abs": [-2.5], "arccos": [0.3], "arcsin": [0.3], "arctan": [0.7],
    "ceil": [2.3], "floor": [2.3], "trunc": [-2.3], "cos": [0.5], "sin": [0.5], "tan": [0.5],
    "exp": [1.2], "ln": [2.0], "log10": [2.0], "sqrt": [4.0], "percent": [0.3],
    "gammaln": [3.5], "rootn": [27.0, 3.0],
    "factorial": [(4.0, COMPOUND_WHOLE)], "combinations": [(5.0, COMPOUND_WHOLE), (2.0, COMPOUND_WHOLE)],
    "permutations": [(5.0, COMPOUND_WHOLE), (2.0, COMPOUND_WHOLE)],
    "round": [2.345, (1.0, COMPOUND_WHOLE)],
    "coswave": [2.0, 4.0], "sinwave": [2.0, 4.0],
    "max": [1.5, 2.5], "min": [1.5, 2.5],
    "safediv": [3.0, 2.0, -1.0],
    "isnan": [2.0], "rework": [10.0],
    "expbound": [1.0, 9.0, 4.0, 2.0, 2.0, 8.0],
    "logisticbound": [1.0, 9.0, 4.0, 5.0, 1.0, 1.0, 10.0],
    "maxsoft": [1.5, 1.0, 2.0], "minsoft": [1.5, 2.0, 2.0],
    "step": [2.0, 1.0], "ramp": [1.0, 1.0, 3.0],
    "pulse": [COMPOUND_MODEL, 2.0, 1.0, 2.0],
    "fv": [0.05, 10.0, -100.0, 0.0], "pmt": [0.05, 10.0, 1000.0, 0.0],
    "pv": [0.05, 10.0, -100.0, 0.0],
    "invnorm": [0.3, 1.0, 2.0], "normalcdf": [-1.0, 1.0, 0.0, 1.0],
    "lookup": [1.5, ([[0.0, 0.0], [2.0, 4.0], [4.0, 6.0]], COMPOUND_FIXED)],
    "lookupinv": [1.5, ([[0.0, 0.0], [2.0, 4.0], [4.0, 6.0]], COMPOUND_FIXED)],
    "lookuparea": [([[0.0, 0.0], [2.0, 4.0], [4.0, 6.0]], COMPOUND_FIXED), 0.5, 3.0],
    **{name: [([[0.0, 0.0], [2.0, 4.0], [4.0, 6.0]], COMPOUND_FIXED), 0.5, 3.0]
       for name in ("lookupmax", "lookupmin", "lookupmean")},
    "cgrowth": [COMPOUND_MODEL, 10.0], "counter": [COMPOUND_MODEL, 0.0, 5.0],
    "delay": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 2.0, 1.0],
    "delay1": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 2.0, 1.0], "delay3": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 2.0, 1.0],
    "delayn": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 2.0, (3, COMPOUND_FIXED), 1.0],
    "smooth": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 2.0, 1.0], "smooth3": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 2.0, 1.0],
    "smoothn": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 2.0, (3, COMPOUND_FIXED), 1.0],
    "trend": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 2.0, 0.1],
    "forecast": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 3.0, 2.0, 0.1],
    "npv": [COMPOUND_MODEL, (10.0, COMPOUND_ELEMENT), 0.1, 0.0],
    "irr": [COMPOUND_MODEL, (10.0, COMPOUND_ELEMENT), -1.0],
    "derivn": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), (1, COMPOUND_FIXED)],
    "init": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT)], "previous": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 1.0],
    "history": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 1.0],
    **{name: [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 0.5, 3.0] for name in ("runcum", "runmax", "runmin", "runmean")},
    "runcumtarget": [COMPOUND_MODEL, (2.0, COMPOUND_ELEMENT), 3.0],
}

# Functions this file does not compare, and why.
COMPOUND_NOT_COMPARED = {
    # The engines draw from different generators: not value-comparable.
    **{name: "random" for name in ("beta", "binomial", "exprnd", "gamma", "geometric",
                                    "logistic", "lognormal", "montecarlo", "negbinomial",
                                    "normal", "pareto", "poisson", "random", "triangular", "lookuprandom", "normalpink",
                                    "uniform", "weibull")},
    # Takes a conveyor: compared in TestParityConveyors.
    "agecount": "takes a conveyor",
    # No argument to fill.
    **{name: "no argument" for name in ("Inf", "nan", "pi", "time", "dt", "starttime", "stoptime")},
    # Conditions: covered below with compound comparisons.
    **{name: "condition" for name in ("And", "Or", "Not", "If")},
}

# Positions where a function refuses an expression and wants an element or a number.
# XMILE takes an expression everywhere; each entry here is a limit of the SD DSL, and
# the test fails when one is lifted, so that the entry goes.
COMPOUND_REFUSED = {}

# Where the engine itself falls short, not the Python term: each case is expected to
# fail, strictly, so that it shows when the engine catches up.
COMPOUND_ENGINE_GAPS = {}

COMPOUND_BINARY = {
    ops.AdditionOperator: operator.add, ops.SubtractionOperator: operator.sub,
    ops.MultiplicationOperator: operator.mul, ops.DivisionOperator: operator.truediv,
    ops.PowerOperator: operator.pow, ops.ModOperator: operator.mod,
}
# Binary operators covered by tests of their own below.
COMPOUND_ELSEWHERE = {ops.And: "conditions", ops.Or: "conditions",
             ops.NumericalMultiplicationOperator: "a number and a compound"}
COMPOUND_COMPARISONS = (operator.gt, operator.lt, operator.ge, operator.le, operator.eq, operator.ne)

COMPOUND_FORMS = ("sum", "difference", "negation", "quotient")
COMPOUND_PLACES = ("converter", "stock", "arrayed")

# The array methods that take numbers besides the array: (method, the array's values, the
# other arguments). An arrayed operand is no case here - each of those arguments is one number.
COMPOUND_ARRAY_METHODS = {
    "arr_rank": ([3.0, 1.0, 3.0, 2.0], [(3.0, COMPOUND_WHOLE)]),
    "arr_interpolate": ([[0.0, 1.0, 4.0], [10.0, 11.0, 14.0]], [0.3, 0.6]),
    "arr_largest": ([3.0, 1.0, 3.0, 2.0], [(2.0, COMPOUND_WHOLE)]),
    "arr_percentile": ([3.0, 1.0, 3.0, 2.0], [40.0, 10.0]),
}


def _compound_functions():
    return sorted(name for name, function in vars(sd).items()
                  if inspect.isfunction(function) and function.__module__ == sd.__name__
                  and not name.startswith("_"))


def _compound_value(entry):
    return entry if not isinstance(entry, tuple) else entry[0]


def _compound_kind(entry):
    return None if not isinstance(entry, tuple) else entry[1]


def _compound_expression(model, form, value, slope, arrayed, tag):
    """An expression of `form` that has `value` at time 0 and grows by `slope` a step.
    Arrayed, the second cell is a little larger - by 1 for a whole number, which does not
    grow, so that it stays whole."""
    step = 1.0 if slope == 0.0 else 0.1

    def part(name, equation_of):
        element = model.converter("{}_{}".format(tag, name))
        if arrayed:
            element.setup_vector(2, [0.0, 0.0])
            for cell, offset in enumerate((0.0, step)):
                element[cell].equation = equation_of(value + offset)
        else:
            element.equation = equation_of(value)
        return element

    grow = lambda base: base + slope * sd.time()
    if form == "sum":
        return part("a", lambda v: grow(v - 1.0)) + part("b", lambda v: 1.0)
    if form == "difference":
        return part("a", lambda v: grow(v + 1.0)) - part("b", lambda v: 1.0)
    if form == "negation":
        return -part("a", lambda v: -grow(v))
    return part("a", lambda v: grow(v) * 2.0) / part("b", lambda v: 2.0)


def _compound_cases():
    for name in _compound_functions():
        if name not in COMPOUND_BASE:
            continue
        for position, entry in enumerate(COMPOUND_BASE[name]):
            if entry is COMPOUND_MODEL or _compound_kind(entry) == COMPOUND_FIXED:
                continue
            for form in COMPOUND_FORMS:
                for place in COMPOUND_PLACES:
                    yield pytest.param(name, position, form, place, id="{}-{}-{}-{}".format(name, position, form, place))


def _compound_build(name, position, form, place):
    model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="{}_{}_{}_{}".format(name, position, form, place))
    arguments = []
    for index, entry in enumerate(COMPOUND_BASE[name]):
        if entry is COMPOUND_MODEL:
            arguments.append(model)
        elif index == position:
            slope = 0.0 if _compound_kind(entry) == COMPOUND_WHOLE else COMPOUND_SLOPE
            arguments.append(_compound_expression(model, form, _compound_value(entry), slope, place == "arrayed", "x"))
        elif _compound_kind(entry) == COMPOUND_ELEMENT:
            element = model.converter("input_{}".format(index))
            element.equation = _compound_value(entry) + COMPOUND_SLOPE * sd.time()
            arguments.append(element)
        else:
            arguments.append(_compound_value(entry))
    expression = getattr(sd, name)(*arguments)
    if place == "stock":
        target = model.stock("target")
        target.initial_value = 1.0
    else:
        target = model.converter("target")
    target.equation = expression
    return model, target


def _compound_leaves(element):
    if element._elements.vector_size() == 0:
        return [element.name]
    return [name for key in element._elements.equations for name in _compound_leaves(element[key])]


class TestParityCompoundOperands:
    """Python-vs-Rust parity with a compound expression in every argument position.
    
    The other parity tests fill an argument with a single element, and four times in 3.4.0 a
    Python term lost something only a compound operand shows: the parentheses of a
    subtraction, of a power, of a delay's duration, and the time at which `lookup` read its
    input. Rust was right each time.
    
    So this file takes every function of `sd_functions` and every binary operator, and fills
    one argument position at a time with each of four compound forms - a sum, a difference,
    a negation and a quotient. Each form has the value the position needs and grows a little
    with time, so that reading it at `t` instead of `t - dt` shows. Each case runs in three
    places: a converter's equation, a stock's equation - where the term is rendered at
    `t - dt` - and, where the function takes arrays, as an arrayed operand.
    
    The list of functions is not written here: it is read from `sd_functions`. A function
    that is neither in `COMPOUND_BASE` nor in `COMPOUND_NOT_COMPARED` fails `test_every_function_is_covered`.
    """

    def test_every_function_is_covered(self):
        """A new function has to be given arguments here, or a reason it is not compared."""
        missing = [name for name in _compound_functions() if name not in COMPOUND_BASE and name not in COMPOUND_NOT_COMPARED]
        stale = [name for name in list(COMPOUND_BASE) + list(COMPOUND_NOT_COMPARED) if name not in _compound_functions()]
        assert missing == [] and stale == [], "missing: {}, no longer a function: {}".format(missing, stale)



    def test_every_binary_operator_is_covered(self):
        tabled = {entry[0] for entry in json_serializer._BINARY_OPERATORS}
        uncovered = tabled - set(COMPOUND_BINARY) - set(COMPOUND_ELSEWHERE)
        assert uncovered == set(), sorted(cls.__name__ for cls in uncovered)

    @pytest.mark.parametrize("name, position, form, place", list(_compound_cases()))

    def test_a_compound_argument(self, name, position, form, place):
        refused = COMPOUND_REFUSED.get((name, position))
        if refused is not None:
            with pytest.raises((ops.OperatorError, Exception), match=refused):
                _compound_build(name, position, form, place)
            return
        model, target = _compound_build(name, position, form, place)
        gap = COMPOUND_ENGINE_GAPS.get((name, position, place))
        if gap is not None:
            with pytest.raises(RuntimeError, match="less than half of dt"):
                run_parity(model, _compound_leaves(target), atol=1e-9)
            return
        run_parity(model, _compound_leaves(target), atol=1e-9)

    @pytest.mark.parametrize("name, position", [
        pytest.param(name, position, id="{}-{}".format(name, position))
        for name in _compound_functions() if name in COMPOUND_BASE
        for position, entry in enumerate(COMPOUND_BASE[name])
        if entry is not COMPOUND_MODEL and _compound_kind(entry) not in (COMPOUND_FIXED, COMPOUND_ELEMENT)])
    @pytest.mark.parametrize("literal", [math.nan, math.inf, -math.inf], ids=["nan", "inf", "minus_inf"])
    # numpy says so when it answers sin(inf) and the like with NaN - which is the answer here
    @pytest.mark.filterwarnings("ignore:invalid value encountered:RuntimeWarning")
    def test_a_nan_or_infinite_literal_in_every_argument_position(self, name, position, literal):
        """Written into the term as Python reads it back, and into the JSON as the builtin
        that gives it - `nan` and `inf` are no names in the term, and no numbers in JSON."""
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="{}_{}_literal".format(name, position))
        arguments = []
        for index, entry in enumerate(COMPOUND_BASE[name]):
            if entry is COMPOUND_MODEL:
                arguments.append(model)
            elif index == position:
                arguments.append(literal)
            elif _compound_kind(entry) == COMPOUND_ELEMENT:
                element = model.converter("input_{}".format(index))
                element.equation = _compound_value(entry)
                arguments.append(element)
            else:
                arguments.append(_compound_value(entry))
        model.converter("target").equation = getattr(sd, name)(*arguments)
        run_parity(model, ["target"], atol=1e-9)

    @pytest.mark.parametrize("name, position", [
        pytest.param(name, position, id="{}-{}".format(name, position))
        for name in _compound_functions() if name in COMPOUND_BASE
        for position, entry in enumerate(COMPOUND_BASE[name])
        if entry is not COMPOUND_MODEL and _compound_kind(entry) not in (COMPOUND_FIXED, COMPOUND_ELEMENT)])
    @pytest.mark.parametrize("value", [-2.5, -2.0, -1.0, 0.0, 0.5, 2.5, 1e300])
    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_an_edge_value_in_every_argument_position(self, name, position, value):
        """Negative, not whole, zero and huge, in every position: the same value or NaN on
        both engines, and the same `[ERROR]` lines where an argument is refused."""
        model = Model(starttime=1.0, stoptime=3.0, dt=0.5, name="{}_{}_edge".format(name, position))
        arguments = []
        for index, entry in enumerate(COMPOUND_BASE[name]):
            if entry is COMPOUND_MODEL:
                arguments.append(model)
            elif index == position:
                arguments.append(value)
            elif _compound_kind(entry) == COMPOUND_ELEMENT:
                element = model.converter("input_{}".format(index))
                element.equation = _compound_value(entry) + 0.1 * sd.time()
                arguments.append(element)
            else:
                arguments.append(_compound_value(entry))
        model.converter("target").equation = getattr(sd, name)(*arguments)
        python, python_errors = _error_lines(lambda: model.simulate(["target"]))
        rust, rust_errors = _error_lines(lambda: model.simulate(["target"], backend="rust"))
        assert np.allclose(python["target"].values, rust["target"].values, rtol=1e-9, atol=1e-9, equal_nan=True), \
            "python {} rust {}".format(list(python["target"]), list(rust["target"]))
        assert python_errors == rust_errors

    @pytest.mark.parametrize("place", ["stock", "arrayed", "late_start"])
    @pytest.mark.parametrize("literal", [math.nan, math.inf, -math.inf], ids=["nan", "inf", "minus_inf"])
    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_a_non_finite_literal_in_a_stock_an_array_and_a_late_start(self, place, literal):
        """The literal test for a converter, in the other places: a stock's equation, an
        arrayed operand beside it, and dt 0.5 from starttime 1."""
        late = place == "late_start"
        model = Model(starttime=1.0 if late else 0.0, stoptime=4.0, dt=0.5 if late else 1.0, name="literal_" + place)
        if place == "arrayed":
            vector = model.converter("vector")
            vector.setup_vector(2, [1.0, 2.0])
            target = model.converter("target")
            target.equation = vector * literal + sd.max(vector, literal)
            names = ["target[0]", "target[1]"]
        else:
            target = model.stock("target") if place == "stock" else model.converter("target")
            if place == "stock":
                target.initial_value = 1.0
            target.equation = sd.max(literal, 1.0) + sd.exp(literal) - sd.sqrt(literal) + sd.lookup(literal, [[0, 0], [2, 4]])
            names = ["target"]
        python = model.simulate(names)
        rust = model.simulate(names, backend="rust")
        assert np.allclose(python[names].values, rust[names].values, equal_nan=True)

    @pytest.mark.parametrize("method, position", [(method, position) for method, (_, others) in COMPOUND_ARRAY_METHODS.items()
                                                  for position in range(len(others))])
    @pytest.mark.parametrize("form", COMPOUND_FORMS)
    @pytest.mark.parametrize("place", ("converter", "stock"))
    def test_a_compound_argument_of_an_array_method(self, method, position, form, place):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="{}_{}_{}_{}".format(method, position, form, place))
        values, others = COMPOUND_ARRAY_METHODS[method]
        array = model.converter("array")
        if isinstance(values[0], list):
            array.setup_matrix([len(values), len(values[0])], values)
        else:
            array.setup_vector(len(values), values)
        arguments = []
        for index, entry in enumerate(others):
            if index == position:
                slope = 0.0 if _compound_kind(entry) == COMPOUND_WHOLE else COMPOUND_SLOPE
                arguments.append(_compound_expression(model, form, _compound_value(entry), slope, False, "x"))
            else:
                arguments.append(_compound_value(entry))
        target = model.stock("target") if place == "stock" else model.converter("target")
        if place == "stock":
            target.initial_value = 1.0
        target.equation = getattr(array, method)(*arguments)
        run_parity(model, ["target"], atol=1e-9)

    @pytest.mark.parametrize("method, position", [("arr_rank", 0), ("arr_interpolate", 0), ("arr_interpolate", 1),
                                                   ("arr_percentile", 0), ("arr_percentile", 1)])
    def test_an_arrayed_number_for_an_array_method_is_refused(self, method, position):
        """The rank and the weights are one number each: an array there is refused when the
        expression is built, on both engines alike."""
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="{}_{}_arrayed".format(method, position))
        values, others = COMPOUND_ARRAY_METHODS[method]
        array = model.converter("array")
        if isinstance(values[0], list):
            array.setup_matrix([len(values), len(values[0])], values)
        else:
            array.setup_vector(len(values), values)
        arguments = [_compound_value(entry) for entry in others]
        arguments[position] = _compound_expression(model, "sum", 0.5, COMPOUND_SLOPE, True, "x")
        with pytest.raises(ops.OperatorError, match="is one number, not an array"):
            getattr(array, method)(*arguments)

    @pytest.mark.parametrize("operation", list(COMPOUND_BINARY.values()), ids=lambda o: o.__name__)

    @pytest.mark.parametrize("side", ("left", "right"))

    @pytest.mark.parametrize("form", COMPOUND_FORMS)

    @pytest.mark.parametrize("place", COMPOUND_PLACES)

    def test_a_compound_operand(self, operation, side, form, place):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="operand")
        compound = _compound_expression(model, form, 2.0, COMPOUND_SLOPE, place == "arrayed", "x")
        other = model.converter("other")
        other.equation = 1.5 + COMPOUND_SLOPE * sd.time()
        expression = operation(compound, other) if side == "left" else operation(other, compound)
        target = model.stock("target") if place == "stock" else model.converter("target")
        target.equation = expression
        run_parity(model, _compound_leaves(target))

    @pytest.mark.parametrize("comparison", COMPOUND_COMPARISONS, ids=lambda o: o.__name__)

    @pytest.mark.parametrize("form", COMPOUND_FORMS)

    @pytest.mark.parametrize("place", COMPOUND_PLACES)

    def test_conditions_with_compound_sides(self, comparison, form, place):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="conditions")
        left = _compound_expression(model, form, 2.0, COMPOUND_SLOPE, place == "arrayed", "x")
        condition = comparison(left, 2.02)
        other = model.converter("other")
        other.equation = 1.0
        expression = sd.If(sd.And(condition, sd.Not(sd.Or(condition, other < 0.0))), left * 2.0, left - 1.0)
        target = model.stock("target") if place == "stock" else model.converter("target")
        target.equation = expression
        run_parity(model, _compound_leaves(target))

    @pytest.mark.parametrize("side", ("left", "right"))

    @pytest.mark.parametrize("form", COMPOUND_FORMS)

    @pytest.mark.parametrize("place", COMPOUND_PLACES)

    def test_a_number_and_a_compound(self, side, form, place):
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="number")
        compound = _compound_expression(model, form, 2.0, COMPOUND_SLOPE, place == "arrayed", "x")
        expression = 3.0 * compound if side == "left" else compound * 3.0
        target = model.stock("target") if place == "stock" else model.converter("target")
        target.equation = expression
        run_parity(model, _compound_leaves(target))


# Valid arguments of each random function, in order; whole numbers do not grow with time.
COMPOUND_RANDOM = {
    "beta": [2.0, 3.0], "binomial": [(10.0, COMPOUND_WHOLE), 0.3], "exprnd": [2.0],
    "gamma": [2.0, 1.5], "geometric": [0.3], "logistic": [1.0, 2.0], "lognormal": [1.0, 0.5],
    "lookuprandom": [],  # takes a table, no expression
    "montecarlo": [40.0], "negbinomial": [(3.0, COMPOUND_WHOLE), 0.4],
    "normal": [5.0, 2.0], "normalpink": [COMPOUND_MODEL, 5.0, 2.0, 3.0], "pareto": [3.0, 2.0],
    "poisson": [3.0], "random": [1.0, 4.0], "triangular": [1.0, 2.0, 5.0], "uniform": [1.0, 4.0],
    "weibull": [1.5, 2.0],
}


def _random_cases():
    for name, entries in COMPOUND_RANDOM.items():
        for position, entry in enumerate(entries):
            if entry is not COMPOUND_MODEL:
                for form in COMPOUND_FORMS:
                    yield pytest.param(name, position, form, id="{}-{}-{}".format(name, position, form))


class TestRandomFunctionsWithCompoundArguments:
    """The random functions are left out of the parity above, since the engines draw from
    different generators. Each engine is compared with itself instead: a compound argument
    has to draw what the same value through a single element draws, with the same seed."""

    def test_every_random_function_is_covered(self):
        random_functions = {name for name, reason in COMPOUND_NOT_COMPARED.items() if reason == "random"}
        assert random_functions == set(COMPOUND_RANDOM)

    @pytest.mark.parametrize("backend", ["python", "rust"])
    @pytest.mark.parametrize("name, position, form", list(_random_cases()))
    def test_a_compound_argument_draws_as_its_value(self, name, position, form, backend):
        drawn = []
        for compound in (True, False):
            # dt other than 1, so that a term scaled by dt shows a missing parenthesis
            model = Model(starttime=0.0, stoptime=6.0, dt=0.5, name="{}_{}_{}".format(name, position, form))
            arguments = []
            for index, entry in enumerate(COMPOUND_RANDOM[name]):
                if entry is COMPOUND_MODEL:
                    arguments.append(model)
                elif index != position:
                    arguments.append(_compound_value(entry))
                elif compound:
                    arguments.append(_compound_expression(model, form, _compound_value(entry), 0.0, False, "x"))
                else:
                    single = model.converter("single")
                    single.equation = _compound_value(entry)
                    arguments.append(single)
            model.converter("target").equation = getattr(sd, name)(*arguments, seed=7)
            drawn.append(model.simulate(["target"], backend=backend)["target"].to_numpy(float))
        assert np.array_equal(drawn[0], drawn[1], equal_nan=True), "{} against {}".format(*drawn)


# Expressions built at random and computed by plain Python arithmetic - a reference that
# neither engine shares, so that it sees a mistake both of them make the same way.
ORACLE_CONSTANTS = {"a": 10.0, "b": 3.0, "c": 2.0, "d": -7.5}
ORACLE_BINARY = ("+", "-", "*", "/", "**", "%")
ORACLE_COMPARISONS = {">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le,
                      "==": operator.eq, "!=": operator.ne}


def _oracle_tree(draw, depth):
    """A random expression of at most `depth` levels, as nested tuples."""
    if depth == 0 or draw.random() < 0.2:
        leaf = draw.choice(["number", "constant", "constant", "time"])
        if leaf == "number":
            return ("number", draw.choice([0.5, 1.0, 2.0, 3.0, -4.0]))
        return ("constant", draw.choice(sorted(ORACLE_CONSTANTS))) if leaf == "constant" else ("time",)
    kind = draw.choice(["binary"] * 6 + ["negation", "max", "min", "abs", "if"])
    if kind == "binary":
        symbol = draw.choice(ORACLE_BINARY)
        if symbol == "**":
            # A small exponent of its own, so that the values stay in range
            return ("**", _oracle_tree(draw, depth - 1), ("number", draw.choice([0.0, 1.0, 2.0, 3.0, -1.0])))
        return (symbol, _oracle_tree(draw, depth - 1), _oracle_tree(draw, depth - 1))
    if kind in ("negation", "abs"):
        return (kind, _oracle_tree(draw, depth - 1))
    if kind == "if":
        return ("if", draw.choice(sorted(ORACLE_COMPARISONS)), _oracle_tree(draw, depth - 1),
                _oracle_tree(draw, depth - 1), _oracle_tree(draw, depth - 1), _oracle_tree(draw, depth - 1))
    return (kind, _oracle_tree(draw, depth - 1), _oracle_tree(draw, depth - 1))


def _oracle_value(node, t):
    """The value plain Python gives: NaN where a divisor is 0 and for a negative base to a
    fractional power, a floored modulo - XMILE's rules, computed without the library."""
    kind = node[0]
    if kind == "number":
        return node[1]
    if kind == "constant":
        return ORACLE_CONSTANTS[node[1]]
    if kind == "time":
        return t
    if kind == "negation":
        return -_oracle_value(node[1], t)
    if kind == "abs":
        return abs(_oracle_value(node[1], t))
    if kind == "if":
        left, right = _oracle_value(node[2], t), _oracle_value(node[3], t)
        return _oracle_value(node[4] if ORACLE_COMPARISONS[node[1]](left, right) else node[5], t)
    left, right = _oracle_value(node[1], t), _oracle_value(node[2], t)
    if kind == "max":
        return max(left, right)
    if kind == "min":
        return min(left, right)
    if kind == "+":
        return left + right
    if kind == "-":
        return left - right
    if kind == "*":
        return left * right
    if kind in ("/", "%"):
        if right == 0:
            return math.nan
        return left / right if kind == "/" else left % right
    if left == 0 and right < 0 or left < 0 and right != int(right):
        return math.nan
    return left ** right


def _oracle_expression(node, constants):
    """The same expression in the SD DSL."""
    kind = node[0]
    if kind == "number":
        return node[1]
    if kind == "constant":
        return constants[node[1]]
    if kind == "time":
        return sd.time()
    if kind == "negation":
        return -_oracle_expression(node[1], constants)
    if kind == "abs":
        return sd.abs(_oracle_expression(node[1], constants))
    if kind == "if":
        left, right = _oracle_expression(node[2], constants), _oracle_expression(node[3], constants)
        return sd.If(ORACLE_COMPARISONS[node[1]](left, right), _oracle_expression(node[4], constants),
                     _oracle_expression(node[5], constants))
    left, right = _oracle_expression(node[1], constants), _oracle_expression(node[2], constants)
    if kind in ("max", "min"):
        return getattr(sd, kind)(left, right)
    return {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv,
            "**": operator.pow, "%": operator.mod}[kind](left, right)


def _oracle_text(node):
    kind = node[0]
    if kind == "number":
        return repr(node[1])
    if kind == "constant":
        return node[1]
    if kind == "time":
        return "t"
    if kind in ("negation", "abs"):
        return "{}({})".format("-" if kind == "negation" else "abs", _oracle_text(node[1]))
    if kind == "if":
        return "if({} {} {}, {}, {})".format(_oracle_text(node[2]), node[1], _oracle_text(node[3]),
                                              _oracle_text(node[4]), _oracle_text(node[5]))
    if kind in ("max", "min"):
        return "{}({}, {})".format(kind, _oracle_text(node[1]), _oracle_text(node[2]))
    return "({} {} {})".format(_oracle_text(node[1]), kind, _oracle_text(node[2]))


def _oracle_parts(node):
    yield node
    for child in node[1:]:
        if isinstance(child, tuple):
            yield from _oracle_parts(child)


def _oracle_trees(count, seed):
    """`count` expressions each part of which is finite at every step - a NaN or an
    infinity is the edge tests' subject, and Python's min and max of a NaN depend on the
    order of their arguments."""
    draw = random.Random(seed)
    trees = []
    while len(trees) < count:
        tree = _oracle_tree(draw, 4)
        if tree[0] in ("number", "constant", "time"):
            continue
        try:
            values = [_oracle_value(part, t) for part in _oracle_parts(tree) for t in timerange(1.0, 4.5, 0.5)]
        except (OverflowError, ZeroDivisionError):
            continue
        if all(math.isfinite(value) and abs(value) < 1e12 for value in values):
            trees.append(tree)
    return trees


class TestExpressionsAgainstPlainArithmetic:
    """Expressions built at random, run on both engines and compared with what plain
    Python arithmetic gives. Parity cannot see a mistake both engines share; this can -
    and it is the test that would have caught `a - (b + c)` computed as `a - b + c`."""

    TREES = _oracle_trees(500, seed=20261022)

    @pytest.mark.parametrize("backend", ["python", "rust"])
    @pytest.mark.parametrize("place", ["converter", "stock"])
    def test_every_expression(self, place, backend):
        # dt other than 1 and a late start, so that a term scaled by dt or read at the
        # wrong time shows
        times = list(timerange(1.0, 4.5, 0.5))
        wrong = []
        for number, tree in enumerate(self.TREES):
            model = Model(starttime=1.0, stoptime=4.0, dt=0.5, name="oracle_{}".format(number))
            constants = {}
            for name, value in ORACLE_CONSTANTS.items():
                constants[name] = model.constant(name)
                constants[name].equation = value
            if place == "stock":
                target = model.stock("target")
                target.initial_value = 1.0
                expected, level = [], 1.0
                for t in times:
                    expected.append(level)
                    level += 0.5 * _oracle_value(tree, t)
            else:
                target = model.converter("target")
                expected = [_oracle_value(tree, t) for t in times]
            target.equation = _oracle_expression(tree, constants)
            computed = model.simulate(["target"], backend=backend)["target"].tolist()
            if not np.allclose(computed, expected, rtol=1e-9, atol=1e-9):
                wrong.append("{}: {} instead of {}".format(_oracle_text(tree), computed, expected))
        assert wrong == [], "{} of {} wrong, the first ones:\n".format(len(wrong), len(self.TREES)) + "\n".join(wrong[:5])
