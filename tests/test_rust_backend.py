"""Integration tests for the Rust execution backend via bptk.run_scenarios().

Tests that backend="rust" produces identical results to backend="python"
through the full BPTK scenario pipeline.
"""

import importlib
import os

import pytest
import pandas as pd
from pandas._testing import assert_frame_equal

from BPTK_Py import Model
import BPTK_Py
import BPTK_Py.logger.logger as logmod
from BPTK_Py.sddsl import functions as sd
from BPTK_Py.scenariorunners.sd_runner import SdRunner


# ---------------------------------------------------------------------------
# Model builders + fixtures
#
# The builder functions return fresh bptk instances on every call so the
# step-by-step interleaved parity tests (TestRunStepInterleavedParity below)
# can stand up two independent engines for Python and Rust. The fixtures wrap
# them for the existing run_scenarios / simulate / plot_scenarios tests, which
# only need one bptk instance per test.
# ---------------------------------------------------------------------------

def _build_simple_bptk():
    """Simple stock + flow + constant model with two scenarios."""
    model = Model(starttime=1, stoptime=10, dt=1, name="simple")

    stock = model.stock("stock")
    flow = model.flow("flow")
    constant = model.constant("constant")

    stock.initial_value = 0.0
    stock.equation = flow
    flow.equation = constant
    constant.equation = 1.0

    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({"mgr": {"model": model}})
    bptk.register_scenarios(
        scenarios={
            "base": {"constants": {"constant": 1.0}},
            "double": {"constants": {"constant": 2.0}},
        },
        scenario_manager="mgr",
    )
    return bptk


def _build_sir_bptk():
    """SIR epidemic model."""
    model = Model(starttime=0, stoptime=20, dt=0.25, name="SIR")

    susceptible = model.stock("susceptible")
    infected = model.stock("infected")
    recovered = model.stock("recovered")
    infection = model.flow("infection")
    recovery = model.flow("recovery")
    contact_rate = model.constant("contact_rate")
    transmission_prob = model.constant("transmission_prob")
    duration = model.constant("duration")

    susceptible.initial_value = 990.0
    infected.initial_value = 10.0
    recovered.initial_value = 0.0

    susceptible.equation = -infection
    infected.equation = infection - recovery
    recovered.equation = recovery

    infection.equation = contact_rate * transmission_prob * susceptible * infected
    recovery.equation = infected / duration

    contact_rate.equation = 10.0
    transmission_prob.equation = 0.001
    duration.equation = 5.0

    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({"sir_mgr": {"model": model}})
    bptk.register_scenarios(
        scenarios={
            "base": {},
            "high_contact": {"constants": {"contact_rate": 20.0}},
        },
        scenario_manager="sir_mgr",
    )
    return bptk


def _build_lookup_bptk():
    """Model with a graphical function (lookup table)."""
    model = Model(starttime=0, stoptime=10, dt=1, name="lookup_test")

    stock = model.stock("stock")
    flow = model.flow("flow")
    rate = model.converter("rate")

    stock.initial_value = 0.0
    stock.equation = flow
    flow.equation = rate
    model.points["rate_table"] = [[0, 1], [5, 5], [10, 2]]
    rate.equation = sd.lookup(sd.time(), "rate_table")

    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({"lookup_mgr": {"model": model}})
    bptk.register_scenarios(
        scenarios={
            "base": {},
            "new_table": {
                "points": {"rate_table": [[0, 10], [5, 10], [10, 10]]}
            },
        },
        scenario_manager="lookup_mgr",
    )
    return bptk


def _build_dotted_module_bptk():
    """Beergame-style Module-namespaced element names (`Retailer.inventory`).

    Two Module instances cross-reference each other (Wholesaler.outgoing reads
    Retailer.order) so the test exercises the dotted-name resolution path that
    Phase 4 Substep 4i's beergame integration depends on."""
    from BPTK_Py import Module
    model = Model(starttime=0, stoptime=5, dt=1, name="dotted_module")

    retailer = Module(model=model, name="Retailer")
    wholesaler = Module(model=model, name="Wholesaler")

    inv = retailer.stock("inventory")
    inc = retailer.flow("incoming")
    order = retailer.constant("order")
    inv.initial_value = 100.0
    inv.equation = inc
    inc.equation = order
    order.equation = 5.0

    w_inv = wholesaler.stock("inventory")
    w_out = wholesaler.flow("outgoing")
    w_inv.initial_value = 200.0
    w_inv.equation = -w_out
    w_out.equation = order

    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({"chain": {"model": model}})
    bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="chain")
    return bptk


@pytest.fixture
def simple_bptk():
    return _build_simple_bptk()


@pytest.fixture
def sir_bptk():
    return _build_sir_bptk()


@pytest.fixture
def lookup_bptk():
    return _build_lookup_bptk()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run_both(bptk, scenario_manager, scenarios, equations, return_format="df"):
    """Run scenarios on both backends and return (python_result, rust_result)."""
    # Reset model cache between runs to avoid stale state
    for _, mgr in bptk.scenario_manager_factory.scenario_managers.items():
        if hasattr(mgr, 'model') and mgr.model is not None:
            mgr.model.reset_cache()

    py = bptk.run_scenarios(
        scenario_managers=[scenario_manager],
        scenarios=scenarios,
        equations=equations,
        return_format=return_format,
        backend="python",
    )

    # Reset cache again before Rust run
    for _, mgr in bptk.scenario_manager_factory.scenario_managers.items():
        if hasattr(mgr, 'model') and mgr.model is not None:
            mgr.model.reset_cache()

    rust = bptk.run_scenarios(
        scenario_managers=[scenario_manager],
        scenarios=scenarios,
        equations=equations,
        return_format=return_format,
        backend="rust",
    )
    return py, rust


# ---------------------------------------------------------------------------
# Tests: basic pipeline parity
# ---------------------------------------------------------------------------

class TestSimpleModel:
    def test_df_results(self, simple_bptk):
        py, rust = _run_both(simple_bptk, "mgr", ["base"], ["stock", "flow"])
        assert_frame_equal(py, rust)

    def test_json_results(self, simple_bptk):
        py, rust = _run_both(simple_bptk, "mgr", ["base"], ["stock", "flow"], return_format="json")
        assert py == rust

    def test_dict_results(self, simple_bptk):
        py, rust = _run_both(simple_bptk, "mgr", ["base"], ["stock", "flow"], return_format="dict")
        # dict format contains nested dicts with pd.Series — compare via DataFrame
        py_df = pd.DataFrame(py["mgr"]["base"]["equations"])
        rust_df = pd.DataFrame(rust["mgr"]["base"]["equations"])
        assert_frame_equal(py_df, rust_df)

    def test_constant_override(self, simple_bptk):
        """Scenario 'double' overrides constant to 2.0 — stock should grow twice as fast."""
        py, rust = _run_both(simple_bptk, "mgr", ["double"], ["stock", "flow"])
        assert_frame_equal(py, rust)

    def test_multiple_scenarios(self, simple_bptk):
        """Run both scenarios at once — results should match."""
        py, rust = _run_both(simple_bptk, "mgr", ["base", "double"], ["stock"])
        assert_frame_equal(py, rust)


# ---------------------------------------------------------------------------
# Tests: SIR model
# ---------------------------------------------------------------------------

class TestSIRModel:
    def test_sir_base(self, sir_bptk):
        py, rust = _run_both(
            sir_bptk, "sir_mgr", ["base"],
            ["susceptible", "infected", "recovered"]
        )
        assert_frame_equal(py, rust, atol=1e-6)

    def test_sir_constant_override(self, sir_bptk):
        py, rust = _run_both(
            sir_bptk, "sir_mgr", ["high_contact"],
            ["susceptible", "infected", "recovered"]
        )
        assert_frame_equal(py, rust, atol=1e-6)


# ---------------------------------------------------------------------------
# Tests: lookup / points override
# ---------------------------------------------------------------------------

class TestLookupModel:
    def test_lookup_base(self, lookup_bptk):
        py, rust = _run_both(lookup_bptk, "lookup_mgr", ["base"], ["stock", "rate"])
        assert_frame_equal(py, rust)

    def test_points_override(self, lookup_bptk):
        py, rust = _run_both(lookup_bptk, "lookup_mgr", ["new_table"], ["stock", "rate"])
        assert_frame_equal(py, rust)


# ---------------------------------------------------------------------------
# Tests: inline lookup points
# ---------------------------------------------------------------------------

class TestInlineLookupParity:
    def test_inline_lookup_parity(self):
        model = Model(starttime=0, stoptime=10, dt=0.5, name="inline_lookup")
        input_val = model.converter("input_val")
        input_val.equation = sd.time() * 0.5
        output = model.converter("output")
        output.equation = sd.lookup(input_val, [(0, 0), (1, 2), (2, 6), (3, 4), (5, 10)])

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["input_val", "output"])
        assert_frame_equal(py, rust)

    def test_inline_lookup_boundary_parity(self):
        model = Model(starttime=0, stoptime=10, dt=1, name="inline_boundary")
        input_val = model.converter("input_val")
        input_val.equation = sd.time() - 2.0
        output = model.converter("output")
        output.equation = sd.lookup(input_val, [(0, 0), (5, 10)])

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["input_val", "output"])
        assert_frame_equal(py, rust)

    def test_mixed_inline_and_named_lookup_parity(self):
        model = Model(starttime=0, stoptime=10, dt=0.5, name="mixed_lookup")
        input_val = model.converter("input_val")
        input_val.equation = sd.time() * 0.5

        model.points["named_table"] = [[0, 0], [2, 4], [5, 10]]
        named_out = model.converter("named_out")
        named_out.equation = sd.lookup(input_val, "named_table")

        inline_out = model.converter("inline_out")
        inline_out.equation = sd.lookup(input_val, [(0, 1), (2, 5), (5, 8)])

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["input_val", "named_out", "inline_out"])
        assert_frame_equal(py, rust)


# ---------------------------------------------------------------------------
# Tests: runspec overrides
# ---------------------------------------------------------------------------

class TestRunspecOverrides:
    def test_fractional_dt(self):
        model = Model(starttime=0, stoptime=4, dt=0.25, name="frac_dt")
        stock = model.stock("stock")
        flow = model.flow("flow")
        stock.initial_value = 0.0
        stock.equation = flow
        flow.equation = 10.0

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["stock"])
        assert_frame_equal(py, rust)

    def test_non_zero_starttime(self):
        model = Model(starttime=5, stoptime=10, dt=1, name="nonzero_start")
        stock = model.stock("stock")
        flow = model.flow("flow")
        stock.initial_value = 100.0
        stock.equation = flow
        flow.equation = 5.0

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["stock"])
        assert_frame_equal(py, rust)

    def test_runspec_override_in_scenario(self):
        model = Model(starttime=0, stoptime=10, dt=1, name="runspec_override")
        stock = model.stock("stock")
        flow = model.flow("flow")
        stock.initial_value = 0.0
        stock.equation = flow
        flow.equation = 1.0

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(
            scenarios={"short": {"runspecs": {"stoptime": 5}}},
            scenario_manager="mgr",
        )

        py, rust = _run_both(bptk, "mgr", ["short"], ["stock"])
        assert_frame_equal(py, rust)


# ---------------------------------------------------------------------------
# Tests: Model.simulate() direct API
# ---------------------------------------------------------------------------

class TestModelSimulate:
    def test_simulate_rust(self):
        model = Model(starttime=0, stoptime=5, dt=1, name="direct")
        stock = model.stock("stock")
        flow = model.flow("flow")
        stock.initial_value = 100.0
        stock.equation = flow
        flow.equation = 10.0

        result = model.simulate(["stock", "flow"], backend="rust")
        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "t"
        assert set(result.columns) == {"stock", "flow"}
        assert result.loc[0.0, "stock"] == 100.0
        assert result.loc[5.0, "stock"] == 150.0

    def test_simulate_python(self):
        model = Model(starttime=0, stoptime=5, dt=1, name="direct")
        stock = model.stock("stock")
        flow = model.flow("flow")
        stock.initial_value = 100.0
        stock.equation = flow
        flow.equation = 10.0

        result = model.simulate(["stock", "flow"], backend="python")
        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "t"
        assert result.loc[0.0, "stock"] == 100.0
        assert result.loc[5.0, "stock"] == 150.0

    def test_simulate_parity(self):
        model = Model(starttime=0, stoptime=10, dt=1, name="parity")

        s = model.stock("s")
        f = model.flow("f")
        c = model.constant("c")
        s.initial_value = 0.0
        s.equation = f
        f.equation = c
        c.equation = 3.0

        py = model.simulate(["s", "f"], backend="python")
        model.reset_cache()
        rust = model.simulate(["s", "f"], backend="rust")
        # Ensure same column order before comparison (Rust HashMap is unordered)
        assert_frame_equal(py[sorted(py.columns)], rust[sorted(rust.columns)])


# ---------------------------------------------------------------------------
# Tests: Smooth model
# ---------------------------------------------------------------------------

