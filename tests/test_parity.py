"""
Parity tests: build SD DSL models in Python, serialize via to_json(),
run in both Python and Rust engines, and compare results at every timestep.

This verifies that the Rust engine produces identical results to the
Python SD DSL for all supported features.
"""

import math
import numpy as np
import pytest
from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
from BPTK_Py.util import timerange
from BPTK_Py._rust_engine import RustSdEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rust_time_key(t):
    """Format time value to match Rust engine's time key format."""
    if t == int(t):
        return f"{t:.1f}"
    else:
        return str(t)


def run_parity(model, equations, atol=1e-10):
    """
    Run a model through both Python and Rust engines and compare results.

    Args:
        model: an SD DSL Model instance (fully defined)
        equations: list of equation/entity names to compare
        atol: absolute tolerance for pytest.approx

    Returns:
        (python_results, rust_results) dicts for further inspection if needed.
    """
    # --- Python results ---
    py_results = {}
    times = timerange(model.starttime, model.stoptime, model.dt, exclusive=False)
    for eq_name in equations:
        # Look up the element by name
        element = (
            model.stocks.get(eq_name)
            or model.flows.get(eq_name)
            or model.biflows.get(eq_name)
            or model.converters.get(eq_name)
            or model.constants.get(eq_name)
        )
        assert element is not None, f"Element '{eq_name}' not found in model"
        py_results[eq_name] = {t: element(t) for t in times}

    # --- Rust results ---
    json_str = model.to_json()
    engine = RustSdEngine()
    rust_model = engine.load_model(json_str)
    rust_results = rust_model.simulate(equations)

    # --- Compare ---
    for eq_name in equations:
        for t in times:
            py_val = py_results[eq_name][t]
            key = _rust_time_key(t)
            assert key in rust_results[eq_name], \
                f"Missing Rust key '{key}' for {eq_name}"
            rust_val = rust_results[eq_name][key]
            assert py_val == pytest.approx(rust_val, abs=atol), \
                f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"

    return py_results, rust_results


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
        """Test round() for values that don't land on exact .5 boundaries.

        KNOWN DIFFERENCE: Python uses banker's rounding (round half to even)
        while Rust uses round half away from zero. For example:
          - Python: round(0.5) = 0, round(1.5) = 2, round(2.5) = 2
          - Rust:   round(0.5) = 1, round(1.5) = 2, round(2.5) = 3

        This test avoids .5 boundaries to verify round() works identically
        for unambiguous cases. The .5 boundary difference is documented
        in the progress report.
        """
        model = Model(starttime=0, stoptime=5, dt=1, name='round')
        f = model.converter("round_val")
        f.equation = sd.round(sd.time() + 0.3, 0)
        run_parity(model, ['round_val'])

    def test_round_half_difference(self):
        """Demonstrate the known rounding difference at exact .5 boundaries.

        Python: banker's rounding (round half to even)
        Rust:   round half away from zero

        This test documents the difference — it is NOT a bug.
        """
        model = Model(starttime=0, stoptime=4, dt=0.5, name='round_half')
        f = model.converter("round_val")
        f.equation = sd.round(sd.time(), 0)

        # Python results
        times = timerange(model.starttime, model.stoptime, model.dt, exclusive=False)
        py_results = {t: f(t) for t in times}

        # Rust results
        engine = RustSdEngine()
        rust_model = engine.load_model(model.to_json())
        rust_results = rust_model.simulate(["round_val"])

        # At non-.5 values they agree
        for t in [0.0, 1.0, 2.0, 3.0, 4.0]:
            key = _rust_time_key(t)
            assert py_results[t] == rust_results["round_val"][key]

        # At .5 boundaries they may differ due to different rounding rules
        for t in [0.5, 1.5, 2.5, 3.5]:
            key = _rust_time_key(t)
            py_val = py_results[t]
            rust_val = rust_results["round_val"][key]
            # Both are valid roundings — they just use different tie-breaking
            assert abs(py_val - t) <= 0.5, f"Python round({t}) = {py_val}"
            assert abs(rust_val - t) <= 0.5, f"Rust round({t}) = {rust_val}"

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
        run_parity(model, ['x'])

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

    def test_biflow_oscillator(self):
        """Biflow allows negative values — simple oscillator."""
        model = Model(starttime=0, stoptime=10, dt=0.25, name='biflow_osc')
        position = model.stock("position")
        position.initial_value = 1.0
        velocity = model.biflow("velocity")
        velocity.equation = -position
        position.equation = velocity
        run_parity(model, ['position', 'velocity'])


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
                           mean_tol=None, var_tol=None, name="stoch"):
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
        model = Model(starttime=0, stoptime=N_SAMPLES, dt=1,
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
            values = [raw["x"][_rust_time_key(t)] for t in times]

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
        # lognormal(mean=0, stddev=1): mean=exp(0.5)≈1.649, var=(exp(1)-1)*exp(1)≈4.671
        import math
        mu, sigma = 0.0, 1.0
        _run_stochastic_parity(sd.lognormal(mu, sigma),
                               math.exp(mu + sigma ** 2 / 2),
                               (math.exp(sigma ** 2) - 1) * math.exp(2 * mu + sigma ** 2),
                               mean_tol=0.3, var_tol=3.0, name="lognormal")

    def test_poisson(self):
        # poisson(mu=5): mean=5, var=5
        _run_stochastic_parity(sd.poisson(5), 5.0, 5.0, name="poisson")

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
        # Python SD DSL: np.random.pareto(shape) * scale → shifted Pareto (min=0)
        # mean = scale / (shape - 1), var = scale² * shape / ((shape-1)² * (shape-2))
        # Using shape=5 so kurtosis is finite (requires shape>4), which makes
        # sample variance converge reliably with N=5000.
        alpha, xm = 5.0, 1.0
        _run_stochastic_parity(sd.pareto(alpha, xm),
                               xm / (alpha - 1),
                               xm ** 2 * alpha / ((alpha - 1) ** 2 * (alpha - 2)),
                               mean_tol=0.1, var_tol=0.15, name="pareto")

    def test_logistic(self):
        # logistic(mean=10, scale=2): mean=10, var=π²*scale²/3≈13.159
        import math
        mu, s = 10.0, 2.0
        _run_stochastic_parity(sd.logistic(mu, s),
                               mu,
                               (math.pi ** 2 * s ** 2) / 3.0,
                               name="logistic")


# ---------------------------------------------------------------------------
# Test: Stochastic function guards (invalid params → NaN)
# ---------------------------------------------------------------------------

def _run_nan_parity(equation, name):
    """Build a model with the given equation, verify both backends return NaN."""
    model = Model(starttime=0, stoptime=1, dt=1, name=name)
    x = model.converter("x")
    x.equation = equation
    times = timerange(model.starttime, model.stoptime, model.dt, exclusive=False)

    # Python results
    for t in times:
        val = x(t)
        assert math.isnan(val), f"Python {name} at t={t}: expected NaN, got {val}"

    # Rust results
    engine = RustSdEngine()
    json_str = model.to_json()
    rust_model = engine.load_model(json_str)
    rust_results = rust_model.simulate(["x"])
    for t in times:
        key = _rust_time_key(t)
        val = rust_results["x"][key]
        assert math.isnan(val), f"Rust {name} at t={t}: expected NaN, got {val}"


class TestParityStochasticGuards:
    """Invalid parameters should return NaN in both backends."""

    def test_normal_negative_stddev(self):
        _run_nan_parity(sd.normal(0, -1), "normal_neg_std")

    def test_beta_negative_a(self):
        _run_nan_parity(sd.beta(-1, 2), "beta_neg_a")

    def test_beta_zero_b(self):
        _run_nan_parity(sd.beta(2, 0), "beta_zero_b")

    def test_binomial_negative_n(self):
        _run_nan_parity(sd.binomial(-5, 0.5), "binom_neg_n")

    def test_negbinomial_negative_n(self):
        _run_nan_parity(sd.negbinomial(-5, 0.5), "negbinom_neg_n")

    def test_poisson_negative_mu(self):
        _run_nan_parity(sd.poisson(-5), "poisson_neg_mu")

    def test_gamma_negative_shape(self):
        _run_nan_parity(sd.gamma(-1, 2), "gamma_neg_shape")

    def test_gamma_zero_scale(self):
        _run_nan_parity(sd.gamma(2, 0), "gamma_zero_scale")

    def test_exprnd_negative_scale(self):
        _run_nan_parity(sd.exprnd(-1), "exprnd_neg")

    def test_exprnd_zero_scale(self):
        _run_nan_parity(sd.exprnd(0), "exprnd_zero")

    def test_lognormal_negative_stddev(self):
        _run_nan_parity(sd.lognormal(0, -1), "lognorm_neg_std")

    def test_logistic_negative_scale(self):
        _run_nan_parity(sd.logistic(0, -1), "logistic_neg_scale")

    def test_triangular_lower_gt_upper(self):
        _run_nan_parity(sd.triangular(10, 5, 1), "tri_lower_gt_upper")

    def test_triangular_mode_gt_upper(self):
        _run_nan_parity(sd.triangular(0, 15, 10), "tri_mode_gt_upper")

    def test_triangular_mode_lt_lower(self):
        _run_nan_parity(sd.triangular(5, 2, 10), "tri_mode_lt_lower")

    def test_weibull_negative_shape(self):
        _run_nan_parity(sd.weibull(-1, 2), "weibull_neg_shape")

    def test_weibull_zero_scale(self):
        _run_nan_parity(sd.weibull(2, 0), "weibull_zero_scale")

    def test_binomial_p_negative(self):
        _run_nan_parity(sd.binomial(10, -0.1), "binom_p_neg")

    def test_binomial_p_gt_one(self):
        _run_nan_parity(sd.binomial(10, 1.1), "binom_p_gt1")

    def test_negbinomial_zero_n(self):
        _run_nan_parity(sd.negbinomial(0, 0.5), "negbinom_zero_n")

    def test_negbinomial_p_negative(self):
        _run_nan_parity(sd.negbinomial(5, -0.1), "negbinom_p_neg")

    def test_negbinomial_p_gt_one(self):
        _run_nan_parity(sd.negbinomial(5, 1.1), "negbinom_p_gt1")

    def test_triangular_lower_eq_upper_mode_differs(self):
        _run_nan_parity(sd.triangular(5, 3, 5), "tri_leq_u_m_diff")

    def test_pareto_negative_shape(self):
        _run_nan_parity(sd.pareto(-1, 1), "pareto_neg_shape")

    def test_pareto_zero_shape(self):
        _run_nan_parity(sd.pareto(0, 1), "pareto_zero_shape")

    def test_pareto_negative_scale(self):
        _run_nan_parity(sd.pareto(1, -1), "pareto_neg_scale")

    def test_pareto_zero_scale(self):
        _run_nan_parity(sd.pareto(1, 0), "pareto_zero_scale")

    def test_invnorm_p_negative(self):
        _run_nan_parity(sd.invnorm(-0.5, 0, 1), "invnorm_p_neg")

    def test_invnorm_p_gt_one(self):
        _run_nan_parity(sd.invnorm(1.5, 0, 1), "invnorm_p_gt1")

    def test_invnorm_negative_stddev(self):
        _run_nan_parity(sd.invnorm(0.5, 0, -1), "invnorm_neg_std")

    def test_normalcdf_negative_stddev(self):
        _run_nan_parity(sd.normalcdf(-1, 1, 0, -1), "ncdf_neg_std")

    def test_normalcdf_zero_stddev(self):
        _run_nan_parity(sd.normalcdf(-1, 1, 0, 0), "ncdf_zero_std")

    def test_invnorm_zero_stddev(self):
        _run_nan_parity(sd.invnorm(0.5, 7, 0), "invnorm_zero_std")


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
    for t in times:
        val = x(t)
        assert abs(val - expected) < 1e-10, f"Python {name} at t={t}: expected {expected}, got {val}"

    # Rust
    engine = RustSdEngine()
    rust_model = engine.load_model(model.to_json())
    rust_results = rust_model.simulate(["x"])
    for t in times:
        key = _rust_time_key(t)
        val = rust_results["x"][key]
        assert abs(val - expected) < 1e-10, f"Rust {name} at t={t}: expected {expected}, got {val}"


class TestParityStochasticBoundary:
    """Valid boundary values should work in both backends."""

    def test_normal_zero_stddev(self):
        _run_constant_parity(sd.normal(5, 0), 5.0, "normal_zero_std")

    def test_lognormal_zero_stddev(self):
        _run_constant_parity(sd.lognormal(0, 0), 1.0, "lognorm_zero_std")

    def test_logistic_zero_scale(self):
        _run_constant_parity(sd.logistic(5, 0), 5.0, "logistic_zero_scale")

    def test_binomial_zero_n(self):
        _run_constant_parity(sd.binomial(0, 0.5), 0.0, "binom_zero_n")

    def test_binomial_p_zero(self):
        _run_constant_parity(sd.binomial(10, 0), 0.0, "binom_p_zero")

    def test_binomial_p_one(self):
        _run_constant_parity(sd.binomial(10, 1), 10.0, "binom_p_one")

    def test_poisson_zero_mu(self):
        _run_constant_parity(sd.poisson(0), 0.0, "poisson_zero_mu")

    def test_triangular_all_equal(self):
        _run_constant_parity(sd.triangular(5, 5, 5), 5.0, "tri_all_equal")

    def test_invnorm_valid(self):
        _run_constant_parity(sd.invnorm(0.5, 0, 1), 0.0, "invnorm_valid")


# ---------------------------------------------------------------------------
# Parity: Stateful functions (smooth / trend / delay) at the engine level.
# test_rust_engine.py already compares Rust to expected analytical values; here
# we use the strictest comparison: Python lambda vs Rust engine.
# ---------------------------------------------------------------------------

class TestParitySmooth:
    """sd.smooth — exponential smoothing of an input."""

    def test_smooth_step_input(self):
        model = Model(starttime=0, stoptime=10, dt=0.25, name='smooth_step_par')
        inp = model.converter('input')
        inp.equation = sd.step(10.0, 3.0)
        out = model.converter('out')
        out.equation = sd.smooth(model, inp, 1.0, 0.0)
        run_parity(model, ['out'], atol=1e-9)

    def test_smooth_ramp_input(self):
        model = Model(starttime=0, stoptime=10, dt=0.25, name='smooth_ramp_par')
        inp = model.converter('input')
        inp.equation = sd.time()
        out = model.converter('out')
        out.equation = sd.smooth(model, inp, 2.0, 0.0)
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

    def test_trend_step_input(self):
        model = Model(starttime=1, stoptime=10, dt=0.25, name='trend_step_par')
        inp = model.converter('input')
        inp.equation = sd.step(10.0, 3.0)
        out = model.converter('out')
        out.equation = sd.trend(model, inp, 2.0, 5.0)
        run_parity(model, ['out'], atol=1e-9)

    def test_trend_linear_input(self):
        model = Model(starttime=1, stoptime=10, dt=0.25, name='trend_linear_par')
        inp = model.converter('input')
        inp.equation = sd.time()
        out = model.converter('out')
        out.equation = sd.trend(model, inp, 1.0, 1.0)
        run_parity(model, ['out'], atol=1e-9)

    def test_trend_constant_input(self):
        """Constant input — trend should converge to zero."""
        model = Model(starttime=0, stoptime=10, dt=0.5, name='trend_const_par')
        inp = model.converter('input')
        inp.equation = 5.0
        out = model.converter('out')
        out.equation = sd.trend(model, inp, 1.0, 5.0)
        run_parity(model, ['out'], atol=1e-10)


class TestParityDelay:
    """sd.delay — memo lookback."""

    def test_delay_time_input(self):
        model = Model(starttime=0, stoptime=10, dt=1, name='delay_time_par')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = sd.time()
        b.equation = sd.delay(model, a, 3.0, 0.0)
        run_parity(model, ['a', 'b'], atol=1e-10)

    def test_delay_fractional_dt(self):
        model = Model(starttime=0, stoptime=8, dt=0.5, name='delay_frac_par')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = sd.time()
        b.equation = sd.delay(model, a, 2.0, -1.0)
        run_parity(model, ['a', 'b'], atol=1e-10)

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


# ---------------------------------------------------------------------------
# Test: feedback loops and the topological sort
#
# The engine evaluates non-stock entities eagerly, once per timestep, in an order
# computed by a topological sort at load time. Loops must therefore be broken by
# something that reads a *past* value: a stock (integrated in the previous step)
# or a `delay` (reads memo[step - delay_steps]). These tests pin down which
# shapes must load and which must stay rejected.
# ---------------------------------------------------------------------------

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
        """The shape that blocked Substep 4i: an ordering policy whose only time
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
        error names the equations that form it — Python itself can only offer a
        RecursionError, so this message is the only cycle diagnosis a model author gets.
        """
        model = Model(starttime=1, stoptime=5, dt=1, name='loop_algebraic_par')
        a = model.converter('a')
        b = model.converter('b')
        a.equation = b + 1.0
        b.equation = a * 2.0

        with pytest.raises(ValueError) as excinfo:
            RustSdEngine().load_model(model.to_json())
        assert str(excinfo.value) == \
            "Cyclic dependency among non-stock entities: a → b → a"

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

        with pytest.raises(ValueError) as excinfo:
            RustSdEngine().load_model(model.to_json())
        assert str(excinfo.value) == (
            "Cyclic dependency among non-stock entities: "
            "wholesaler.makingOrders → wholesaler.orderDecision → "
            "wholesaler.sendingOrders → wholesaler.makingOrders")

    def test_loop_closed_by_zero_duration_delay_is_rejected(self):
        """delay(x, 0) reads the *current* step, so it breaks no loop."""
        model = Model(starttime=1, stoptime=5, dt=1, name='loop_delay_zero_par')
        a = model.converter('a')
        d = model.converter('d')
        a.equation = d + 1.0
        d.equation = sd.delay(model, a, 0.0, 0.0)

        with pytest.raises(ValueError) as excinfo:
            RustSdEngine().load_model(model.to_json())
        assert str(excinfo.value) == \
            "Cyclic dependency among non-stock entities: a → d → a"
