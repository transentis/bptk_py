"""Integration tests for the Rust execution backend via bptk.run_scenarios().

Tests that backend="rust" produces identical results to backend="python"
through the full BPTK scenario pipeline.
"""

import importlib
import pytest
import pandas as pd
from pandas._testing import assert_frame_equal

from BPTK_Py import Model
import BPTK_Py
import BPTK_Py.logger.logger as logmod
from BPTK_Py.sddsl import functions as sd


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_bptk():
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


@pytest.fixture
def sir_bptk():
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


@pytest.fixture
def lookup_bptk():
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