class TestSmoothModel:
    @pytest.fixture
    def smooth_bptk(self):
        """Model using sd.smooth() — smooths a step input."""
        model = Model(starttime=1, stoptime=10, dt=0.1, name="smooth_test")

        input_fn = model.converter("input_function")
        input_fn.equation = sd.step(10.0, 3.0)

        smooth_out = model.converter("smooth_out")
        smooth_out.equation = sd.smooth(model, input_fn, 1.0, 0.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"smooth_mgr": {"model": model}})
        bptk.register_scenarios(
            scenarios={"base": {}},
            scenario_manager="smooth_mgr",
        )
        return bptk

    def test_smooth_parity(self, smooth_bptk):
        py, rust = _run_both(smooth_bptk, "smooth_mgr", ["base"], ["smooth_out"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_smooth_ramp_input(self):
        """Smooth of a ramp (time()) — smooth lags behind the input."""
        model = Model(starttime=0, stoptime=10, dt=0.25, name="smooth_ramp")
        input_fn = model.converter("input_function")
        input_fn.equation = sd.time()
        smooth_out = model.converter("smooth_out")
        smooth_out.equation = sd.smooth(model, input_fn, 2.0, 0.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["smooth_out"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_smooth_constant_input(self):
        """Smooth of a constant with matching initial value — output stays constant."""
        model = Model(starttime=0, stoptime=5, dt=0.5, name="smooth_const")
        input_fn = model.converter("input_function")
        input_fn.equation = 42.0
        smooth_out = model.converter("smooth_out")
        smooth_out.equation = sd.smooth(model, input_fn, 1.0, 42.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["smooth_out"])
        assert_frame_equal(py, rust, atol=1e-10)

    def test_smooth_large_averaging_time(self):
        """Smooth with large averaging time — output changes very slowly."""
        model = Model(starttime=0, stoptime=20, dt=0.5, name="smooth_slow")
        input_fn = model.converter("input_function")
        input_fn.equation = sd.step(100.0, 5.0)
        smooth_out = model.converter("smooth_out")
        smooth_out.equation = sd.smooth(model, input_fn, 10.0, 0.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["smooth_out"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_smooth_small_dt(self):
        """Smooth with very small dt — precision test."""
        model = Model(starttime=0, stoptime=5, dt=0.01, name="smooth_precise")
        input_fn = model.converter("input_function")
        input_fn.equation = sd.step(1.0, 1.0)
        smooth_out = model.converter("smooth_out")
        smooth_out.equation = sd.smooth(model, input_fn, 0.5, 0.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["smooth_out"])
        assert_frame_equal(py, rust, atol=1e-6)


# ---------------------------------------------------------------------------
# Tests: Trend model
# ---------------------------------------------------------------------------

class TestTrendModel:
    @pytest.fixture
    def trend_bptk(self):
        """Model using sd.trend() — computes fractional rate of change."""
        model = Model(starttime=1, stoptime=10, dt=0.1, name="trend_test")

        input_fn = model.converter("input_function")
        input_fn.equation = sd.step(10.0, 3.0)

        trend_out = model.converter("trend_out")
        trend_out.equation = sd.trend(model, input_fn, 2.0, 5.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"trend_mgr": {"model": model}})
        bptk.register_scenarios(
            scenarios={"base": {}},
            scenario_manager="trend_mgr",
        )
        return bptk

    def test_trend_parity(self, trend_bptk):
        py, rust = _run_both(trend_bptk, "trend_mgr", ["base"], ["trend_out"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_trend_linear_input(self):
        """Trend of linear input (time()) — should converge to a positive fractional rate."""
        model = Model(starttime=1, stoptime=10, dt=0.25, name="trend_linear")
        input_fn = model.converter("input_function")
        input_fn.equation = sd.time()
        trend_out = model.converter("trend_out")
        trend_out.equation = sd.trend(model, input_fn, 1.0, 1.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["trend_out"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_trend_constant_input(self):
        """Trend of constant input — trend should approach zero."""
        model = Model(starttime=0, stoptime=10, dt=0.1, name="trend_const")
        input_fn = model.converter("input_function")
        input_fn.equation = 5.0
        trend_out = model.converter("trend_out")
        trend_out.equation = sd.trend(model, input_fn, 1.0, 5.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["trend_out"])
        assert_frame_equal(py, rust, atol=1e-10)

    def test_trend_large_averaging_time(self):
        """Trend with large averaging time — slow response to changes."""
        model = Model(starttime=0, stoptime=20, dt=0.5, name="trend_slow")
        input_fn = model.converter("input_function")
        input_fn.equation = sd.step(10.0, 5.0)
        trend_out = model.converter("trend_out")
        trend_out.equation = sd.trend(model, input_fn, 8.0, 5.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["trend_out"])
        assert_frame_equal(py, rust, atol=1e-6)


# ---------------------------------------------------------------------------
# Tests: Delay model
# ---------------------------------------------------------------------------

class TestDelayModel:
    @pytest.fixture
    def delay_bptk(self):
        """Model using sd.delay() — lookback in memo table."""
        model = Model(starttime=0, stoptime=10, dt=1, name="delay_test")

        a = model.converter("a")
        b = model.converter("b")
        a.equation = sd.time()
        b.equation = sd.delay(model, a, 3.0, 0.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"delay_mgr": {"model": model}})
        bptk.register_scenarios(
            scenarios={"base": {}},
            scenario_manager="delay_mgr",
        )
        return bptk

    def test_delay_parity(self, delay_bptk):
        py, rust = _run_both(delay_bptk, "delay_mgr", ["base"], ["a", "b"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_delay_before_duration(self, delay_bptk):
        """Before delay_duration elapses, initial_value (0.0) is returned."""
        rust = delay_bptk.run_scenarios(
            scenario_managers=["delay_mgr"],
            scenarios=["base"],
            equations=["b"],
            backend="rust",
        )
        # At t=0,1,2: step < delay_steps(3), so b should be 0.0
        assert rust.iloc[0]["b"] == 0.0
        assert rust.iloc[1]["b"] == 0.0
        assert rust.iloc[2]["b"] == 0.0

    def test_delay_after_duration(self, delay_bptk):
        """After delay_duration, b = a(t - delay). a=time(), delay=3, so b(t) = t-3."""
        rust = delay_bptk.run_scenarios(
            scenario_managers=["delay_mgr"],
            scenarios=["base"],
            equations=["b"],
            backend="rust",
        )
        # At t=3: b = a(0) = 0.0
        # At t=4: b = a(1) = 1.0
        # At t=5: b = a(2) = 2.0
        assert rust.iloc[3]["b"] == 0.0
        assert rust.iloc[4]["b"] == 1.0
        assert rust.iloc[5]["b"] == 2.0

    def test_delay_fractional_dt(self):
        """Delay with fractional dt — lookback is duration/dt steps."""
        model = Model(starttime=0, stoptime=8, dt=0.5, name="delay_frac")
        a = model.converter("a")
        b = model.converter("b")
        a.equation = sd.time()
        b.equation = sd.delay(model, a, 2.0, -1.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["a", "b"])
        assert_frame_equal(py, rust, atol=1e-10)

    def test_delay_step_input(self):
        """Delay of a step function — step appears shifted in time."""
        model = Model(starttime=0, stoptime=10, dt=0.5, name="delay_step")
        input_fn = model.converter("input")
        delayed = model.converter("delayed")
        input_fn.equation = sd.step(5.0, 3.0)
        delayed.equation = sd.delay(model, input_fn, 2.0, 0.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["delayed"])
        assert_frame_equal(py, rust, atol=1e-10)

    def test_delay_with_stock(self):
        """Delay reading from a stock — interaction with Euler integration."""
        model = Model(starttime=0, stoptime=10, dt=1, name="delay_stock")
        level = model.stock("level")
        inflow = model.flow("inflow")
        delayed_level = model.converter("delayed_level")
        level.initial_value = 0.0
        level.equation = inflow
        inflow.equation = 5.0
        delayed_level.equation = sd.delay(model, level, 3.0, 0.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["level", "delayed_level"])
        assert_frame_equal(py, rust, atol=1e-10)

    def test_delay_zero_duration(self):
        """Delay with duration=0 — should return current value."""
        model = Model(starttime=0, stoptime=5, dt=1, name="delay_zero")
        a = model.converter("a")
        b = model.converter("b")
        a.equation = sd.time()
        b.equation = sd.delay(model, a, 0.0, 0.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["a", "b"])
        assert_frame_equal(py, rust, atol=1e-10)


# ---------------------------------------------------------------------------
# Tests: biflow support
# ---------------------------------------------------------------------------

class TestBiflowModel:
    """Tests that biflows work correctly in the Rust engine."""

    @pytest.fixture
    def biflow_bptk(self):
        """Oscillator model using biflows — velocity goes negative."""
        model = Model(starttime=0, stoptime=10, dt=0.1, name="biflow_test")
        position = model.stock("position")
        velocity = model.biflow("velocity")
        position.initial_value = 10.0
        position.equation = velocity
        velocity.equation = -position  # Goes negative — biflow allows this

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
        return bptk

    def test_biflow_parity(self, biflow_bptk):
        """Rust backend produces same results as Python for biflow model."""
        py = biflow_bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["position", "velocity"], backend="python",
        )
        rust = biflow_bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["position", "velocity"], backend="rust",
        )
        assert_frame_equal(py, rust, atol=1e-10)

    def test_biflow_goes_negative(self, biflow_bptk):
        """Biflow values go negative — not clamped like regular flows."""
        rust = biflow_bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["velocity"], backend="rust",
        )
        # velocity = -position, and position starts at 10 and oscillates
        # velocity must go negative at some point
        assert (rust.values < 0).any(), "Biflow values should go negative"

    def test_biflow_constant_negative(self):
        """Biflow with constant negative equation — stock decreases."""
        model = Model(starttime=0, stoptime=5, dt=1, name="biflow_const_neg")
        stock = model.stock("stock")
        bf = model.biflow("bf")
        stock.initial_value = 100.0
        stock.equation = bf
        bf.equation = -10.0

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["stock", "bf"])
        assert_frame_equal(py, rust, atol=1e-10)

    def test_biflow_vs_flow_clamping(self):
        """Same negative equation — flow clamps to 0, biflow doesn't."""
        model = Model(starttime=0, stoptime=3, dt=1, name="flow_vs_biflow")
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

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"],
                             ["stock_flow", "stock_biflow", "regular_flow", "bi_flow"])
        assert_frame_equal(py, rust, atol=1e-10, check_dtype=False)

    def test_biflow_spring_mass_oscillator(self):
        """Two-stock spring-mass system — classic biflow use case with small dt."""
        model = Model(starttime=0, stoptime=10, dt=0.01, name="spring_mass")
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

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["position", "velocity"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_biflow_simulate_api(self):
        """Biflow works through model.simulate() API too."""
        model = Model(starttime=0, stoptime=5, dt=0.5, name="biflow_simulate")
        stock = model.stock("stock")
        bf = model.biflow("bf")
        stock.initial_value = 50.0
        stock.equation = bf
        bf.equation = -5.0

        py = model.simulate(["stock", "bf"], backend="python")
        model.reset_cache()
        rust = model.simulate(["stock", "bf"], backend="rust")
        assert_frame_equal(
            py[sorted(py.columns)], rust[sorted(rust.columns)], atol=1e-10
        )


# ---------------------------------------------------------------------------
# Tests: fallback behaviour
# ---------------------------------------------------------------------------

@pytest.mark.allow_rust_fallback
class TestFallback:
    """Tests that models with unsupported features fall back to Python and log [WARN]."""

    @pytest.fixture
    def unsupported_model(self):
        """Model using custom NaryOperator function — not supported by Rust engine."""
        model = Model(starttime=0, stoptime=10, dt=1, name="nary_fallback")
        stock = model.stock("stock")
        flow = model.flow("flow")
        stock.initial_value = 100.0
        stock.equation = flow
        # Register a custom function that works in Python but can't be serialized to JSON
        my_fn = model.function("my_custom_fn", lambda model, t, *args: 5.0)
        flow.equation = my_fn(model.stock("stock"))
        return model

    def _cleanup_logfile(self):
        """Reload logger module and clear the logfile."""
        importlib.reload(logmod)
        logmod.logfire_enabled = False
        logmod.loglevel = "WARN"
        with open(logmod.logfile, "w", encoding="UTF-8") as f:
            pass

    def _read_logfile(self):
        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            return f.read()

    def test_fallback_run_scenarios(self, unsupported_model):
        """run_scenarios(backend='rust') falls back to Python and logs [WARN]."""
        self._cleanup_logfile()

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": unsupported_model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        result = bptk.run_scenarios(
            scenario_managers=["mgr"],
            scenarios=["base"],
            equations=["stock"],
            backend="rust",
        )
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

        content = self._read_logfile()
        assert "[WARN]" in content
        assert "falling back" in content.lower()

    def test_fallback_simulate(self, unsupported_model):
        """model.simulate(backend='rust') falls back to Python and logs [WARN]."""
        self._cleanup_logfile()

        result = unsupported_model.simulate(["stock"], backend="rust")
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

        content = self._read_logfile()
        assert "[WARN]" in content
        assert "falling back" in content.lower()

    @pytest.mark.requires_extra("plotting")
    def test_fallback_plot_scenarios(self, unsupported_model):
        """plot_scenarios(backend='rust') falls back to Python and still produces output."""
        import matplotlib
        matplotlib.use("Agg")

        self._cleanup_logfile()

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": unsupported_model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        bptk.plot_scenarios(
            scenario_managers=["mgr"],
            scenarios=["base"],
            equations=["stock"],
            backend="rust",
        )

        content = self._read_logfile()
        assert "[WARN]" in content
        assert "falling back" in content.lower()

    def test_fallback_step(self, unsupported_model):
        """begin_session(backend='rust') + run_step on a model that can't be
        JSON-serialised must transparently fall back to the Python step path
        for the rest of the session, with a [WARN] log line."""
        self._cleanup_logfile()

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": unsupported_model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust_history = _run_session_history(bptk, ["mgr"], ["base"],
                                            ["stock", "flow"], steps=6, backend="rust")

        # Compare against a clean Python-only session on a freshly-built model
        # (the unsupported_model fixture is shared, so we rebuild equivalent state).
        py_model = Model(starttime=0, stoptime=10, dt=1, name="nary_py")
        s = py_model.stock("stock")
        f = py_model.flow("flow")
        s.initial_value = 100.0
        s.equation = f
        my_fn = py_model.function("my_custom_fn", lambda model, t, *args: 5.0)
        f.equation = my_fn(py_model.stock("stock"))
        py_bptk = BPTK_Py.bptk()
        py_bptk.register_scenario_manager({"mgr": {"model": py_model}})
        py_bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
        py_history = _run_session_history(py_bptk, ["mgr"], ["base"],
                                          ["stock", "flow"], steps=6, backend="python")

        for i, (p, r) in enumerate(zip(py_history, rust_history)):
            _assert_step_dicts_equal(p, r, i)

        content = self._read_logfile()
        assert "[WARN]" in content
        assert "falling back" in content.lower()

    def test_fallback_non_numeric_constant(self):
        """Non-numeric constant override triggers fallback to Python."""
        self._cleanup_logfile()

        model = Model(starttime=0, stoptime=5, dt=1, name="non_numeric_const")
        stock = model.stock("stock")
        flow = model.flow("flow")
        constant = model.constant("constant")
        stock.initial_value = 0.0
        stock.equation = flow
        flow.equation = constant
        constant.equation = 1.0

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(
            scenarios={"base": {"constants": {"constant": "not_a_number"}}},
            scenario_manager="mgr",
        )

        result = bptk.run_scenarios(
            scenario_managers=["mgr"],
            scenarios=["base"],
            equations=["stock"],
            backend="rust",
        )
        assert result is not None
        assert isinstance(result, pd.DataFrame)

        content = self._read_logfile()
        assert "Non-numeric constant" in content

    def test_fallback_engine_raises_after_load(self, monkeypatch):
        """ValueError raised by the Rust engine after load_model() is caught and triggers fallback."""
        self._cleanup_logfile()

        model = Model(starttime=0, stoptime=3, dt=1, name="rust_runtime_error")
        stock = model.stock("stock")
        flow = model.flow("flow")
        constant = model.constant("constant")
        stock.initial_value = 0.0
        stock.equation = flow
        flow.equation = constant
        constant.equation = 1.0

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        # Make the Rust engine's simulate() blow up so that the inner
        # try/except in _run_scenario_rust catches it (sd_runner.py:282-284).
        import BPTK_Py._rust_engine as rust_engine_mod

        original_load = rust_engine_mod.RustSdEngine.load_model

        def patched_load(self, json_str):
            wrapped = original_load(self, json_str)

            class _RaisingProxy:
                def __init__(self, inner):
                    self._inner = inner

                def set_constant(self, *a, **kw):
                    return self._inner.set_constant(*a, **kw)

                def set_points(self, *a, **kw):
                    return self._inner.set_points(*a, **kw)

                def set_runspecs(self, *a, **kw):
                    return self._inner.set_runspecs(*a, **kw)

                def simulate(self, *a, **kw):
                    raise ValueError("simulated runtime failure")

            return _RaisingProxy(wrapped)

        monkeypatch.setattr(rust_engine_mod.RustSdEngine, "load_model", patched_load)

        result = bptk.run_scenarios(
            scenario_managers=["mgr"],
            scenarios=["base"],
            equations=["stock"],
            backend="rust",
        )
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

        content = self._read_logfile()
        assert "Rust engine failed" in content
        assert "simulated runtime failure" in content
        assert "falling back" in content.lower()



# ---------------------------------------------------------------------------
# Tests: multiple scenario managers
# ---------------------------------------------------------------------------

class TestMultipleManagers:
    def test_two_managers(self):
        model = Model(starttime=0, stoptime=5, dt=1, name="multi")
        stock = model.stock("stock")
        flow = model.flow("flow")
        c = model.constant("c")
        stock.initial_value = 0.0
        stock.equation = flow
        flow.equation = c
        c.equation = 1.0

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr1": {"model": model}})
        bptk.register_scenarios(
            scenarios={"base": {"constants": {"c": 1.0}}},
            scenario_manager="mgr1",
        )
        bptk.register_scenario_manager({"mgr2": {"model": model}})
        bptk.register_scenarios(
            scenarios={"base": {"constants": {"c": 2.0}}},
            scenario_manager="mgr2",
        )

        py = bptk.run_scenarios(
            scenario_managers=["mgr1", "mgr2"],
            scenarios=["base"],
            equations=["stock"],
            backend="python",
        )
        # Reset cache
        for _, mgr in bptk.scenario_manager_factory.scenario_managers.items():
            if hasattr(mgr, 'model') and mgr.model is not None:
                mgr.model.reset_cache()

        rust = bptk.run_scenarios(
            scenario_managers=["mgr1", "mgr2"],
            scenarios=["base"],
            equations=["stock"],
            backend="rust",
        )
        assert_frame_equal(py, rust)


# ---------------------------------------------------------------------------
# ln, log10, floor, ceil — full pipeline parity
# ---------------------------------------------------------------------------

@pytest.fixture
def ln_log10_bptk():
    """Model using ln and log10 functions."""
    model = Model(starttime=1, stoptime=10, dt=1, name="ln_log10")
    inp = model.converter("input")
    inp.equation = sd.time()
    fn_ln = model.converter("fn_ln")
    fn_ln.equation = sd.ln(inp)
    fn_log10 = model.converter("fn_log10")
    fn_log10.equation = sd.log10(inp)

    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({"mgr": {"model": model}})
    bptk.register_scenarios(
        scenarios={"base": {}},
        scenario_manager="mgr",
    )
    return bptk


@pytest.fixture
def floor_ceil_bptk():
    """Model using floor and ceil functions."""
    model = Model(starttime=0, stoptime=10, dt=1, name="floor_ceil")
    inp = model.converter("input")
    inp.equation = sd.time() * 1.7 - 3.0
    fn_floor = model.converter("fn_floor")
    fn_floor.equation = sd.floor(inp)
    fn_ceil = model.converter("fn_ceil")
    fn_ceil.equation = sd.ceil(inp)

    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({"mgr": {"model": model}})
    bptk.register_scenarios(
        scenarios={"base": {}},
        scenario_manager="mgr",
    )
    return bptk


class TestLnLog10FloorCeilParity:
    """Full pipeline parity for ln, log10, floor, ceil."""

    def test_ln_log10_parity(self, ln_log10_bptk):
        py = ln_log10_bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["fn_ln", "fn_log10"], backend="python",
        )
        for _, mgr in ln_log10_bptk.scenario_manager_factory.scenario_managers.items():
            if hasattr(mgr, 'model') and mgr.model is not None:
                mgr.model.reset_cache()
        rust = ln_log10_bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["fn_ln", "fn_log10"], backend="rust",
        )
        assert_frame_equal(py, rust, atol=1e-10)

    def test_floor_ceil_parity(self, floor_ceil_bptk):
        py = floor_ceil_bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["fn_floor", "fn_ceil"], backend="python",
        )
        for _, mgr in floor_ceil_bptk.scenario_manager_factory.scenario_managers.items():
            if hasattr(mgr, 'model') and mgr.model is not None:
                mgr.model.reset_cache()
        rust = floor_ceil_bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["fn_floor", "fn_ceil"], backend="rust",
        )
        assert_frame_equal(py, rust, atol=1e-10)


# ---------------------------------------------------------------------------
# Tests: Combinatorial & special functions
# ---------------------------------------------------------------------------

class TestCombinatorialFunctions:
    def test_factorial(self):
        model = Model(starttime=0, stoptime=5, dt=1, name="factorial")
        x = model.converter("x")
        x.equation = sd.factorial(sd.time())

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["x"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_combinations(self):
        model = Model(starttime=0, stoptime=1, dt=1, name="combinations")
        x = model.converter("x")
        x.equation = sd.combinations(10, 3)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["x"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_permutations(self):
        model = Model(starttime=0, stoptime=1, dt=1, name="permutations")
        x = model.converter("x")
        x.equation = sd.permutations(5, 2)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["x"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_factorial_negative(self):
        """factorial(-5) should return 0 for negative input."""
        model = Model(starttime=0, stoptime=1, dt=1, name="factorial_neg")
        x = model.converter("x")
        x.equation = sd.factorial(-5)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["x"])
        assert_frame_equal(py, rust, atol=1e-6)
        assert (py["x"] == 0.0).all()

    def test_combinations_n_less_than_r(self):
        """combinations(2, 5) should return 0 when n < r."""
        model = Model(starttime=0, stoptime=1, dt=1, name="comb_n_lt_r")
        x = model.converter("x")
        x.equation = sd.combinations(2, 5)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["x"])
        assert_frame_equal(py, rust, atol=1e-6)
        assert (py["x"] == 0.0).all()

    def test_permutations_n_less_than_r(self):
        """permutations(2, 5) should return 0 when n < r."""
        model = Model(starttime=0, stoptime=1, dt=1, name="perm_n_lt_r")
        x = model.converter("x")
        x.equation = sd.permutations(2, 5)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["x"])
        assert_frame_equal(py, rust, atol=1e-6)
        assert (py["x"] == 0.0).all()

    def test_gammaln(self):
        model = Model(starttime=1, stoptime=5, dt=1, name="gammaln")
        x = model.converter("x")
        x.equation = sd.gammaln(sd.time())

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["x"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_round_with_digits(self):
        model = Model(starttime=0, stoptime=1, dt=1, name="round_digits")
        x = model.converter("x")
        x.equation = sd.round(3.14159, 2)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["x"])
        assert_frame_equal(py, rust, atol=1e-10)


# ---------------------------------------------------------------------------
# Tests: Inf and Nan
# ---------------------------------------------------------------------------

class TestInfNan:
    def test_inf_parity(self):
        model = Model(starttime=0, stoptime=5, dt=1, name="inf_backend")
        t_val = model.converter("t_val")
        t_val.equation = sd.time()
        x = model.converter("x")
        x.equation = sd.min(t_val, sd.Inf())

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["t_val", "x"])
        assert_frame_equal(py, rust, atol=1e-10)

    def test_nan_produces_nan(self):
        """NaN values should appear in both backends."""
        import math
        model = Model(starttime=0, stoptime=1, dt=1, name="nan_backend")
        x = model.converter("x")
        x.equation = sd.nan()

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["x"])
        # Both DataFrames should have NaN values
        assert py.isna().all().all(), "Python backend should produce NaN"
        assert rust.isna().all().all(), "Rust backend should produce NaN"


# ---------------------------------------------------------------------------
# Tests: Statistical functions
# ---------------------------------------------------------------------------

class TestStochasticFunctions:
    """Tests that stochastic functions produce valid output via Rust backend."""

    def test_uniform_in_range(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="uniform")
        x = model.converter("x")
        x.equation = sd.random(0, 1)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 0).all().all(), "Uniform values should be >= 0"
        assert (rust <= 1).all().all(), "Uniform values should be <= 1"

    def test_normal_produces_valid_output(self):
        model = Model(starttime=0, stoptime=1000, dt=1, name="normal")
        x = model.converter("x")
        x.equation = sd.normal(100, 10)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        mean = rust.values.mean()
        assert 80 < mean < 120, f"Normal mean should be ~100, got {mean}"

    def test_montecarlo_produces_binary(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="mc")
        x = model.converter("x")
        x.equation = sd.montecarlo(50)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        values = rust.values.flatten()
        assert all(v in (0.0, 1.0) for v in values), "Montecarlo should produce only 0 or 1"

    def test_invnorm_parity(self):
        """Deterministic: exact comparison Python vs Rust."""
        model = Model(starttime=0, stoptime=1, dt=1, name="invnorm")
        x = model.converter("x")
        x.equation = sd.invnorm(0.975, 0, 1)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["x"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_normalcdf_parity(self):
        """Deterministic: exact comparison Python vs Rust."""
        model = Model(starttime=0, stoptime=1, dt=1, name="normalcdf")
        x = model.converter("x")
        x.equation = sd.normalcdf(-1, 1, 0, 1)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        py, rust = _run_both(bptk, "mgr", ["base"], ["x"])
        assert_frame_equal(py, rust, atol=1e-6)

    def test_poisson_non_negative(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="poisson")
        x = model.converter("x")
        x.equation = sd.poisson(5)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 0).all().all(), "Poisson values should be non-negative"

    def test_beta_in_range(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="beta")
        x = model.converter("x")
        x.equation = sd.beta(2, 5)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 0).all().all(), "Beta values should be >= 0"
        assert (rust <= 1).all().all(), "Beta values should be <= 1"

    def test_binomial_non_negative(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="binomial")
        x = model.converter("x")
        x.equation = sd.binomial(10, 0.5)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 0).all().all(), "Binomial values should be >= 0"
        assert (rust <= 10).all().all(), "Binomial values should be <= n"

    def test_exprnd_positive(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="exprnd")
        x = model.converter("x")
        x.equation = sd.exprnd(5)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 0).all().all(), "Exponential values should be >= 0"

    def test_gamma_positive(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="gamma_test")
        x = model.converter("x")
        x.equation = sd.gamma(2, 3)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 0).all().all(), "Gamma values should be >= 0"

    def test_geometric_positive(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="geometric")
        x = model.converter("x")
        x.equation = sd.geometric(0.3)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 0).all().all(), "Geometric values should be >= 0"

    def test_lognormal_positive(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="lognormal")
        x = model.converter("x")
        x.equation = sd.lognormal(0, 1)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 0).all().all(), "Lognormal values should be >= 0"

    def test_logistic_produces_output(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="logistic")
        x = model.converter("x")
        x.equation = sd.logistic(0, 1)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert rust is not None
        assert len(rust) > 0

    def test_triangular_in_range(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="triangular")
        x = model.converter("x")
        x.equation = sd.triangular(1, 5, 10)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 1).all().all(), "Triangular values should be >= lower"
        assert (rust <= 10).all().all(), "Triangular values should be <= upper"

    def test_weibull_positive(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="weibull")
        x = model.converter("x")
        x.equation = sd.weibull(2, 5)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 0).all().all(), "Weibull values should be >= 0"

    def test_pareto_positive(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="pareto")
        x = model.converter("x")
        x.equation = sd.pareto(3, 1)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 0).all().all(), "Pareto values should be >= 0"

    def test_negbinomial_non_negative(self):
        model = Model(starttime=0, stoptime=100, dt=1, name="negbinomial")
        x = model.converter("x")
        x.equation = sd.negbinomial(5, 0.4)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 0).all().all(), "NegBinomial values should be >= 0"

    def test_negbinomial_non_negative_integer(self):
        model = Model(starttime=0, stoptime=1000, dt=1, name="negbinomial")
        x = model.converter("x")
        x.equation = sd.negbinomial(5, 0.4)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust >= 0).all().all(), "NegBinomial values should be >= 0"
        # Values should be integers (number of failures before n successes)
        assert (rust == rust.map(lambda v: float(int(v)))).all().all(), \
            "NegBinomial values should be integers"
        # Expected mean of negbinomial(n=5, p=0.4) = n*(1-p)/p = 7.5
        mean = rust.values.mean()
        assert 3.0 < mean < 15.0, f"NegBinomial mean {mean} out of expected range"

    def test_negbinomial_p_zero(self):
        """p=0 means success is impossible → infinite failures."""
        model = Model(starttime=0, stoptime=5, dt=1, name="negbinom_p0")
        x = model.converter("x")
        x.equation = sd.negbinomial(5, 0.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        import numpy as np
        assert (rust.map(lambda v: np.isinf(v))).all().all(), \
            "NegBinomial with p=0 should return inf"

    def test_negbinomial_p_one(self):
        """p=1 means every trial succeeds → zero failures."""
        model = Model(starttime=0, stoptime=5, dt=1, name="negbinom_p1")
        x = model.converter("x")
        x.equation = sd.negbinomial(5, 1.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert (rust == 0.0).all().all(), \
            "NegBinomial with p=1 should return 0"


# ---------------------------------------------------------------------------
# Stochastic function guards — invalid params should return NaN
# ---------------------------------------------------------------------------

class TestStochasticGuards:
    """Invalid parameters return NaN via Rust backend."""

    def _run_nan_check(self, equation, name):
        import numpy as np
        model = Model(starttime=0, stoptime=1, dt=1, name=name)
        x = model.converter("x")
        x.equation = equation

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")

        rust = bptk.run_scenarios(
            scenario_managers=["mgr"], scenarios=["base"],
            equations=["x"], backend="rust",
        )
        assert rust.map(lambda v: np.isnan(v)).all().all(), \
            f"{name}: expected all NaN, got {rust.values}"

    def test_normal_negative_stddev(self):
        self._run_nan_check(sd.normal(0, -1), "normal_neg_std")

    def test_beta_negative_a(self):
        self._run_nan_check(sd.beta(-1, 2), "beta_neg_a")

    def test_beta_zero_b(self):
        self._run_nan_check(sd.beta(2, 0), "beta_zero_b")

    def test_binomial_negative_n(self):
        self._run_nan_check(sd.binomial(-5, 0.5), "binom_neg_n")

    def test_negbinomial_negative_n(self):
        self._run_nan_check(sd.negbinomial(-5, 0.5), "negbinom_neg_n")

    def test_poisson_negative_mu(self):
        self._run_nan_check(sd.poisson(-5), "poisson_neg_mu")

    def test_gamma_negative_shape(self):
        self._run_nan_check(sd.gamma(-1, 2), "gamma_neg_shape")

    def test_gamma_zero_scale(self):
        self._run_nan_check(sd.gamma(2, 0), "gamma_zero_scale")

    def test_exprnd_negative_scale(self):
        self._run_nan_check(sd.exprnd(-1), "exprnd_neg")

    def test_exprnd_zero_scale(self):
        self._run_nan_check(sd.exprnd(0), "exprnd_zero")

    def test_lognormal_negative_stddev(self):
        self._run_nan_check(sd.lognormal(0, -1), "lognorm_neg_std")

    def test_logistic_negative_scale(self):
        self._run_nan_check(sd.logistic(0, -1), "logistic_neg_scale")

    def test_triangular_lower_gt_upper(self):
        self._run_nan_check(sd.triangular(10, 5, 1), "tri_lower_gt_upper")

    def test_triangular_mode_gt_upper(self):
        self._run_nan_check(sd.triangular(0, 15, 10), "tri_mode_gt_upper")

    def test_weibull_negative_shape(self):
        self._run_nan_check(sd.weibull(-1, 2), "weibull_neg_shape")

    def test_weibull_zero_scale(self):
        self._run_nan_check(sd.weibull(2, 0), "weibull_zero_scale")


# ---------------------------------------------------------------------------
# Step-by-step parity (Phase 4 Substep 4d): the same fixtures as the
# run_scenarios parity tests above, exercised through bptk.begin_session +
# run_step instead. Two flavours:
#
#   TestRunStepParity            — whole-session: run Python all the way, run
#                                  Rust all the way, then compare histories.
#                                  Mirrors the _run_both pattern.
#
#   TestRunStepInterleavedParity — Python step N and Rust step N are computed
#                                  back-to-back on independent bptk instances
#                                  (the builders are called twice) and
#                                  compared *before* either side advances.
#                                  Catches state-bleed bugs that a converging
#                                  whole-session run could hide.
# ---------------------------------------------------------------------------

def _run_session_history(bptk, scenario_managers, scenarios, equations, steps,
                         settings_per_step=None, backend="python", seed=None):
    """Drive a session for `steps` calls; return the list of run_step results."""
    bptk.begin_session(scenarios=scenarios, scenario_managers=scenario_managers,
                       equations=equations, backend=backend, seed=seed)
    history = []
    try:
        for i in range(steps):
            per_step = settings_per_step[i] if settings_per_step and i < len(settings_per_step) else None
            history.append(bptk.run_step(settings=per_step))
    finally:
        bptk.end_session()
    return history


def _assert_step_dicts_equal(py_step, rust_step, step_idx, rel=1e-9, abs_tol=1e-9):
    """Compare a single {manager: {scenario: {equation: {t: value}}}} dict."""
    assert set(py_step.keys()) == set(rust_step.keys()), \
        "step {}: scenario manager keys differ".format(step_idx)
    for manager in py_step:
        assert set(py_step[manager].keys()) == set(rust_step[manager].keys()), \
            "step {}/{}: scenario keys differ".format(step_idx, manager)
        for scenario in py_step[manager]:
            py_sc = py_step[manager][scenario]
            rust_sc = rust_step[manager][scenario]
            assert set(py_sc.keys()) == set(rust_sc.keys()), \
                "step {}/{}/{}: equation keys differ".format(step_idx, manager, scenario)
            for eq in py_sc:
                py_eq = py_sc[eq]
                rust_eq = rust_sc[eq]
                assert set(py_eq.keys()) == set(rust_eq.keys()), \
                    "step {}/{}/{}/{}: time keys differ".format(
                        step_idx, manager, scenario, eq)
                for t in py_eq:
                    assert py_eq[t] == pytest.approx(rust_eq[t], rel=rel, abs=abs_tol), \
                        "step {} @ t={}: {}/{}/{} python={} rust={}".format(
                            step_idx, t, manager, scenario, eq, py_eq[t], rust_eq[t])


def _interleave_step(builder, scenario_managers, scenarios, equations, steps,
                     settings_per_step=None, rel=1e-9, abs_tol=1e-9):
    """Stand up two independent bptk instances (Python + Rust) and step them
    in lockstep, comparing after each step."""
    py_bptk = builder()
    rust_bptk = builder()

    py_bptk.begin_session(scenarios=scenarios, scenario_managers=scenario_managers,
                          equations=equations, backend="python")
    rust_bptk.begin_session(scenarios=scenarios, scenario_managers=scenario_managers,
                            equations=equations, backend="rust")
    try:
        for i in range(steps):
            per_step = settings_per_step[i] if settings_per_step and i < len(settings_per_step) else None
            py_res = py_bptk.run_step(settings=per_step)
            rust_res = rust_bptk.run_step(settings=per_step)
            _assert_step_dicts_equal(py_res, rust_res, i, rel=rel, abs_tol=abs_tol)
    finally:
        py_bptk.end_session()
        rust_bptk.end_session()


class TestRunStepParity:
    """Whole-session step parity: run Python session, then Rust session,
    then compare histories. Uses the same model fixtures as the run_scenarios
    parity tests above."""

    def test_simple_step_parity(self):
        # starttime=1, stoptime=10, dt=1 → 10 calls covers t=1..10
        py = _run_session_history(_build_simple_bptk(), ["mgr"], ["base", "double"],
                                  ["stock", "flow"], steps=10, backend="python")
        rust = _run_session_history(_build_simple_bptk(), ["mgr"], ["base", "double"],
                                    ["stock", "flow"], steps=10, backend="rust")
        for i, (p, r) in enumerate(zip(py, rust)):
            _assert_step_dicts_equal(p, r, i)

    def test_sir_step_parity(self):
        # SIR fixture is dt=0.25; restrict to dt=1 stepping by building 21 steps with
        # the default starttime/stoptime → covers t=0..20 (with dt=0.25, that's 81
        # internal steps; run_step still advances by dt per call).
        # NB: the SIR fixture uses dt=0.25, but run_step's caller-step is the time,
        # which advances by session_state["dt"]=1.0 by default. Using fewer outer
        # iterations is fine — both backends advance their cursor by the same model
        # dt internally.
        py = _run_session_history(_build_sir_bptk(), ["sir_mgr"], ["base"],
                                  ["susceptible", "infected", "recovered"],
                                  steps=21, backend="python")
        rust = _run_session_history(_build_sir_bptk(), ["sir_mgr"], ["base"],
                                    ["susceptible", "infected", "recovered"],
                                    steps=21, backend="rust")
        for i, (p, r) in enumerate(zip(py, rust)):
            _assert_step_dicts_equal(p, r, i, abs_tol=1e-6)

    def test_lookup_step_parity(self):
        py = _run_session_history(_build_lookup_bptk(), ["lookup_mgr"], ["base"],
                                  ["stock", "rate"], steps=11, backend="python")
        rust = _run_session_history(_build_lookup_bptk(), ["lookup_mgr"], ["base"],
                                    ["stock", "rate"], steps=11, backend="rust")
        for i, (p, r) in enumerate(zip(py, rust)):
            _assert_step_dicts_equal(p, r, i)

    def test_lookup_points_override_step_parity(self):
        py = _run_session_history(_build_lookup_bptk(), ["lookup_mgr"], ["new_table"],
                                  ["stock", "rate"], steps=11, backend="python")
        rust = _run_session_history(_build_lookup_bptk(), ["lookup_mgr"], ["new_table"],
                                    ["stock", "rate"], steps=11, backend="rust")
        for i, (p, r) in enumerate(zip(py, rust)):
            _assert_step_dicts_equal(p, r, i)

    def test_dotted_module_step_parity(self):
        """Module-namespaced element names (`Retailer.inventory`) — beergame
        Substep 4i risk pre-empted at the step-by-step layer."""
        eqs = ["Retailer.inventory", "Wholesaler.inventory", "Retailer.order"]
        py = _run_session_history(_build_dotted_module_bptk(), ["chain"], ["base"],
                                  eqs, steps=6, backend="python")
        rust = _run_session_history(_build_dotted_module_bptk(), ["chain"], ["base"],
                                    eqs, steps=6, backend="rust")
        for i, (p, r) in enumerate(zip(py, rust)):
            _assert_step_dicts_equal(p, r, i)


class TestRunStepInterleavedParity:
    """Interleaved step parity: Python step N and Rust step N back-to-back on
    independent bptk instances, compared before either advances."""

    def test_simple_interleaved(self):
        _interleave_step(_build_simple_bptk, ["mgr"], ["base", "double"],
                         ["stock", "flow"], steps=10)

    def test_sir_interleaved(self):
        _interleave_step(_build_sir_bptk, ["sir_mgr"], ["base"],
                         ["susceptible", "infected", "recovered"],
                         steps=21, abs_tol=1e-6)

    def test_sir_high_contact_interleaved(self):
        _interleave_step(_build_sir_bptk, ["sir_mgr"], ["high_contact"],
                         ["susceptible", "infected", "recovered"],
                         steps=21, abs_tol=1e-6)

    def test_lookup_interleaved(self):
        _interleave_step(_build_lookup_bptk, ["lookup_mgr"], ["base"],
                         ["stock", "rate"], steps=11)

    def test_lookup_points_override_interleaved(self):
        _interleave_step(_build_lookup_bptk, ["lookup_mgr"], ["new_table"],
                         ["stock", "rate"], steps=11)

    def test_dotted_module_interleaved(self):
        _interleave_step(_build_dotted_module_bptk, ["chain"], ["base"],
                         ["Retailer.inventory", "Wholesaler.inventory", "Retailer.order"],
                         steps=6)


class TestRunStepInterleavedSettingsOverrides:
    """Interleaved comparison under mid-session settings overrides. This is the
    case most likely to surface a sticky-override divergence between Python and
    Rust, because both engines must apply set_constant/set_points to the same
    timestep with the same semantics ('takes effect from the next step')."""

    def test_constant_override_interleaved(self):
        # Bump at step 2, restore at step 5, bump again at step 7 — three distinct
        # overrides should expose any state that fails to clear or fails to apply.
        s = [None, None,
             {"mgr": {"base": {"constants": {"constant": 7.0}}}},
             None, None,
             {"mgr": {"base": {"constants": {"constant": 1.0}}}},
             None,
             {"mgr": {"base": {"constants": {"constant": 12.0}}}},
             None, None]
        _interleave_step(_build_simple_bptk, ["mgr"], ["base"],
                         ["stock", "flow"], steps=10, settings_per_step=s)

    def test_alternating_constant_override_interleaved(self):
        """Override at every step. Stresses the per-step set_constant path."""
        s = [None] + [
            {"mgr": {"base": {"constants": {"constant": float(i % 5 + 1)}}}}
            for i in range(9)
        ]
        _interleave_step(_build_simple_bptk, ["mgr"], ["base"],
                         ["stock", "flow"], steps=10, settings_per_step=s)

    def test_points_override_interleaved(self):
        new_table = [[0, 10], [5, 10], [10, 10]]
        s = [None, None,
             {"lookup_mgr": {"base": {"points": {"rate_table": new_table}}}},
             None, None, None, None, None, None, None, None]
        _interleave_step(_build_lookup_bptk, ["lookup_mgr"], ["base"],
                         ["stock", "rate"], steps=11, settings_per_step=s)


class TestRunStepFeatureParity:
    """Step-by-step Python-vs-Rust parity for the stateful + functional features
    that the run_scenarios parity tests above already cover. Each test builds a
    small model inline, then drives both backends through bptk.begin_session +
    run_step and asserts per-step parity.

    These tests catch bugs that whole-simulation parity can't surface — anything
    where the runner's per-step state management (cursor advance, override
    application, dt-mismatch handling) interacts badly with a stateful element."""

    def _step_parity(self, builder, manager, scenarios, equations, steps,
                     rel=1e-9, abs_tol=1e-9):
        """Run the same session on both backends with two fresh bptk instances
        and assert step-by-step parity. Used by all the feature tests below."""
        py = _run_session_history(builder(), [manager], scenarios, equations,
                                  steps=steps, backend="python")
        rust = _run_session_history(builder(), [manager], scenarios, equations,
                                    steps=steps, backend="rust")
        for i, (p, r) in enumerate(zip(py, rust)):
            _assert_step_dicts_equal(p, r, i, rel=rel, abs_tol=abs_tol)

    # -- Stateful functions --

    def test_smooth_step_parity(self):
        def build():
            model = Model(starttime=1, stoptime=10, dt=0.1, name="smooth_step")
            inp = model.converter("input_function")
            inp.equation = sd.step(10.0, 3.0)
            out = model.converter("smooth_out")
            out.equation = sd.smooth(model, inp, 1.0, 0.0)
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"smooth_mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="smooth_mgr")
            return b
        # Session runs t=1..10 (10 calls); model.dt=0.1 → 10 internal steps per call.
        self._step_parity(build, "smooth_mgr", ["base"], ["smooth_out"],
                          steps=10, abs_tol=1e-6)

    def test_trend_step_parity(self):
        def build():
            model = Model(starttime=1, stoptime=10, dt=0.1, name="trend_step")
            inp = model.converter("input_function")
            inp.equation = sd.step(10.0, 3.0)
            out = model.converter("trend_out")
            out.equation = sd.trend(model, inp, 2.0, 5.0)
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"trend_mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="trend_mgr")
            return b
        self._step_parity(build, "trend_mgr", ["base"], ["trend_out"],
                          steps=10, abs_tol=1e-6)

    def test_delay_step_parity(self):
        """sd.delay needs a memo lookback — exercises Rust's pre-allocated memo
        from a partial cursor position."""
        def build():
            model = Model(starttime=0, stoptime=10, dt=1, name="delay_step")
            a = model.converter("a")
            b_eq = model.converter("b")
            a.equation = sd.time()
            b_eq.equation = sd.delay(model, a, 3.0, 0.0)
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"delay_mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="delay_mgr")
            return b
        self._step_parity(build, "delay_mgr", ["base"], ["a", "b"], steps=11)

    def test_biflow_step_parity(self):
        """Biflow allows negative flow values; per-step backend must agree."""
        def build():
            model = Model(starttime=0, stoptime=10, dt=0.1, name="biflow_step")
            position = model.stock("position")
            velocity = model.biflow("velocity")
            position.initial_value = 10.0
            position.equation = velocity
            velocity.equation = -position
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return b
        self._step_parity(build, "mgr", ["base"], ["position", "velocity"],
                          steps=11, abs_tol=1e-6)

    # -- Lookup variants --

    def test_inline_lookup_step_parity(self):
        def build():
            model = Model(starttime=0, stoptime=10, dt=0.5, name="inline_lookup_step")
            x = model.converter("input_val")
            x.equation = sd.time() * 0.5
            out = model.converter("output")
            out.equation = sd.lookup(x, [(0, 0), (1, 2), (2, 6), (3, 4), (5, 10)])
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return b
        self._step_parity(build, "mgr", ["base"], ["input_val", "output"], steps=11)

    # -- Math functions --

    def test_ln_log10_step_parity(self):
        def build():
            model = Model(starttime=1, stoptime=10, dt=1, name="ln_log10_step")
            inp = model.converter("input")
            inp.equation = sd.time()
            fn_ln = model.converter("fn_ln")
            fn_ln.equation = sd.ln(inp)
            fn_log10 = model.converter("fn_log10")
            fn_log10.equation = sd.log10(inp)
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return b
        self._step_parity(build, "mgr", ["base"], ["fn_ln", "fn_log10"], steps=10)

    def test_floor_ceil_step_parity(self):
        def build():
            model = Model(starttime=0, stoptime=10, dt=1, name="floor_ceil_step")
            inp = model.converter("input")
            inp.equation = sd.time() * 1.7 - 3.0
            fn_floor = model.converter("fn_floor")
            fn_floor.equation = sd.floor(inp)
            fn_ceil = model.converter("fn_ceil")
            fn_ceil.equation = sd.ceil(inp)
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return b
        self._step_parity(build, "mgr", ["base"], ["fn_floor", "fn_ceil"], steps=11)

    def test_round_digits_step_parity(self):
        def build():
            model = Model(starttime=0, stoptime=5, dt=1, name="round_step")
            out = model.converter("x")
            out.equation = sd.round(sd.time() * 0.314159, 2)
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return b
        self._step_parity(build, "mgr", ["base"], ["x"], steps=6)

    def test_min_max_step_parity(self):
        def build():
            model = Model(starttime=0, stoptime=5, dt=1, name="minmax_step")
            a = model.converter("a")
            a.equation = sd.time()
            b_eq = model.converter("b")
            b_eq.equation = 3.0
            mn = model.converter("mn")
            mn.equation = sd.min(a, b_eq)
            mx = model.converter("mx")
            mx.equation = sd.max(a, b_eq)
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return b
        self._step_parity(build, "mgr", ["base"], ["mn", "mx"], steps=6)

    # -- Combinatorial --

    def test_combinatorial_step_parity(self):
        def build():
            model = Model(starttime=0, stoptime=5, dt=1, name="combinatorial_step")
            n = model.converter("n")
            n.equation = sd.time() + 2.0
            fact = model.converter("fact")
            fact.equation = sd.factorial(n)
            comb = model.converter("comb")
            comb.equation = sd.combinations(n, 2.0)
            perm = model.converter("perm")
            perm.equation = sd.permutations(n, 2.0)
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return b
        self._step_parity(build, "mgr", ["base"], ["fact", "comb", "perm"], steps=6)

    # -- Statistical (deterministic) --

    def test_invnorm_step_parity(self):
        def build():
            model = Model(starttime=0, stoptime=5, dt=1, name="invnorm_step")
            p = model.converter("p")
            p.equation = (sd.time() + 1.0) * 0.1
            out = model.converter("invn")
            out.equation = sd.invnorm(p)
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return b
        self._step_parity(build, "mgr", ["base"], ["invn"], steps=6, abs_tol=1e-9)

    def test_normalcdf_step_parity(self):
        def build():
            model = Model(starttime=0, stoptime=5, dt=1, name="normalcdf_step")
            t = model.converter("t_val")
            t.equation = sd.time() - 2.0
            out = model.converter("cdf")
            out.equation = sd.normalcdf(-1.0, t)
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return b
        self._step_parity(build, "mgr", ["base"], ["cdf"], steps=6, abs_tol=1e-9)

    # -- Edge values --

    def test_inf_nan_step_parity(self):
        def build():
            model = Model(starttime=0, stoptime=3, dt=1, name="infnan_step")
            inf_c = model.converter("inf_c")
            inf_c.equation = sd.Inf()
            nan_c = model.converter("nan_c")
            nan_c.equation = sd.nan()
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return b
        # NaN ≠ NaN under == comparison, so assert inf parity and that nan stays nan.
        py = _run_session_history(build(), ["mgr"], ["base"], ["inf_c", "nan_c"],
                                  steps=4, backend="python")
        rust = _run_session_history(build(), ["mgr"], ["base"], ["inf_c", "nan_c"],
                                    steps=4, backend="rust")
        import math
        for i in range(4):
            for t, v in py[i]["mgr"]["base"]["inf_c"].items():
                assert v == rust[i]["mgr"]["base"]["inf_c"][t]
            for t, v in py[i]["mgr"]["base"]["nan_c"].items():
                assert math.isnan(v) and math.isnan(rust[i]["mgr"]["base"]["nan_c"][t])


class TestRunStepLifecycle:
    """Integration-level smoke tests for the begin_session / run_step / end_session
    lifecycle. The unit-level coverage of these paths lives in
    tests/unittests/test_bptk.py; this class catches anything that only surfaces
    with a real model registered through the scenario manager factory."""

    def test_back_to_back_sessions(self):
        """Two Rust-backed sessions on the same bptk must each start cleanly
        at starttime — the second must not inherit the first session's cursor."""
        bptk = _build_simple_bptk()

        first = _run_session_history(bptk, ["mgr"], ["base"], ["stock", "flow"],
                                     steps=4, backend="rust")

        # Same bptk, fresh session. end_session was called inside the helper.
        second = _run_session_history(bptk, ["mgr"], ["base"], ["stock", "flow"],
                                      steps=4, backend="rust")

        # Identical trajectories.
        for i in range(4):
            assert first[i]["mgr"]["base"]["stock"] == second[i]["mgr"]["base"]["stock"]
            assert first[i]["mgr"]["base"]["flow"] == second[i]["mgr"]["base"]["flow"]


# ---------------------------------------------------------------------------
#  Substep 4g — resume after a Rust-backed session is reloaded from external
#  state. The live RustSdModel handle is not part of session_state, so on
#  resume the runner must replay settings_log to drive the cursor back to the
#  current step. These tests simulate the server's reconstruct_instance path
#  (fresh bptk + _set_state(deepcopy(session_state))) at the bptk level; the
#  end-to-end file-adapter path is covered in tests/test_rust_server.py.
# ---------------------------------------------------------------------------

def _resume_history(builder, scenario_managers, scenarios, equations, total_steps,
                    break_after, settings_per_step=None, backend="rust", seed=None):
    """Run `break_after` steps on one bptk, snapshot its session_state, then run
    the remaining steps on a *fresh* bptk seeded with that snapshot — mimicking a
    process restart where the in-memory engine state is lost. Returns the full
    list of step results across the two processes."""
    import copy

    def _settings_at(i):
        return settings_per_step[i] if settings_per_step and i < len(settings_per_step) else None

    first = builder()
    first.begin_session(scenarios=scenarios, scenario_managers=scenario_managers,
                        equations=equations, backend=backend, seed=seed)
    history = []
    for i in range(break_after):
        history.append(first.run_step(settings=_settings_at(i)))
    snapshot = copy.deepcopy(first.session_state)
    # The snapshot is what a restart would reload; `first` is the dead process.
    # We end its session now (after snapshotting) purely to release the abandoned
    # RustSdModel handles deterministically — leaving them for GC can trip PyO3's
    # cross-thread "unsendable dropped on another thread" warning in later tests.
    first.end_session()

    second = builder()
    second._set_state(snapshot)
    for i in range(break_after, total_steps):
        history.append(second.run_step(settings=_settings_at(i)))
    second.end_session()
    return history


class TestRustResume:
    """Resume correctness for Rust-backed sessions restored from external state."""

    def test_resume_simple_deterministic(self):
        """A 10-step simple session, broken after step 5 and resumed on a fresh
        bptk, must match a single-process 10-step run."""
        single = _run_session_history(_build_simple_bptk(), ["mgr"], ["base"],
                                      ["stock", "flow"], steps=10, backend="rust")
        resumed = _resume_history(_build_simple_bptk, ["mgr"], ["base"],
                                  ["stock", "flow"], total_steps=10, break_after=5)
        for i in range(10):
            _assert_step_dicts_equal(single[i], resumed[i], i)

    def test_resume_sir_deterministic(self):
        """SIR (dt=0.25) resume parity — exercises stock integration across the
        replay boundary."""
        eqs = ["susceptible", "infected", "recovered"]
        single = _run_session_history(_build_sir_bptk(), ["sir_mgr"], ["base"],
                                      eqs, steps=21, backend="rust")
        resumed = _resume_history(_build_sir_bptk, ["sir_mgr"], ["base"],
                                  eqs, total_steps=21, break_after=8)
        for i in range(21):
            _assert_step_dicts_equal(single[i], resumed[i], i, abs_tol=1e-6)

    def test_grid_exported_into_session_state(self):
        """After stepping, the Rust memo grid is persisted in session_state so a
        resume can import it (all entities, not just requested equations)."""
        b = _build_simple_bptk()
        b.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                        equations=["stock", "flow"], backend="rust")
        for _ in range(4):
            b.run_step()
        blob = b.session_state["rust_state"]["mgr"]["base"]
        b.end_session()
        assert blob is not None, "grid was not exported"
        current_step, memo = blob[0], blob[1]
        assert current_step == 3, "4 steps -> cursor at index 3"
        # Every entity is exported, including the non-requested constant.
        assert set(memo.keys()) >= {"stock", "flow", "constant"}

    def test_resume_takes_import_path_not_replay(self):
        """Resume must rebuild the engine by importing the grid, not by replaying
        the settings_log step-by-step (guards against silent regression to replay)."""
        from BPTK_Py.scenariorunners.sd_runner import SdRunner
        calls = {"import": 0}
        original = SdRunner.restore_scenario_state_rust

        def spy(self, *a, **k):
            calls["import"] += 1
            return original(self, *a, **k)

        SdRunner.restore_scenario_state_rust = spy
        try:
            resumed = _resume_history(_build_simple_bptk, ["mgr"], ["base"],
                                      ["stock", "flow"], total_steps=10, break_after=5)
        finally:
            SdRunner.restore_scenario_state_rust = original

        assert calls["import"] >= 1, "resume did not use the grid-import path"
        single = _run_session_history(_build_simple_bptk(), ["mgr"], ["base"],
                                      ["stock", "flow"], steps=10, backend="rust")
        for i in range(10):
            _assert_step_dicts_equal(single[i], resumed[i], i)

    def test_stateless_cycle_via_file_adapter_matches_single(self):
        """Full externalise/reload of the whole session through a FileAdapter after
        every step (the stateless-server lifecycle) must match a single-process run —
        exercises the JSON round-trip of the persisted rust_state grid."""
        import copy, datetime, tempfile
        from BPTK_Py.externalstateadapter.file_adapter import FileAdapter
        from BPTK_Py.externalstateadapter.externalStateAdapter import InstanceState

        single = _run_session_history(_build_simple_bptk(), ["mgr"], ["base"],
                                      ["stock", "flow"], steps=10, backend="rust")

        adapter = FileAdapter(compress=True, path=tempfile.mkdtemp())
        b = _build_simple_bptk()
        b.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                        equations=["stock", "flow"], backend="rust")
        cycled = []
        for _ in range(10):
            cycled.append(b.run_step())
            snap = copy.deepcopy(b.session_state)
            adapter.save_instance(InstanceState(state=snap, instance_id="c",
                                                 time=str(datetime.datetime.now()),
                                                 timeout=3600, step=b.session_state["step"]))
            b.end_session()
            loaded = adapter.load_instance("c").state
            b = _build_simple_bptk()
            b._set_state(loaded)
        b.end_session()

        for i in range(10):
            _assert_step_dicts_equal(single[i], cycled[i], i)

    def test_resume_falls_back_to_replay_when_grid_missing(self):
        """No exported grid (e.g. a Python-fallback scenario) -> resume must replay
        the settings_log and still match a single-process run."""
        import copy
        single = _run_session_history(_build_simple_bptk(), ["mgr"], ["base"],
                                      ["stock", "flow"], steps=10, backend="rust")
        first = _build_simple_bptk()
        first.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                            equations=["stock", "flow"], backend="rust")
        hist = [first.run_step() for _ in range(5)]
        snap = copy.deepcopy(first.session_state)
        for _m, scs in snap["rust_state"].items():   # wipe grids -> force replay
            for s in scs:
                scs[s] = None
        first.end_session()
        second = _build_simple_bptk()
        second._set_state(snap)
        hist += [second.run_step() for _ in range(5, 10)]
        second.end_session()
        for i in range(10):
            _assert_step_dicts_equal(single[i], hist[i], i)

    def test_resume_falls_back_to_replay_when_import_raises(self):
        """A corrupt exported grid must be caught and the scenario replayed instead."""
        import copy
        single = _run_session_history(_build_simple_bptk(), ["mgr"], ["base"],
                                      ["stock", "flow"], steps=10, backend="rust")
        first = _build_simple_bptk()
        first.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                            equations=["stock", "flow"], backend="rust")
        hist = [first.run_step() for _ in range(5)]
        snap = copy.deepcopy(first.session_state)
        for _m, scs in snap["rust_state"].items():   # out-of-range cursor -> import_state raises
            for s, blob in scs.items():
                if blob is not None:
                    scs[s] = [999999, blob[1]]
        first.end_session()
        second = _build_simple_bptk()
        second._set_state(snap)
        hist += [second.run_step() for _ in range(5, 10)]
        second.end_session()
        for i in range(10):
            _assert_step_dicts_equal(single[i], hist[i], i)

    def test_export_failure_is_swallowed(self):
        """If export_state() raises during run_step, the grid is stored as None
        (so resume replays) rather than crashing the step."""
        class _ExportRaises:
            def __init__(self, real):
                self._real = real

            def export_state(self):
                raise ValueError("boom")

            def __getattr__(self, name):
                return getattr(self._real, name)

        b = _build_simple_bptk()
        b.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                        equations=["stock", "flow"], backend="rust")
        b.run_step()
        sc = b.scenario_manager_factory.get_scenario(scenario_manager="mgr", scenario="base")
        sc.rust_model = _ExportRaises(sc.rust_model)
        b.run_step()  # export raises inside -> caught, grid set to None
        assert b.session_state["rust_state"]["mgr"]["base"] is None
        b.end_session()

    def test_resume_folds_points_overrides(self):
        """A per-step points (lookup) override recorded before the break must be
        re-applied on import so post-resume steps evaluate the overridden table."""
        new_table = [[0, 10], [5, 10], [10, 10]]
        s = [None, None,
             {"lookup_mgr": {"base": {"points": {"rate_table": new_table}}}},
             None, None, None, None, None, None, None, None]
        single = _run_session_history(_build_lookup_bptk(), ["lookup_mgr"], ["base"],
                                      ["stock", "rate"], steps=11, backend="rust",
                                      settings_per_step=s)
        resumed = _resume_history(_build_lookup_bptk, ["lookup_mgr"], ["base"],
                                  ["stock", "rate"], total_steps=11, break_after=5,
                                  settings_per_step=s)
        for i in range(11):
            _assert_step_dicts_equal(single[i], resumed[i], i)

    def test_restore_rejects_non_numeric_constant(self):
        """restore_scenario_state_rust guards against a non-numeric baseline
        constant (defensive symmetry with the first-step init path)."""
        from BPTK_Py.scenariorunners.sd_runner import SdRunner
        b = _build_simple_bptk()
        b.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                        equations=["stock", "flow"], backend="rust")
        b.run_step()
        blob = b.session_state["rust_state"]["mgr"]["base"]
        sc = b.scenario_manager_factory.get_scenario(scenario_manager="mgr", scenario="base")
        sc.rust_model = None
        sc.constants = {"constant": "not_a_number"}
        runner = SdRunner(b.scenario_manager_factory)
        with pytest.raises(ValueError):
            runner.restore_scenario_state_rust(sc, "mgr", "base", ["stock", "flow"], blob, None)
        b.end_session()

    def test_resume_with_per_step_overrides(self):
        """Resume must replay the recorded per-step settings, not just advance the
        cursor — a constant bumped before the break must still be in effect after."""
        s = [None, None,
             {"mgr": {"base": {"constants": {"constant": 9.0}}}},
             None, None, None, None, None, None, None]
        single = _run_session_history(_build_simple_bptk(), ["mgr"], ["base"],
                                      ["stock", "flow"], steps=10,
                                      settings_per_step=s, backend="rust")
        resumed = _resume_history(_build_simple_bptk, ["mgr"], ["base"],
                                  ["stock", "flow"], total_steps=10, break_after=5,
                                  settings_per_step=s)
        for i in range(10):
            _assert_step_dicts_equal(single[i], resumed[i], i)

    def test_resume_ignores_out_of_scope_manager(self):
        """When the bptk has managers the session didn't select, replay must skip
        them (only the in-scope manager's Rust cursor is rebuilt). Guards the
        out-of-scope branch in _restore_rust_session."""
        import copy

        def build_two_managers():
            m1 = Model(starttime=1, stoptime=10, dt=1, name="m1")
            s1 = m1.stock("stock"); f1 = m1.flow("flow"); c1 = m1.constant("constant")
            s1.initial_value = 0.0; s1.equation = f1; f1.equation = c1; c1.equation = 1.0
            m2 = Model(starttime=1, stoptime=10, dt=1, name="m2")
            s2 = m2.stock("stock"); f2 = m2.flow("flow"); c2 = m2.constant("constant")
            s2.initial_value = 0.0; s2.equation = f2; f2.equation = c2; c2.equation = 5.0
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"in_scope": {"model": m1}})
            b.register_scenario_manager({"out_of_scope": {"model": m2}})
            b.register_scenarios(scenario_manager="in_scope",
                                 scenarios={"base": {"constants": {"constant": 1.0}}})
            b.register_scenarios(scenario_manager="out_of_scope",
                                 scenarios={"base": {"constants": {"constant": 5.0}}})
            return b

        # Reference: in-memory session scoped to in_scope only.
        ref = _run_session_history(build_two_managers(), ["in_scope"], ["base"],
                                   ["stock", "flow"], steps=10, backend="rust")

        # Resume across a break — the out_of_scope manager exists on the factory but
        # is not in session scope, so the replay loop must continue past it.
        first = build_two_managers()
        first.begin_session(scenarios=["base"], scenario_managers=["in_scope"],
                            equations=["stock", "flow"], backend="rust")
        resumed = [first.run_step() for _ in range(5)]
        snapshot = copy.deepcopy(first.session_state)
        first.end_session()

        second = build_two_managers()
        second._set_state(snapshot)
        resumed += [second.run_step() for _ in range(5)]
        second.end_session()

        for i in range(10):
            _assert_step_dicts_equal(ref[i], resumed[i], i)
            assert "out_of_scope" not in resumed[i]

    def test_resume_multiple_breaks(self):
        """Resume repeatedly (every step is its own process) — the stateless
        server case with externalize_state_completely=True. Each step replays the
        whole prior history; results must still match a single-process run."""
        import copy
        single = _run_session_history(_build_simple_bptk(), ["mgr"], ["base"],
                                      ["stock", "flow"], steps=8, backend="rust")

        # Drive the session one step per fresh bptk, threading session_state through.
        state = None
        resumed = []
        for i in range(8):
            b = _build_simple_bptk()
            if state is None:
                b.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                                equations=["stock", "flow"], backend="rust")
            else:
                b._set_state(state)
            resumed.append(b.run_step())
            state = copy.deepcopy(b.session_state)

        for i in range(8):
            _assert_step_dicts_equal(single[i], resumed[i], i)


class TestRustResumeStochastic:
    """Seed plumbing for stochastic Rust sessions.

    Resume contract (no-replay memo import): the mid-stream RNG position cannot be
    recovered, so a resumed stochastic session does NOT reproduce the single-process
    trajectory bit-for-bit. Instead:
      * already-computed (exported) steps are preserved exactly;
      * post-resume draws are re-seeded per cursor position, so they are
        non-degenerate (not a repeated constant) and deterministic given the
        persisted seed, but follow a different path than an uninterrupted run.
    The seed is still persisted — for the initial in-process draws and to make the
    resumed continuation deterministic."""

    @staticmethod
    def _build_stochastic_bptk():
        def build():
            model = Model(starttime=0, stoptime=10, dt=1, name="stochastic_step")
            # Accumulate stochastic draws into a stock so divergence compounds and
            # is easy to detect, plus expose the raw draws.
            draw = model.converter("draw")
            draw.equation = sd.normal(100, 15) + sd.poisson(4) + sd.random(0, 1)
            total = model.stock("total")
            total.initial_value = 0.0
            inflow = model.flow("inflow")
            inflow.equation = draw
            total.equation = inflow
            b = BPTK_Py.bptk()
            b.register_scenario_manager({"mgr": {"model": model}})
            b.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return b
        return build

    def test_same_seed_is_reproducible(self):
        """Two independent Rust sessions with the same seed produce identical
        stochastic trajectories."""
        build = self._build_stochastic_bptk()
        a = _run_session_history(build(), ["mgr"], ["base"], ["draw", "total"],
                                 steps=11, backend="rust")
        # Force the same seed on both runs.
        b_bptk = build()
        b_bptk.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                             equations=["draw", "total"], backend="rust", seed=12345)
        # Re-run `a` with the explicit seed too, so both share it.
        a_bptk = build()
        a_bptk.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                             equations=["draw", "total"], backend="rust", seed=12345)
        seeded_a, seeded_b = [], []
        for _ in range(11):
            seeded_a.append(a_bptk.run_step())
            seeded_b.append(b_bptk.run_step())
        a_bptk.end_session()
        b_bptk.end_session()
        for i in range(11):
            _assert_step_dicts_equal(seeded_a[i], seeded_b[i], i)

    def test_different_seed_diverges(self):
        """Sanity check the seed actually drives the RNG: different seeds give
        different stochastic trajectories."""
        build = self._build_stochastic_bptk()
        b1 = build(); b2 = build()
        b1.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                         equations=["total"], backend="rust", seed=1)
        b2.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                         equations=["total"], backend="rust", seed=2)
        h1, h2 = [], []
        for _ in range(11):
            h1.append(b1.run_step())
            h2.append(b2.run_step())
        b1.end_session(); b2.end_session()
        # The accumulated totals at the final step should differ.
        last1 = list(h1[-1]["mgr"]["base"]["total"].values())[0]
        last2 = list(h2[-1]["mgr"]["base"]["total"].values())[0]
        assert last1 != last2, "different seeds produced identical trajectories"

    def test_resume_stochastic_preserves_past_diverges_future(self):
        """A seeded stochastic session, broken mid-run and resumed on a fresh bptk
        via memo import: the exported (past) steps are preserved exactly, while the
        post-resume steps diverge from the single-process run (the RNG position is
        not restored). This is the documented trade-off of the no-replay import."""
        build = self._build_stochastic_bptk()
        break_after = 5
        single = build()
        single.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                             equations=["draw", "total"], backend="rust", seed=777)
        single_hist = [single.run_step() for _ in range(11)]
        single.end_session()

        resumed = _resume_history(build, ["mgr"], ["base"], ["draw", "total"],
                                  total_steps=11, break_after=break_after, seed=777)

        # Past (exported) steps: identical to the single-process run.
        for i in range(break_after):
            _assert_step_dicts_equal(single_hist[i], resumed[i], i)

        # Post-resume steps: the accumulated total diverges (RNG re-seeded on import).
        single_last = list(single_hist[-1]["mgr"]["base"]["total"].values())[0]
        resumed_last = list(resumed[-1]["mgr"]["base"]["total"].values())[0]
        assert single_last != resumed_last, "expected post-resume divergence"

    def test_resume_stochastic_is_nondegenerate_and_deterministic(self):
        """Post-resume draws must NOT collapse to a repeated constant (per-position
        re-seeding), and two resumes with the same persisted seed must agree."""
        build = self._build_stochastic_bptk()

        def draws_after_resume():
            hist = _resume_history(build, ["mgr"], ["base"], ["draw", "total"],
                                   total_steps=11, break_after=5, seed=777)
            out = []
            for step in hist[5:]:
                ts = step["mgr"]["base"]["draw"]
                out.append(ts[list(ts.keys())[-1]])
            return out

        d1 = draws_after_resume()
        d2 = draws_after_resume()
        assert len(set(round(x, 9) for x in d1)) > 1, "post-resume draws degenerated to a constant"
        assert all(abs(a - b) < 1e-12 for a, b in zip(d1, d2)), "same seed gave different resumes"

    def test_seed_is_none_or_passthrough(self):
        """The seed is None-or-not-None: stored verbatim, never auto-generated.
        Deterministic models leave it None (no RNG → seed never matters); a
        stochastic model that wants reproducible resume passes one explicitly."""
        build = self._build_stochastic_bptk()

        # No seed given → stays None (for both backends).
        b = build()
        b.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                        equations=["total"], backend="rust")
        assert b.session_state["backend_seed"] is None
        b.end_session()

        p = build()
        p.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                        equations=["total"], backend="python")
        assert p.session_state["backend_seed"] is None
        p.end_session()

        # Explicit seed → stored verbatim.
        s = build()
        s.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                        equations=["total"], backend="rust", seed=98765)
        assert s.session_state["backend_seed"] == 98765
        s.end_session()


class _FakeRedis:
    """Minimal in-memory stand-in for a redis.Redis client (dict-backed)."""

    def __init__(self):
        self._store = {}

    def set(self, key, value):
        self._store[key] = value
        return True

    def get(self, key):
        return self._store.get(key)

    def delete(self, key):
        existed = key in self._store
        self._store.pop(key, None)
        return 1 if existed else 0

    def expire(self, key, seconds):
        return True


class TestRustResumeThroughAdapters:
    """The rust_state grid must survive the external-state serialisation used by
    the Postgres and Redis adapters (jsonpickle), not just the FileAdapter (JSON)."""

    def test_rust_state_survives_jsonpickle_roundtrip(self):
        """jsonpickle is the serializer used by BOTH the Postgres and Redis adapters.
        Confirm the exported grid round-trips through it byte-for-value."""
        import jsonpickle
        b = _build_simple_bptk()
        b.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                        equations=["stock", "flow"], backend="rust")
        for _ in range(5):
            b.run_step()
        blob = b.session_state["rust_state"]["mgr"]["base"]
        restored = jsonpickle.decode(jsonpickle.encode(b.session_state, make_refs=False))
        b.end_session()
        rblob = restored["rust_state"]["mgr"]["base"]
        assert rblob[0] == blob[0]                       # cursor
        assert set(rblob[1].keys()) == set(blob[1].keys())  # all entities
        for name in blob[1]:
            assert rblob[1][name] == blob[1][name]       # grid values

    @pytest.mark.requires_extra("server")
    def test_stateless_cycle_via_redis_adapter_matches_single(self):
        """Full save/load cycle through a real RedisAdapter (in-memory fake client),
        externalising after every step, must match a single-process run."""
        import copy, datetime
        from BPTK_Py.externalstateadapter.externalStateAdapter import InstanceState
        from BPTK_Py.externalstateadapter.redis_adapter import RedisAdapter

        single = _run_session_history(_build_simple_bptk(), ["mgr"], ["base"],
                                      ["stock", "flow"], steps=10, backend="rust")

        adapter = RedisAdapter(redis_client=_FakeRedis(), compress=True)
        b = _build_simple_bptk()
        b.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                        equations=["stock", "flow"], backend="rust")
        cycled = []
        for _ in range(10):
            cycled.append(b.run_step())
            adapter.save_instance(InstanceState(state=copy.deepcopy(b.session_state),
                                                instance_id="c",
                                                time=datetime.datetime.now(),
                                                timeout={}, step=b.session_state["step"]))
            b.end_session()
            loaded = adapter.load_instance("c").state
            b = _build_simple_bptk()
            b._set_state(loaded)
        b.end_session()

        for i in range(10):
            _assert_step_dicts_equal(single[i], cycled[i], i)


# ---------------------------------------------------------------------------
# Tests: feedback loops through the bptk layer
#
# These are the tests that would have caught the beergame blocker. They rely on
# the no_silent_rust_fallback guard in conftest.py: without it, a model the engine
# refuses is computed in Python on *both* runs and the comparison passes for the
# wrong reason.
# ---------------------------------------------------------------------------

class TestDelayFeedbackLoop:
    """A loop broken only by a delay must run on the Rust backend, not fall back."""

    def _build_loop_bptk(self):
        model = Model(starttime=1, stoptime=5, dt=1, name="delay_loop")
        a = model.converter("a")
        b = model.converter("b")
        c = model.converter("c")
        d = model.converter("d")
        a.equation = d + 1.0
        b.equation = a * 2.0
        c.equation = b + 1.0
        d.equation = sd.delay(model, c, 1.0, 0.0)

        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"mgr": {"model": model}})
        bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
        return bptk

    def test_run_scenarios_parity(self):
        bptk = self._build_loop_bptk()
        py, rust = _run_both(bptk, "mgr", ["base"], ["a", "b", "c", "d"])
        assert_frame_equal(py, rust, atol=1e-10)

    def test_step_parity(self):
        bptk_py_run = self._build_loop_bptk()
        bptk_rust_run = self._build_loop_bptk()
        equations = ["a", "b", "c", "d"]

        py_history = _run_session_history(
            bptk_py_run, ["mgr"], ["base"], equations, steps=5, backend="python")
        rust_history = _run_session_history(
            bptk_rust_run, ["mgr"], ["base"], equations, steps=5, backend="rust")

        assert len(py_history) == len(rust_history)
        for i, (py_step, rust_step) in enumerate(zip(py_history, rust_history)):
            _assert_step_dicts_equal(py_step, rust_step, i)


# ---------------------------------------------------------------------------
# Tests: the model handle crossing threads
#
# A threaded WSGI server (Flask's dev server, uwsgi with threads) serves consecutive
# requests on different threads, while the runner keeps `sc.rust_model` on the
# Scenario between requests — so the handle really does travel between threads. With
# `#[pyclass(unsendable)]` that killed the process with a PyO3 PanicException on the
# second request.
# ---------------------------------------------------------------------------

class TestRustHandleAcrossThreads:

    def test_steps_from_different_threads(self):
        """Each step runs in its own thread, as a threaded server would do."""
        import threading

        equations = ["stock", "flow"]
        rust_bptk = _build_simple_bptk()
        rust_bptk.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                               equations=equations, backend="rust")
        collected, failures = [], []

        def one_step():
            try:
                collected.append(rust_bptk.run_step())
            except BaseException as e:            # PyO3 panics are BaseExceptions
                failures.append(e)

        try:
            for _ in range(5):
                thread = threading.Thread(target=one_step)
                thread.start()
                thread.join()
        finally:
            rust_bptk.end_session()

        assert not failures, "stepping from another thread failed: {!r}".format(failures[0])
        assert len(collected) == 5

        py_bptk = _build_simple_bptk()
        py_history = _run_session_history(py_bptk, ["mgr"], ["base"], equations,
                                         steps=5, backend="python")
        for i, (py_step, rust_step) in enumerate(zip(py_history, collected)):
            _assert_step_dicts_equal(py_step, rust_step, i)

    def test_run_scenarios_from_another_thread(self):
        """A whole-run simulation started on a thread other than the one that built
        the bptk instance."""
        import threading

        bptk = _build_simple_bptk()
        results, failures = [], []

        def run():
            try:
                results.append(bptk.run_scenarios(
                    scenario_managers=["mgr"], scenarios=["base"],
                    equations=["stock"], backend="rust"))
            except BaseException as e:
                failures.append(e)

        thread = threading.Thread(target=run)
        thread.start()
        thread.join()

        assert not failures, "running on another thread failed: {!r}".format(failures[0])
        assert not results[0].empty


# ---------------------------------------------------------------------------
# Tests: overrides passed with the *first* run_step
#
# init() evaluates step 0 (t == starttime) and its values are what the first
# run_step() returns, so the per-step settings of that first call must be applied
# before init(). Overriding a constant in round 1 was silently ignored by the Rust
# backend until 2026-08-11 — invisible whenever the override happened to equal the
# model's own default, which is exactly the case in the beergame's first round.
# ---------------------------------------------------------------------------

class TestRustFirstStepOverride:

    def _bptk(self):
        """`constant` defaults to 1.0 in the model; the tests override it to 7.0."""
        return _build_simple_bptk()

    def test_constant_override_in_first_step(self):
        equations = ["stock", "flow", "constant"]
        # deliberately different from both the model default (1.0) and the scenario
        # value, so an ignored override cannot pass unnoticed
        settings = [{"mgr": {"base": {"constants": {"constant": 7.0}}}} for _ in range(4)]

        py_history = _run_session_history(self._bptk(), ["mgr"], ["base"], equations,
                                         steps=4, settings_per_step=settings,
                                         backend="python")
        rust_history = _run_session_history(self._bptk(), ["mgr"], ["base"], equations,
                                           steps=4, settings_per_step=settings,
                                           backend="rust")

        # The override must be visible in the very first step, not from the second on.
        first_step = rust_history[0]["mgr"]["base"]
        starttime_key = sorted(first_step["constant"].keys())[0]
        assert first_step["constant"][starttime_key] == 7.0, \
            "override passed with the first run_step was ignored: {}".format(first_step)

        for i, (py_step, rust_step) in enumerate(zip(py_history, rust_history)):
            _assert_step_dicts_equal(py_step, rust_step, i)

    def test_points_override_in_first_step(self):
        def build():
            # A fresh Model per session: change_points() mutates model.points, so a
            # shared model would leak the Python run's override into the Rust run's
            # to_json() and mask the bug.
            model = Model(starttime=1, stoptime=5, dt=1, name="first_step_points")
            out = model.converter("out")
            model.points["tbl"] = [(float(t), 100.0) for t in range(1, 6)]
            out.equation = sd.lookup(sd.time(), "tbl")

            bptk = BPTK_Py.bptk()
            bptk.register_scenario_manager({"mgr": {"model": model}})
            bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return bptk

        overridden = [[float(t), 100.0 + 10.0 * t] for t in range(1, 6)]
        settings = [{"mgr": {"base": {"points": {"tbl": overridden}}}} for _ in range(3)]

        py_history = _run_session_history(build(), ["mgr"], ["base"], ["out"], steps=3,
                                         settings_per_step=settings, backend="python")
        rust_history = _run_session_history(build(), ["mgr"], ["base"], ["out"], steps=3,
                                           settings_per_step=settings, backend="rust")

        first_step = rust_history[0]["mgr"]["base"]["out"]
        assert list(first_step.values())[0] == 110.0, \
            "points override passed with the first run_step was ignored: {}".format(first_step)

        for i, (py_step, rust_step) in enumerate(zip(py_history, rust_history)):
            _assert_step_dicts_equal(py_step, rust_step, i)

    def test_stochastic_steps_from_different_threads(self):
        """The RNG sits behind a Mutex since the unsendable fix. Stepping a stochastic
        model from different threads must neither deadlock nor change the trajectory a
        given seed produces."""
        import threading

        def build():
            model = Model(starttime=1, stoptime=6, dt=1, name="threaded_stochastic")
            draw = model.converter("draw")
            total = model.stock("total")
            inflow = model.flow("inflow")
            draw.equation = sd.normal(100.0, 10.0)
            inflow.equation = draw
            total.initial_value = 0.0
            total.equation = inflow

            bptk = BPTK_Py.bptk()
            bptk.register_scenario_manager({"mgr": {"model": model}})
            bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
            return bptk

        equations = ["draw", "total"]

        threaded_bptk = build()
        threaded_bptk.begin_session(scenarios=["base"], scenario_managers=["mgr"],
                                   equations=equations, backend="rust", seed=42)
        threaded, failures = [], []

        def one_step():
            try:
                threaded.append(threaded_bptk.run_step())
            except BaseException as e:
                failures.append(e)

        try:
            for _ in range(6):
                thread = threading.Thread(target=one_step)
                thread.start()
                thread.join(timeout=30)
                assert not thread.is_alive(), "stepping deadlocked on the RNG mutex"
        finally:
            threaded_bptk.end_session()

        assert not failures, "stochastic stepping across threads failed: {!r}".format(failures[0])

        single = _run_session_history(build(), ["mgr"], ["base"], equations, steps=6,
                                     backend="rust", seed=42)
        for i, (single_step, threaded_step) in enumerate(zip(single, threaded)):
            _assert_step_dicts_equal(single_step, threaded_step, i)


# ---------------------------------------------------------------------------
# Tests: the fallback guard itself
#
# conftest.py fails any test during which bptk gave up on the Rust engine, because a
# parity test that compares "python" against a "rust" run that never happened compares
# Python with Python and passes for the wrong reason — how the delay-cycle limitation
# stayed hidden until 2026-08-11. Detection is by log message, so the guard is only as
# good as its marker list; these tests keep that list honest.
# ---------------------------------------------------------------------------

class TestFallbackGuard:

    # Log sites that mention falling back but do *not* mean "the Rust engine did not
    # run", each with the reason it is out of the guard's scope.
    KNOWN_NON_ENGINE_FALLBACKS = {
        "Invalid default_backend": "configuration validation, no engine involved",
        "invalid backend": "begin_session argument validation, no engine involved",
        "will fall back to replay": "Rust did run; only the resume shortcut degrades",
        "Failed to create Logfire span": "logging concern, unrelated to the backend",
    }

    def _fallback_log_sites(self):
        """Every log() call in BPTK_Py whose message talks about falling back."""
        import pathlib
        import re

        package_root = pathlib.Path(BPTK_Py.__file__).parent
        sites = []
        for path in sorted(package_root.rglob("*.py")):
            for number, line in enumerate(path.read_text(encoding="UTF-8").splitlines(), 1):
                if "log(" not in line:
                    continue
                if re.search(r"fall(?:ing|s)?\s+back|fallback", line, re.IGNORECASE):
                    sites.append((path.relative_to(package_root).as_posix(), number, line.strip()))
        return sites

    def test_every_fallback_log_site_is_covered(self):
        """A new fallback path — or a reworded message — must not slip past the guard.

        On failure: add the message to _RUST_FALLBACK_MARKERS in conftest.py, or, if it
        does not mean "Rust did not run", to KNOWN_NON_ENGINE_FALLBACKS above.
        """
        from conftest import _RUST_FALLBACK_MARKERS

        sites = self._fallback_log_sites()
        assert sites, "found no fallback log sites at all — has the search pattern rotted?"

        uncovered = []
        for path, number, line in sites:
            if any(known in line for known in self.KNOWN_NON_ENGINE_FALLBACKS):
                continue
            if not any(marker in line.lower() for marker in _RUST_FALLBACK_MARKERS):
                uncovered.append("{}:{}: {}".format(path, number, line))

        assert not uncovered, (
            "these fallback log sites are invisible to the guard in conftest.py:\n  "
            + "\n  ".join(uncovered))

    def test_known_non_engine_fallbacks_still_exist(self):
        """The exception list must not outlive the messages it exempts."""
        lines = "\n".join(line for _, _, line in self._fallback_log_sites())
        for known, reason in self.KNOWN_NON_ENGINE_FALLBACKS.items():
            assert known in lines, (
                "'{}' is exempted from the guard ({}) but no longer appears in BPTK_Py "
                "— drop it from KNOWN_NON_ENGINE_FALLBACKS".format(known, reason))

    @pytest.mark.allow_rust_fallback
    def test_guard_detects_a_real_fallback(self):
        """Provoke a fallback and confirm the guard's own helpers see it. Marked, so
        the guard does not fail this test for doing exactly what it is testing."""
        from conftest import _fallback_lines_since, _logfile_size

        model = Model(starttime=0, stoptime=3, dt=1, name="guard_probe")
        stock = model.stock("stock")
        flow = model.flow("flow")
        stock.initial_value = 100.0
        stock.equation = flow
        # A custom NaryOperator: works in Python, cannot be serialised to JSON.
        my_fn = model.function("my_custom_fn", lambda model, t, *args: 5.0)
        flow.equation = my_fn(model.stock("stock"))

        offset = _logfile_size()
        result = model.simulate(["stock"], backend="rust")

        assert result is not None, "the fallback must still produce Python results"
        assert _fallback_lines_since(offset), (
            "the guard did not notice a fallback that definitely happened — its marker "
            "list or the log destination has drifted")

    # The branches below are never taken in a green run — the guard only fails a test
    # when something went wrong — so they are exercised directly.

    def _drive_guard(self, item, appended_line=None):
        """Run the guard's hook wrapper around a fake test and return its Result."""
        from pluggy import Result
        import conftest as guard

        wrapper = guard.pytest_runtest_call(item)
        next(wrapper)  # the guard snapshots the logfile size here
        if appended_line:
            with open(logmod.logfile, "a", encoding="UTF-8") as f:
                f.write(appended_line + "\n")
        outcome = Result.from_call(lambda: None)
        try:
            wrapper.send(outcome)
        except StopIteration:
            pass
        return outcome

    @pytest.mark.allow_rust_fallback  # writes a probe line into the real logfile
    def test_guard_turns_a_fallback_into_a_failure(self):
        """The wiring, not just the detection: a fallback during a test must surface as
        an AssertionError on the call outcome."""
        class _UnmarkedItem:
            def get_closest_marker(self, name):
                return None

        outcome = self._drive_guard(
            _UnmarkedItem(),
            "2026-01-01 00:00:00, [WARN] Rust engine failed: probe — falling back to Python")

        with pytest.raises(AssertionError, match="fell back to Python"):
            outcome.get_result()

    @pytest.mark.allow_rust_fallback  # writes a probe line into the real logfile
    def test_guard_respects_the_opt_out_marker(self):
        """A marked test keeps its result even with a fallback in the log."""
        class _MarkedItem:
            def get_closest_marker(self, name):
                return object() if name == "allow_rust_fallback" else None

        outcome = self._drive_guard(
            _MarkedItem(),
            "2026-01-01 00:00:00, [WARN] Rust engine failed: probe — falling back to Python")

        assert outcome.get_result() is None

    def test_guard_survives_a_truncated_or_missing_logfile(self):
        """Tests that wipe the logfile must not make the guard raise on its own."""
        from conftest import _fallback_lines_since

        # offset far beyond the current size: the file was truncated meanwhile
        assert _fallback_lines_since(10 ** 9) == []

        original = logmod.logfile
        try:
            logmod.logfile = "does-not-exist.log"
            assert _fallback_lines_since(0) == []
        finally:
            logmod.logfile = original


# ---------------------------------------------------------------------------
# Tests: how loudly a mid-session fallback is reported
#
# Falling back to Python on the first step is harmless. Falling back later is not: the
# Python backend has no record of the rounds the Rust engine already played, so it
# rebuilds that history from the settings of the current step and anything stateful
# comes out wrong. Measured on a stock model: continuing a Rust session in Python from
# round 4 gave 24 instead of 18. That must not be reported as a mere [WARN].
# ---------------------------------------------------------------------------

@pytest.mark.allow_rust_fallback
class TestMidSessionFallbackIsLoud:

    def _bptk(self):
        return _build_simple_bptk()

    def _fail_rust_from_step(self, monkeypatch, threshold):
        """Make the Rust step path raise once the session has reached `threshold`."""
        original = SdRunner._run_scenario_step_rust

        def maybe_raise(self, sc, step, settings, scenario_manager, scenario, equations, seed=None):
            if float(step) >= threshold:
                raise ValueError("simulated engine failure")
            return original(self, sc, step, settings, scenario_manager, scenario, equations, seed=seed)

        monkeypatch.setattr(SdRunner, "_run_scenario_step_rust", maybe_raise)

    def _logfile_since(self, offset):
        with open(logmod.logfile, "r", encoding="UTF-8", errors="replace") as f:
            f.seek(offset)
            return f.read()

    def test_fallback_on_the_first_step_is_a_warning(self, monkeypatch):
        self._fail_rust_from_step(monkeypatch, threshold=0.0)   # fail immediately
        offset = os.path.getsize(logmod.logfile) if os.path.exists(logmod.logfile) else 0

        history = _run_session_history(self._bptk(), ["mgr"], ["base"], ["stock"],
                                       steps=3, backend="rust")

        content = self._logfile_since(offset)
        assert "[WARN] Rust step failed" in content
        assert "[ERROR] Rust step failed" not in content
        # results are still correct - Python simply ran the whole session
        python_history = _run_session_history(self._bptk(), ["mgr"], ["base"], ["stock"],
                                              steps=3, backend="python")
        for i, (py_step, fallback_step) in enumerate(zip(python_history, history)):
            _assert_step_dicts_equal(py_step, fallback_step, i)

    def test_fallback_after_the_session_advanced_is_an_error(self, monkeypatch):
        self._fail_rust_from_step(monkeypatch, threshold=3.0)   # fail from step 3 on
        offset = os.path.getsize(logmod.logfile) if os.path.exists(logmod.logfile) else 0

        _run_session_history(self._bptk(), ["mgr"], ["base"], ["stock"],
                             steps=4, backend="rust")

        content = self._logfile_since(offset)
        assert "[ERROR] Rust step failed" in content, content[-500:]
        assert "may be wrong" in content
        assert "at step 3.0" in content
