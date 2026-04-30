"""
End-to-end tests for the Rust SD engine (BPTK_Py._rust_engine).

These tests verify the PyO3 bindings by exercising the full pipeline:
  1. Create a RustSdEngine instance
  2. Load a model from JSON (parse + topological sort + resolve refs)
  3. Run simulation (Euler integration)
  4. Verify results match expected values

The JSON model format mirrors the internal representation used by
BPTK-Py's SD DSL, making these tests a reference for the schema.

Parity tests (at the bottom) build identical models in both the Python
SD DSL and Rust JSON format, run both engines, and compare results to
prove the Rust engine matches the Python implementation.
"""

import math
import pytest
from BPTK_Py._rust_engine import RustSdEngine, RustSdModel, version
from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
from BPTK_Py.util import timerange
import json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_engine():
    """Create a fresh RustSdEngine."""
    return RustSdEngine()


def lit(value):
    """Shorthand for a literal expression node."""
    return {"type": "literal", "value": value}


def ref(name):
    """Shorthand for a reference expression node."""
    return {"type": "ref", "name": name}


def binop(op, left, right):
    """Shorthand for a binary-op expression node."""
    return {"type": "binary_op", "op": op, "left": left, "right": right}


def call(fn, args):
    """Shorthand for a function call expression node."""
    return {"type": "call", "function": fn, "args": args}


def build_json(name, specs, entities):
    """Build a model JSON string from components."""
    return json.dumps({"name": name, "specs": specs, "entities": entities})


# ---------------------------------------------------------------------------
# Basic smoke tests
# ---------------------------------------------------------------------------

class TestVersionAndImport:
    """Verify that the module loads and exposes the expected API."""

    def test_version_returns_string(self):
        v = version()
        assert isinstance(v, str)
        assert v == "0.1.0"

    def test_engine_creates(self):
        engine = make_engine()
        assert engine is not None

    def test_load_model_returns_model(self):
        engine = make_engine()
        model_json = build_json(
            "smoke",
            {"starttime": 0.0, "stoptime": 1.0, "dt": 1.0},
            {"constants": [{"name": "x", "equation": lit(1.0)}]},
        )
        model = engine.load_model(model_json)
        assert isinstance(model, RustSdModel)


# ---------------------------------------------------------------------------
# Constant model
# ---------------------------------------------------------------------------

class TestConstantModel:
    """A model with a single constant — simplest possible simulation."""

    def test_constant_value_at_all_timesteps(self):
        engine = make_engine()
        model_json = build_json(
            "constant",
            {"starttime": 0.0, "stoptime": 5.0, "dt": 1.0},
            {"constants": [{"name": "x", "equation": lit(42.0)}]},
        )
        model = engine.load_model(model_json)
        results = model.simulate(["x"])

        x = results["x"]
        assert len(x) == 6  # t = 0,1,2,3,4,5
        for t in range(6):
            assert x[f"{t:.1f}"] == 42.0


# ---------------------------------------------------------------------------
# Linear growth (stock + constant flow)
# ---------------------------------------------------------------------------

class TestLinearGrowth:
    """Stock with constant inflow: level(t) = 0 + 10*t."""

    def test_stock_increases_linearly(self):
        engine = make_engine()
        model_json = build_json(
            "linear",
            {"starttime": 0.0, "stoptime": 5.0, "dt": 1.0},
            {
                "stocks": [{
                    "name": "level",
                    "initial_value": lit(0.0),
                    "equation": ref("inflow"),
                }],
                "flows": [{
                    "name": "inflow",
                    "equation": lit(10.0),
                }],
            },
        )
        model = engine.load_model(model_json)
        results = model.simulate(["level", "inflow"])

        level = results["level"]
        for t in range(6):
            expected = 10.0 * t
            assert abs(level[f"{t:.1f}"] - expected) < 1e-10, f"t={t}"


# ---------------------------------------------------------------------------
# Exponential growth (stock with feedback)
# ---------------------------------------------------------------------------

class TestExponentialGrowth:
    """Stock grows by 10% each step: population(t+1) = population(t) * 1.1."""

    def test_exponential_population(self):
        engine = make_engine()
        model_json = build_json(
            "exponential",
            {"starttime": 0.0, "stoptime": 5.0, "dt": 1.0},
            {
                "stocks": [{
                    "name": "population",
                    "initial_value": lit(100.0),
                    "equation": ref("growth"),
                }],
                "flows": [{
                    "name": "growth",
                    "equation": binop("mul", ref("population"), lit(0.1)),
                }],
            },
        )
        model = engine.load_model(model_json)
        results = model.simulate(["population"])

        pop = results["population"]
        expected = 100.0
        for t in range(6):
            assert abs(pop[f"{t:.1f}"] - expected) < 1e-6, f"t={t}"
            expected *= 1.1


# ---------------------------------------------------------------------------
# SIR epidemic model
# ---------------------------------------------------------------------------

class TestSIRModel:
    """Classic SIR model — verifies multi-stock, multi-flow interaction."""

    def setup_method(self):
        engine = make_engine()
        model_json = build_json(
            "SIR",
            {"starttime": 0.0, "stoptime": 10.0, "dt": 1.0},
            {
                "stocks": [
                    {
                        "name": "susceptible",
                        "initial_value": lit(990.0),
                        "equation": {
                            "type": "unary_op", "op": "neg",
                            "operand": ref("infection"),
                        },
                    },
                    {
                        "name": "infected",
                        "initial_value": lit(10.0),
                        "equation": binop("sub", ref("infection"), ref("recovery")),
                    },
                    {
                        "name": "recovered",
                        "initial_value": lit(0.0),
                        "equation": ref("recovery"),
                    },
                ],
                "flows": [
                    {
                        "name": "infection",
                        "equation": binop(
                            "mul",
                            binop("mul", ref("contact_rate"), ref("transmission_prob")),
                            binop("mul", ref("susceptible"), ref("infected")),
                        ),
                    },
                    {
                        "name": "recovery",
                        "equation": binop("div", ref("infected"), ref("duration")),
                    },
                ],
                "constants": [
                    {"name": "contact_rate", "equation": lit(10.0)},
                    {"name": "transmission_prob", "equation": lit(0.001)},
                    {"name": "duration", "equation": lit(5.0)},
                ],
            },
        )
        model = engine.load_model(model_json)
        self.results = model.simulate(["susceptible", "infected", "recovered"])

    def test_initial_values(self):
        assert self.results["susceptible"]["0.0"] == 990.0
        assert self.results["infected"]["0.0"] == 10.0
        assert self.results["recovered"]["0.0"] == 0.0

    def test_population_conservation(self):
        """S + I + R should always equal 1000."""
        for t in range(11):
            t_str = f"{t:.1f}"
            total = (
                self.results["susceptible"][t_str]
                + self.results["infected"][t_str]
                + self.results["recovered"][t_str]
            )
            assert abs(total - 1000.0) < 1e-6, f"t={t}: S+I+R={total}"

    def test_infection_reduces_susceptible(self):
        assert self.results["susceptible"]["1.0"] < self.results["susceptible"]["0.0"]

    def test_recovered_increases(self):
        assert self.results["recovered"]["1.0"] > self.results["recovered"]["0.0"]


# ---------------------------------------------------------------------------
# set_constant — runtime parameter override
# ---------------------------------------------------------------------------

class TestSetConstant:
    """Override a constant's value after loading, then re-simulate."""

    def test_override_changes_results(self):
        engine = make_engine()
        model_json = build_json(
            "override",
            {"starttime": 0.0, "stoptime": 3.0, "dt": 1.0},
            {
                "stocks": [{
                    "name": "level",
                    "initial_value": lit(0.0),
                    "equation": ref("inflow"),
                }],
                "flows": [{
                    "name": "inflow",
                    "equation": ref("rate"),
                }],
                "constants": [
                    {"name": "rate", "equation": lit(10.0)},
                ],
            },
        )
        model = engine.load_model(model_json)

        # Original: rate=10, level(3) = 30
        r1 = model.simulate(["level"])
        assert abs(r1["level"]["3.0"] - 30.0) < 1e-10

        # Override: rate=20, level(3) = 60
        model.set_constant("rate", 20.0)
        r2 = model.simulate(["level"])
        assert abs(r2["level"]["3.0"] - 60.0) < 1e-10

    def test_set_constant_unknown_raises(self):
        engine = make_engine()
        model_json = build_json(
            "simple",
            {"starttime": 0.0, "stoptime": 1.0, "dt": 1.0},
            {"constants": [{"name": "x", "equation": lit(1.0)}]},
        )
        model = engine.load_model(model_json)
        with pytest.raises(ValueError, match="Unknown entity"):
            model.set_constant("nonexistent", 99.0)


# ---------------------------------------------------------------------------
# set_points — graphical function (lookup table) override
# ---------------------------------------------------------------------------

class TestSetPoints:
    """Override a graphical function's points after loading."""

    def _make_model_with_lookup(self):
        model_dict = {
            "name": "lookup_test",
            "specs": {"starttime": 0.0, "stoptime": 4.0, "dt": 1.0},
            "entities": {
                "converters": [{
                    "name": "output",
                    "equation": call("lookup", [
                        call("time", []),
                        {"type": "literal", "value": "my_table"},
                    ]),
                }],
            },
            "graphical_functions": {
                "my_table": {
                    "points": [[0.0, 0.0], [2.0, 10.0], [4.0, 20.0]],
                },
            },
        }
        return json.dumps(model_dict)

    def test_original_lookup(self):
        engine = make_engine()
        model = engine.load_model(self._make_model_with_lookup())
        results = model.simulate(["output"])

        # With original points: (0,0), (2,10), (4,20) — linear
        assert abs(results["output"]["0.0"] - 0.0) < 1e-10
        assert abs(results["output"]["1.0"] - 5.0) < 1e-10
        assert abs(results["output"]["2.0"] - 10.0) < 1e-10

    def test_override_points(self):
        engine = make_engine()
        model = engine.load_model(self._make_model_with_lookup())

        # Replace with constant lookup: always returns 99
        model.set_points("my_table", [(0.0, 99.0), (4.0, 99.0)])
        results = model.simulate(["output"])

        for t in range(5):
            t_str = f"{t:.1f}"
            assert abs(results["output"][t_str] - 99.0) < 1e-10, f"t={t_str}"

    def test_set_points_unknown_raises(self):
        engine = make_engine()
        model = engine.load_model(self._make_model_with_lookup())
        with pytest.raises(ValueError, match="Unknown graphical function"):
            model.set_points("nonexistent_table", [(0.0, 1.0)])


# ---------------------------------------------------------------------------
# Flow non-negativity
# ---------------------------------------------------------------------------

class TestFlowNonNegativity:
    """Flows are clamped to max(0, val) — negative flows become zero."""

    def test_negative_flow_clamped(self):
        engine = make_engine()
        model_json = build_json(
            "non_neg",
            {"starttime": 0.0, "stoptime": 3.0, "dt": 1.0},
            {
                "stocks": [{
                    "name": "level",
                    "initial_value": lit(100.0),
                    "equation": ref("outflow"),
                }],
                "flows": [{
                    "name": "outflow",
                    "equation": lit(-10.0),
                }],
            },
        )
        model = engine.load_model(model_json)
        results = model.simulate(["level", "outflow"])

        # Flow clamped to 0, stock stays at 100
        for t in range(4):
            t_str = f"{t:.1f}"
            assert results["outflow"][t_str] == 0.0
            assert results["level"][t_str] == 100.0


# ---------------------------------------------------------------------------
# Fractional dt
# ---------------------------------------------------------------------------

class TestFractionalDt:
    """Verify correct timestep count and values with dt < 1."""

    def test_dt_025(self):
        engine = make_engine()
        model_json = build_json(
            "frac_dt",
            {"starttime": 0.0, "stoptime": 2.0, "dt": 0.25},
            {
                "stocks": [{
                    "name": "level",
                    "initial_value": lit(0.0),
                    "equation": ref("inflow"),
                }],
                "flows": [{
                    "name": "inflow",
                    "equation": lit(10.0),
                }],
            },
        )
        model = engine.load_model(model_json)
        results = model.simulate(["level"])

        level = results["level"]
        assert len(level) == 9  # 0.0, 0.25, 0.5, ..., 2.0
        assert abs(level["0.0"] - 0.0) < 1e-10
        assert abs(level["0.5"] - 5.0) < 1e-10
        assert abs(level["1.0"] - 10.0) < 1e-10
        assert abs(level["2.0"] - 20.0) < 1e-10


# ---------------------------------------------------------------------------
# Non-zero start time
# ---------------------------------------------------------------------------

class TestNonZeroStartTime:
    """Simulation can start at t > 0."""

    def test_start_at_5(self):
        engine = make_engine()
        model_json = build_json(
            "nonzero_start",
            {"starttime": 5.0, "stoptime": 8.0, "dt": 1.0},
            {
                "stocks": [{
                    "name": "level",
                    "initial_value": lit(100.0),
                    "equation": ref("inflow"),
                }],
                "flows": [{
                    "name": "inflow",
                    "equation": lit(5.0),
                }],
            },
        )
        model = engine.load_model(model_json)
        results = model.simulate(["level"])

        level = results["level"]
        assert len(level) == 4  # t = 5, 6, 7, 8
        assert level["5.0"] == 100.0
        assert level["6.0"] == 105.0
        assert level["7.0"] == 110.0
        assert level["8.0"] == 115.0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Invalid inputs should raise clear Python exceptions."""

    def test_invalid_json_raises(self):
        engine = make_engine()
        with pytest.raises(ValueError):
            engine.load_model("not valid json")

    def test_unknown_entity_ref_raises(self):
        engine = make_engine()
        model_json = build_json(
            "bad_ref",
            {"starttime": 0.0, "stoptime": 1.0, "dt": 1.0},
            {
                "constants": [{
                    "name": "x",
                    "equation": ref("nonexistent"),
                }],
            },
        )
        with pytest.raises(ValueError):
            engine.load_model(model_json)


# ===========================================================================
# PARITY TESTS — Python SD DSL vs Rust engine
#
# Each test builds the same model in both engines and compares results.
# ===========================================================================

def _rust_time_key(t):
    """Format time value to match Rust engine's time key format."""
    if t == int(t):
        return f"{t:.1f}"
    else:
        return str(t)


def _if_expr(condition, then, else_):
    """Shorthand for an if expression node."""
    return {"type": "if", "condition": condition, "then": then, "else": else_}


def _unop(op, operand):
    """Shorthand for a unary-op expression node."""
    return {"type": "unary_op", "op": op, "operand": operand}


# ---------------------------------------------------------------------------
# Parity: Arithmetic operators
# ---------------------------------------------------------------------------

class TestParityArithmetic:
    """Compare all arithmetic operators between Python SD DSL and Rust."""

    def test_arithmetic_operators(self):
        starttime, stoptime, dt = 1.0, 10.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="arith_py")
        py_a = py.converter("a")
        py_b = py.converter("b")
        py_a.equation = sd.time()
        py_b.equation = 3.0

        py_add = py.converter("op_add")
        py_sub = py.converter("op_sub")
        py_mul = py.converter("op_mul")
        py_div = py.converter("op_div")
        py_pow = py.converter("op_pow")
        py_mod = py.converter("op_mod")

        py_add.equation = py_a + py_b
        py_sub.equation = py_a - py_b
        py_mul.equation = py_a * py_b
        py_div.equation = py_a / py_b
        py_pow.equation = py_a ** 2
        py_mod.equation = py_a % py_b

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "arith_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "a", "equation": call("time", [])},
                    {"name": "b", "equation": lit(3.0)},
                    {"name": "op_add", "equation": binop("add", ref("a"), ref("b"))},
                    {"name": "op_sub", "equation": binop("sub", ref("a"), ref("b"))},
                    {"name": "op_mul", "equation": binop("mul", ref("a"), ref("b"))},
                    {"name": "op_div", "equation": binop("div", ref("a"), ref("b"))},
                    {"name": "op_pow", "equation": binop("pow", ref("a"), lit(2.0))},
                    {"name": "op_mod", "equation": binop("mod", ref("a"), ref("b"))},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        equations = ["op_add", "op_sub", "op_mul", "op_div", "op_pow", "op_mod"]
        rust_results = rust_model.simulate(equations)

        py_elements = {
            "op_add": py_add, "op_sub": py_sub, "op_mul": py_mul,
            "op_div": py_div, "op_pow": py_pow, "op_mod": py_mod,
        }

        for eq_name in equations:
            for t in timerange(starttime, stoptime, dt):
                py_val = py_elements[eq_name](t)
                rust_val = rust_results[eq_name][_rust_time_key(t)]
                assert py_val == pytest.approx(rust_val, abs=1e-10), \
                    f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"


# ---------------------------------------------------------------------------
# Parity: Comparison operators with If
# ---------------------------------------------------------------------------

class TestParityComparisons:
    """Compare comparison operators (via If expressions) between engines."""

    def test_comparison_operators(self):
        starttime, stoptime, dt = 0.0, 10.0, 1.0

        # Python model: a = time(), compare against 5
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="cmp_py")
        py_a = py.converter("a")
        py_a.equation = sd.time()

        py_gt = py.converter("cmp_gt")
        py_lt = py.converter("cmp_lt")
        py_gte = py.converter("cmp_gte")
        py_lte = py.converter("cmp_lte")
        py_eq = py.converter("cmp_eq")
        py_neq = py.converter("cmp_neq")

        py_gt.equation = sd.If(py_a > 5, 1, 0)
        py_lt.equation = sd.If(py_a < 5, 1, 0)
        py_gte.equation = sd.If(py_a >= 5, 1, 0)
        py_lte.equation = sd.If(py_a <= 5, 1, 0)
        py_eq.equation = sd.If(py_a == 5, 1, 0)
        py_neq.equation = sd.If(py_a != 5, 1, 0)

        # Rust model
        engine = make_engine()
        a_expr = call("time", [])
        rust_json = json.dumps({
            "name": "cmp_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "a", "equation": a_expr},
                    {"name": "cmp_gt", "equation": _if_expr(
                        binop("gt", ref("a"), lit(5.0)), lit(1.0), lit(0.0))},
                    {"name": "cmp_lt", "equation": _if_expr(
                        binop("lt", ref("a"), lit(5.0)), lit(1.0), lit(0.0))},
                    {"name": "cmp_gte", "equation": _if_expr(
                        binop("gte", ref("a"), lit(5.0)), lit(1.0), lit(0.0))},
                    {"name": "cmp_lte", "equation": _if_expr(
                        binop("lte", ref("a"), lit(5.0)), lit(1.0), lit(0.0))},
                    {"name": "cmp_eq", "equation": _if_expr(
                        binop("eq", ref("a"), lit(5.0)), lit(1.0), lit(0.0))},
                    {"name": "cmp_neq", "equation": _if_expr(
                        binop("neq", ref("a"), lit(5.0)), lit(1.0), lit(0.0))},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        equations = ["cmp_gt", "cmp_lt", "cmp_gte", "cmp_lte", "cmp_eq", "cmp_neq"]
        rust_results = rust_model.simulate(equations)

        py_elements = {
            "cmp_gt": py_gt, "cmp_lt": py_lt, "cmp_gte": py_gte,
            "cmp_lte": py_lte, "cmp_eq": py_eq, "cmp_neq": py_neq,
        }

        for eq_name in equations:
            for t in timerange(starttime, stoptime, dt):
                py_val = py_elements[eq_name](t)
                rust_val = rust_results[eq_name][_rust_time_key(t)]
                assert py_val == pytest.approx(rust_val, abs=1e-10), \
                    f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"


# ---------------------------------------------------------------------------
# Parity: Logical operators (and, or, not)
# ---------------------------------------------------------------------------

class TestParityLogical:
    """Compare logical operators between engines."""

    def test_and_or_not(self):
        starttime, stoptime, dt = 0.0, 10.0, 1.0

        # Python model: two growing stocks, test and/or/not
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="logic_py")
        py_s1 = py.stock("stock1")
        py_s2 = py.stock("stock2")
        py_f1 = py.flow("inflow1")
        py_f2 = py.flow("inflow2")
        py_s1.initial_value = 1.0
        py_s2.initial_value = 1.0
        py_f1.equation = 1.0 * py_s1
        py_f2.equation = 2.0 * py_s2
        py_s1.equation = py_f1
        py_s2.equation = py_f2

        py_x = py.converter("x")
        py_y = py.converter("y")
        py_z = py.converter("z")
        py_x.equation = sd.If(sd.And(py_s1 > 4, py_s2 > 4), 1, 0)
        py_y.equation = sd.If(sd.Or(py_s1 > 4, py_s2 > 4), 1, 0)
        py_z.equation = sd.If(sd.Not(sd.And(py_s1 > 4, py_s2 > 4)), 1, 0)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "logic_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "stocks": [
                    {"name": "stock1", "initial_value": lit(1.0),
                     "equation": ref("inflow1")},
                    {"name": "stock2", "initial_value": lit(1.0),
                     "equation": ref("inflow2")},
                ],
                "flows": [
                    {"name": "inflow1", "equation": binop("mul", lit(1.0), ref("stock1"))},
                    {"name": "inflow2", "equation": binop("mul", lit(2.0), ref("stock2"))},
                ],
                "converters": [
                    {"name": "x", "equation": _if_expr(
                        binop("and",
                              binop("gt", ref("stock1"), lit(4.0)),
                              binop("gt", ref("stock2"), lit(4.0))),
                        lit(1.0), lit(0.0))},
                    {"name": "y", "equation": _if_expr(
                        binop("or",
                              binop("gt", ref("stock1"), lit(4.0)),
                              binop("gt", ref("stock2"), lit(4.0))),
                        lit(1.0), lit(0.0))},
                    {"name": "z", "equation": _if_expr(
                        _unop("not", binop("and",
                              binop("gt", ref("stock1"), lit(4.0)),
                              binop("gt", ref("stock2"), lit(4.0)))),
                        lit(1.0), lit(0.0))},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["x", "y", "z"])

        py_elements = {"x": py_x, "y": py_y, "z": py_z}

        for eq_name in ["x", "y", "z"]:
            for t in timerange(starttime, stoptime, dt):
                py_val = py_elements[eq_name](t)
                rust_val = rust_results[eq_name][_rust_time_key(t)]
                assert py_val == pytest.approx(rust_val, abs=1e-10), \
                    f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"


# ---------------------------------------------------------------------------
# Parity: Math functions
# ---------------------------------------------------------------------------

class TestParityMathFunctions:
    """Compare math functions between engines."""

    def test_abs_sqrt_exp(self):
        starttime, stoptime, dt = 0.0, 10.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="math_py")
        py_input = py.converter("input")
        py_input.equation = sd.time() - 5

        py_abs = py.converter("fn_abs")
        py_abs.equation = sd.abs(py_input)

        py_sqrt = py.converter("fn_sqrt")
        py_sqrt.equation = sd.sqrt(sd.time())

        py_exp = py.converter("fn_exp")
        py_exp.equation = sd.exp(sd.time() * 0.1)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "math_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "input", "equation": binop("sub", call("time", []), lit(5.0))},
                    {"name": "fn_abs", "equation": call("abs", [ref("input")])},
                    {"name": "fn_sqrt", "equation": call("sqrt", [call("time", [])])},
                    {"name": "fn_exp", "equation": call("exp", [
                        binop("mul", call("time", []), lit(0.1))])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        equations = ["fn_abs", "fn_sqrt", "fn_exp"]
        rust_results = rust_model.simulate(equations)

        py_elements = {"fn_abs": py_abs, "fn_sqrt": py_sqrt, "fn_exp": py_exp}

        for eq_name in equations:
            for t in timerange(starttime, stoptime, dt):
                py_val = py_elements[eq_name](t)
                rust_val = rust_results[eq_name][_rust_time_key(t)]
                assert py_val == pytest.approx(rust_val, abs=1e-10), \
                    f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"

    def test_trig_functions_as_converters(self):
        """Test sin/cos/tan/arctan as converters (no flow non-negativity)."""
        starttime, stoptime, dt = 0.0, 6.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="trig_py")
        py_sin = py.converter("fn_sin")
        py_cos = py.converter("fn_cos")
        py_arctan = py.converter("fn_arctan")

        py_sin.equation = sd.sin(sd.time())
        py_cos.equation = sd.cos(sd.time())
        py_arctan.equation = sd.arctan(sd.time())

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "trig_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "fn_sin", "equation": call("sin", [call("time", [])])},
                    {"name": "fn_cos", "equation": call("cos", [call("time", [])])},
                    {"name": "fn_arctan", "equation": call("arctan", [call("time", [])])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        equations = ["fn_sin", "fn_cos", "fn_arctan"]
        rust_results = rust_model.simulate(equations)

        # Compare against Python math directly (converters = no non-negativity)
        for t in timerange(starttime, stoptime, dt):
            key = _rust_time_key(t)
            assert rust_results["fn_sin"][key] == pytest.approx(math.sin(t), abs=1e-10)
            assert rust_results["fn_cos"][key] == pytest.approx(math.cos(t), abs=1e-10)
            assert rust_results["fn_arctan"][key] == pytest.approx(math.atan(t), abs=1e-10)

    def test_trig_as_flows_with_non_negativity(self):
        """Trig functions as flows get max(0, val) — matches Python SD DSL flows."""
        starttime, stoptime, dt = 0.0, 10.0, 0.5

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="trigflow_py")
        py_sin = py.flow("fn_sin")
        py_cos = py.flow("fn_cos")
        py_sin.equation = sd.sin(sd.time())
        py_cos.equation = sd.cos(sd.time())

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "trigflow_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "flows": [
                    {"name": "fn_sin", "equation": call("sin", [call("time", [])])},
                    {"name": "fn_cos", "equation": call("cos", [call("time", [])])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["fn_sin", "fn_cos"])

        # Both engines should apply max(0, val) since these are flows
        for t in timerange(starttime, stoptime, dt):
            key = _rust_time_key(t)
            py_sin_val = py_sin(t)
            py_cos_val = py_cos(t)
            assert py_sin_val == pytest.approx(rust_results["fn_sin"][key], abs=1e-10), \
                f"sin at t={t}: Python={py_sin_val}, Rust={rust_results['fn_sin'][key]}"
            assert py_cos_val == pytest.approx(rust_results["fn_cos"][key], abs=1e-10), \
                f"cos at t={t}: Python={py_cos_val}, Rust={rust_results['fn_cos'][key]}"


# ---------------------------------------------------------------------------
# Parity: Step function
# ---------------------------------------------------------------------------

class TestParityStep:
    """Compare step function between engines."""

    def test_step_function(self):
        starttime, stoptime, dt = 1.0, 10.0, 1.0
        step_height = 10.0
        step_timestep = 5.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="step_py")
        py_step = py.converter("step_val")
        py_step.equation = sd.step(step_height, step_timestep)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "step_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [{
                    "name": "step_val",
                    "equation": call("step", [lit(step_height), lit(step_timestep)]),
                }],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["step_val"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_step(t)
            rust_val = rust_results["step_val"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-10), \
                f"step at t={t}: Python={py_val}, Rust={rust_val}"


# ---------------------------------------------------------------------------
# Parity: Pulse function
# ---------------------------------------------------------------------------

class TestParityPulse:
    """Compare pulse function between engines."""

    def test_pulse_with_interval(self):
        starttime, stoptime, dt = 0.0, 9.0, 0.5
        volume = 9.0
        first_pulse = 1.5
        interval = 3.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="pulse_py")
        py_stock = py.stock("stock")
        py_stock.initial_value = 0.0
        py_flow = py.flow("flow")
        py_flow.equation = sd.pulse(py, volume, first_pulse, interval)
        py_stock.equation = py_flow

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "pulse_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "stocks": [{
                    "name": "stock",
                    "initial_value": lit(0.0),
                    "equation": ref("flow"),
                }],
                "flows": [{
                    "name": "flow",
                    "equation": call("pulse", [lit(volume), lit(first_pulse), lit(interval)]),
                }],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["stock", "flow"])

        for t in timerange(starttime, stoptime, dt):
            key = _rust_time_key(t)
            py_flow_val = py_flow(t)
            rust_flow_val = rust_results["flow"][key]
            assert py_flow_val == pytest.approx(rust_flow_val, abs=1e-10), \
                f"flow at t={t}: Python={py_flow_val}, Rust={rust_flow_val}"

            py_stock_val = py_stock(t)
            rust_stock_val = rust_results["stock"][key]
            assert py_stock_val == pytest.approx(rust_stock_val, abs=1e-10), \
                f"stock at t={t}: Python={py_stock_val}, Rust={rust_stock_val}"


# ---------------------------------------------------------------------------
# Parity: Lookup function
# ---------------------------------------------------------------------------

class TestParityLookup:
    """Compare lookup (graphical function) between engines."""

    def test_lookup_parity(self):
        starttime, stoptime, dt = 0.0, 10.0, 1.0
        points = [
            [0, 0.4], [0.25, 0.444], [0.5, 0.506], [0.75, 0.594],
            [1.0, 1.0], [1.25, 1.119], [1.5, 1.1625], [1.75, 1.2125],
            [2.0, 1.2375], [2.25, 1.245], [2.5, 1.25],
        ]

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="lookup_py")
        py.points["my_table"] = points
        py_input = py.converter("input")
        py_input.equation = sd.time() * 0.25  # ramps 0..2.5 over 0..10
        py_output = py.converter("output")
        py_output.equation = sd.lookup(py_input, "my_table")

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "lookup_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "input", "equation": binop("mul", call("time", []), lit(0.25))},
                    {"name": "output", "equation": call("lookup", [
                        ref("input"),
                        {"type": "literal", "value": "my_table"},
                    ])},
                ],
            },
            "graphical_functions": {
                "my_table": {"points": points},
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["output"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_output(t)
            rust_val = rust_results["output"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-10), \
                f"lookup at t={t}: Python={py_val}, Rust={rust_val}"


# ---------------------------------------------------------------------------
# Parity: Sinwave and Coswave
# ---------------------------------------------------------------------------

class TestParitySinwaveCoswave:
    """Compare sinwave/coswave between engines."""

    def test_sinwave_coswave_as_flows(self):
        """Sinwave/coswave as flows — both engines apply max(0, val)."""
        starttime, stoptime, dt = 0.0, 10.0, 0.5

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="wave_py")
        py_sinwave = py.flow("sinwave")
        py_coswave = py.flow("coswave")
        py_sinwave.equation = sd.sinwave(amplitude=2, period=4)
        py_coswave.equation = sd.coswave(amplitude=8, period=16)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "wave_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "flows": [
                    {"name": "sinwave", "equation": call("sinwave", [lit(2.0), lit(4.0)])},
                    {"name": "coswave", "equation": call("coswave", [lit(8.0), lit(16.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["sinwave", "coswave"])

        for t in timerange(starttime, stoptime, dt):
            key = _rust_time_key(t)
            py_sin = py_sinwave(t)
            py_cos = py_coswave(t)
            assert py_sin == pytest.approx(rust_results["sinwave"][key], abs=1e-10), \
                f"sinwave at t={t}: Python={py_sin}, Rust={rust_results['sinwave'][key]}"
            assert py_cos == pytest.approx(rust_results["coswave"][key], abs=1e-10), \
                f"coswave at t={t}: Python={py_cos}, Rust={rust_results['coswave'][key]}"


# ---------------------------------------------------------------------------
# Parity: SIR model (full comparison)
# ---------------------------------------------------------------------------

class TestParitySIR:
    """Full SIR model parity between Python SD DSL and Rust engine."""

    def test_sir_parity(self):
        starttime, stoptime, dt = 0.0, 40.0, 0.25

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="sir_py")
        py_s = py.stock("susceptible")
        py_i = py.stock("infected")
        py_r = py.stock("recovered")
        py_infection = py.flow("infection")
        py_recovery = py.flow("recovery")
        py_contact = py.constant("contact_rate")
        py_trans = py.constant("transmission_prob")
        py_dur = py.constant("duration")

        py_contact.equation = 10.0
        py_trans.equation = 0.001
        py_dur.equation = 5.0

        py_s.initial_value = 990.0
        py_i.initial_value = 10.0
        py_r.initial_value = 0.0

        py_infection.equation = py_contact * py_trans * py_s * py_i
        py_recovery.equation = py_i / py_dur

        py_s.equation = -py_infection
        py_i.equation = py_infection - py_recovery
        py_r.equation = py_recovery

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "sir_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "stocks": [
                    {"name": "susceptible", "initial_value": lit(990.0),
                     "equation": _unop("neg", ref("infection"))},
                    {"name": "infected", "initial_value": lit(10.0),
                     "equation": binop("sub", ref("infection"), ref("recovery"))},
                    {"name": "recovered", "initial_value": lit(0.0),
                     "equation": ref("recovery")},
                ],
                "flows": [
                    {"name": "infection", "equation": binop("mul",
                        binop("mul", ref("contact_rate"), ref("transmission_prob")),
                        binop("mul", ref("susceptible"), ref("infected")))},
                    {"name": "recovery", "equation": binop("div",
                        ref("infected"), ref("duration"))},
                ],
                "constants": [
                    {"name": "contact_rate", "equation": lit(10.0)},
                    {"name": "transmission_prob", "equation": lit(0.001)},
                    {"name": "duration", "equation": lit(5.0)},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        equations = ["susceptible", "infected", "recovered"]
        rust_results = rust_model.simulate(equations)

        py_elements = {
            "susceptible": py_s, "infected": py_i, "recovered": py_r,
        }

        for eq_name in equations:
            for t in timerange(starttime, stoptime, dt):
                py_val = py_elements[eq_name](t)
                rust_val = rust_results[eq_name][_rust_time_key(t)]
                assert py_val == pytest.approx(rust_val, abs=1e-6), \
                    f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"


# ---------------------------------------------------------------------------
# Parity: Smooth function
# ---------------------------------------------------------------------------

class TestParitySmooth:
    """Compare smooth function between Python SD DSL and Rust engine.

    Smooth is decomposed into internal stock + flow + converters.
    The serializer emits these as regular entities and the Smooth expression
    becomes a ref to the internal stock.
    """

    def test_smooth_step_input(self):
        """Smooth of a step input — exponential approach to step value."""
        starttime, stoptime, dt = 1.0, 10.0, 0.25

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="smooth_py")
        py_input = py.converter("input_function")
        py_input.equation = sd.step(10.0, 3.0)
        py_smooth = py.converter("smooth_out")
        py_smooth.equation = sd.smooth(py, py_input, 1.0, 0.0)

        # Rust model — manually construct the decomposed smooth entities
        # smooth = stock that tracks the exponential average
        # change_in_smooth = flow = (input - smooth) / averaging_time
        engine = make_engine()
        rust_json = json.dumps({
            "name": "smooth_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "stocks": [
                    {"name": "smooth_stock", "initial_value": lit(0.0),
                     "equation": ref("change_in_smooth")},
                ],
                "flows": [
                    {"name": "change_in_smooth", "equation":
                        binop("div",
                              binop("sub", ref("input_function"), ref("smooth_stock")),
                              ref("averaging_time"))},
                ],
                "converters": [
                    {"name": "input_function", "equation": call("step", [lit(10.0), lit(3.0)])},
                    {"name": "averaging_time", "equation": lit(1.0)},
                    {"name": "smooth_out", "equation": ref("smooth_stock")},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["smooth_out"])

        py_elements = {"smooth_out": py_smooth}
        for t in timerange(starttime, stoptime, dt):
            py_val = py_elements["smooth_out"](t)
            rust_val = rust_results["smooth_out"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-6), \
                f"smooth_out at t={t}: Python={py_val}, Rust={rust_val}"

    def test_smooth_ramp_input(self):
        """Smooth of a ramp input (time()) — smooth lags behind."""
        starttime, stoptime, dt = 0.0, 10.0, 0.25

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="smooth_ramp_py")
        py_input = py.converter("input_function")
        py_input.equation = sd.time()
        py_smooth = py.converter("smooth_out")
        py_smooth.equation = sd.smooth(py, py_input, 2.0, 0.0)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "smooth_ramp_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "stocks": [
                    {"name": "smooth_stock", "initial_value": lit(0.0),
                     "equation": ref("change_in_smooth")},
                ],
                "flows": [
                    {"name": "change_in_smooth", "equation":
                        binop("div",
                              binop("sub", ref("input_function"), ref("smooth_stock")),
                              ref("averaging_time"))},
                ],
                "converters": [
                    {"name": "input_function", "equation": call("time", [])},
                    {"name": "averaging_time", "equation": lit(2.0)},
                    {"name": "smooth_out", "equation": ref("smooth_stock")},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["smooth_out"])

        py_elements = {"smooth_out": py_smooth}
        for t in timerange(starttime, stoptime, dt):
            py_val = py_elements["smooth_out"](t)
            rust_val = rust_results["smooth_out"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-6), \
                f"smooth_out at t={t}: Python={py_val}, Rust={rust_val}"

    def test_smooth_already_smooth_input(self):
        """Smooth of a constant — output should equal input from the start."""
        starttime, stoptime, dt = 0.0, 5.0, 0.5

        engine = make_engine()
        rust_json = json.dumps({
            "name": "smooth_const",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "stocks": [
                    {"name": "smooth_stock", "initial_value": lit(42.0),
                     "equation": ref("change_in_smooth")},
                ],
                "flows": [
                    {"name": "change_in_smooth", "equation":
                        binop("div",
                              binop("sub", ref("input_function"), ref("smooth_stock")),
                              lit(1.0))},
                ],
                "converters": [
                    {"name": "input_function", "equation": lit(42.0)},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["smooth_stock"])

        # When input == initial_value, smooth should stay constant
        for t in timerange(starttime, stoptime, dt):
            assert rust_results["smooth_stock"][_rust_time_key(t)] == pytest.approx(42.0, abs=1e-10), \
                f"smooth_stock at t={t} should be 42.0"


# ---------------------------------------------------------------------------
# Parity: Trend function
# ---------------------------------------------------------------------------

class TestParityTrend:
    """Compare trend function between Python SD DSL and Rust engine.

    Trend is decomposed into: exponential_average (stock), change_in_average (flow),
    input_function (converter), averaging_time (converter), trend (converter).
    trend = (input - exp_avg) / (exp_avg * averaging_time)
    """

    def test_trend_step_input(self):
        """Trend of a step input."""
        starttime, stoptime, dt = 1.0, 10.0, 0.25

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="trend_py")
        py_input = py.converter("input_function")
        py_input.equation = sd.step(10.0, 3.0)
        py_trend = py.converter("trend_out")
        py_trend.equation = sd.trend(py, py_input, 2.0, 5.0)

        # Rust model — decomposed trend entities
        engine = make_engine()
        rust_json = json.dumps({
            "name": "trend_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "stocks": [
                    {"name": "exp_avg", "initial_value": lit(5.0),
                     "equation": ref("change_in_avg")},
                ],
                "flows": [
                    {"name": "change_in_avg", "equation":
                        binop("div",
                              binop("sub", ref("input_function"), ref("exp_avg")),
                              ref("averaging_time"))},
                ],
                "converters": [
                    {"name": "input_function", "equation": call("step", [lit(10.0), lit(3.0)])},
                    {"name": "averaging_time", "equation": lit(2.0)},
                    {"name": "trend_out", "equation":
                        binop("div",
                              binop("sub", ref("input_function"), ref("exp_avg")),
                              binop("mul", ref("exp_avg"), ref("averaging_time")))},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["trend_out"])

        py_elements = {"trend_out": py_trend}
        for t in timerange(starttime, stoptime, dt):
            py_val = py_elements["trend_out"](t)
            rust_val = rust_results["trend_out"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-6), \
                f"trend_out at t={t}: Python={py_val}, Rust={rust_val}"

    def test_trend_linear_input(self):
        """Trend of linear input (time()) — should converge to a positive trend."""
        starttime, stoptime, dt = 1.0, 10.0, 0.25

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="trend_lin_py")
        py_input = py.converter("input_function")
        py_input.equation = sd.time()
        py_trend = py.converter("trend_out")
        py_trend.equation = sd.trend(py, py_input, 1.0, 1.0)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "trend_lin_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "stocks": [
                    {"name": "exp_avg", "initial_value": lit(1.0),
                     "equation": ref("change_in_avg")},
                ],
                "flows": [
                    {"name": "change_in_avg", "equation":
                        binop("div",
                              binop("sub", ref("input_function"), ref("exp_avg")),
                              ref("averaging_time"))},
                ],
                "converters": [
                    {"name": "input_function", "equation": call("time", [])},
                    {"name": "averaging_time", "equation": lit(1.0)},
                    {"name": "trend_out", "equation":
                        binop("div",
                              binop("sub", ref("input_function"), ref("exp_avg")),
                              binop("mul", ref("exp_avg"), ref("averaging_time")))},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["trend_out"])

        py_elements = {"trend_out": py_trend}
        for t in timerange(starttime, stoptime, dt):
            py_val = py_elements["trend_out"](t)
            rust_val = rust_results["trend_out"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-6), \
                f"trend_out at t={t}: Python={py_val}, Rust={rust_val}"


# ---------------------------------------------------------------------------
# Parity: Delay function
# ---------------------------------------------------------------------------

class TestParityDelay:
    """Compare delay function between Python SD DSL and Rust engine.

    Delay uses memo-table lookback: delay(input, duration, initial_value).
    """

    def test_delay_time_input(self):
        """Delay of time() by 3 steps — b(t) = t-3 for t >= 3, else 0."""
        starttime, stoptime, dt = 0.0, 10.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="delay_py")
        py_a = py.converter("a")
        py_b = py.converter("b")
        py_a.equation = sd.time()
        py_b.equation = sd.delay(py, py_a, 3.0, 0.0)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "delay_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "a", "equation": call("time", [])},
                    {"name": "b", "equation": call("delay", [ref("a"), lit(3.0), lit(0.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["a", "b"])

        py_elements = {"a": py_a, "b": py_b}
        for eq_name in ["a", "b"]:
            for t in timerange(starttime, stoptime, dt):
                py_val = py_elements[eq_name](t)
                rust_val = rust_results[eq_name][_rust_time_key(t)]
                assert py_val == pytest.approx(rust_val, abs=1e-10), \
                    f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"

    def test_delay_fractional_dt(self):
        """Delay with dt=0.5 and delay_duration=2.0 — lookback of 4 steps."""
        starttime, stoptime, dt = 0.0, 8.0, 0.5

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="delay_frac_py")
        py_a = py.converter("a")
        py_b = py.converter("b")
        py_a.equation = sd.time()
        py_b.equation = sd.delay(py, py_a, 2.0, -1.0)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "delay_frac_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "a", "equation": call("time", [])},
                    {"name": "b", "equation": call("delay", [ref("a"), lit(2.0), lit(-1.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["b"])

        py_elements = {"b": py_b}
        for t in timerange(starttime, stoptime, dt):
            py_val = py_elements["b"](t)
            rust_val = rust_results["b"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-10), \
                f"b at t={t}: Python={py_val}, Rust={rust_val}"

    def test_delay_zero_duration(self):
        """Delay with duration=0 — should return current value."""
        starttime, stoptime, dt = 0.0, 5.0, 1.0

        engine = make_engine()
        rust_json = json.dumps({
            "name": "delay_zero",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "a", "equation": call("time", [])},
                    {"name": "b", "equation": call("delay", [ref("a"), lit(0.0), lit(0.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["a", "b"])

        # With delay=0, b should equal a at every step
        for t in timerange(starttime, stoptime, dt):
            t_str = _rust_time_key(t)
            assert rust_results["b"][t_str] == pytest.approx(rust_results["a"][t_str], abs=1e-10), \
                f"delay(0) at t={t}: b should equal a"

    def test_delay_step_input(self):
        """Delay of a step function — step appears delayed."""
        starttime, stoptime, dt = 0.0, 10.0, 0.5

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="delay_step_py")
        py_input = py.converter("input")
        py_delayed = py.converter("delayed")
        py_input.equation = sd.step(5.0, 3.0)
        py_delayed.equation = sd.delay(py, py_input, 2.0, 0.0)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "delay_step_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "input", "equation": call("step", [lit(5.0), lit(3.0)])},
                    {"name": "delayed", "equation": call("delay", [ref("input"), lit(2.0), lit(0.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["delayed"])

        py_elements = {"delayed": py_delayed}
        for t in timerange(starttime, stoptime, dt):
            py_val = py_elements["delayed"](t)
            rust_val = rust_results["delayed"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-10), \
                f"delayed at t={t}: Python={py_val}, Rust={rust_val}"

    def test_delay_with_stock(self):
        """Delay reading from a stock — tests interaction with Euler integration."""
        starttime, stoptime, dt = 0.0, 10.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="delay_stock_py")
        py_level = py.stock("level")
        py_inflow = py.flow("inflow")
        py_delayed = py.converter("delayed_level")
        py_level.initial_value = 0.0
        py_level.equation = py_inflow
        py_inflow.equation = 5.0
        py_delayed.equation = sd.delay(py, py_level, 3.0, 0.0)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "delay_stock_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "stocks": [
                    {"name": "level", "initial_value": lit(0.0),
                     "equation": ref("inflow")},
                ],
                "flows": [
                    {"name": "inflow", "equation": lit(5.0)},
                ],
                "converters": [
                    {"name": "delayed_level", "equation":
                        call("delay", [ref("level"), lit(3.0), lit(0.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["level", "delayed_level"])

        py_elements = {"level": py_level, "delayed_level": py_delayed}
        for eq_name in ["level", "delayed_level"]:
            for t in timerange(starttime, stoptime, dt):
                py_val = py_elements[eq_name](t)
                rust_val = rust_results[eq_name][_rust_time_key(t)]
                assert py_val == pytest.approx(rust_val, abs=1e-10), \
                    f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"


# ---------------------------------------------------------------------------
# Parity: Biflow (no non-negativity clamping)
# ---------------------------------------------------------------------------

class TestParityBiflow:
    """Compare biflow behavior between Python SD DSL and Rust engine.

    Biflows are like flows but skip non-negativity clamping, allowing
    negative values.
    """

    def test_biflow_oscillator(self):
        """Oscillator model: position stock + velocity biflow."""
        starttime, stoptime, dt = 0.0, 10.0, 0.25

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="biflow_py")
        py_pos = py.stock("position")
        py_vel = py.biflow("velocity")
        py_pos.initial_value = 10.0
        py_pos.equation = py_vel
        py_vel.equation = -py_pos

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "biflow_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "stocks": [
                    {"name": "position", "initial_value": lit(10.0),
                     "equation": ref("velocity")},
                ],
                "biflows": [
                    {"name": "velocity", "equation": _unop("neg", ref("position"))},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["position", "velocity"])

        py_elements = {"position": py_pos, "velocity": py_vel}
        for eq_name in ["position", "velocity"]:
            for t in timerange(starttime, stoptime, dt):
                py_val = py_elements[eq_name](t)
                rust_val = rust_results[eq_name][_rust_time_key(t)]
                assert py_val == pytest.approx(rust_val, abs=1e-10), \
                    f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"

    def test_biflow_goes_negative(self):
        """Biflow values can go negative — unlike regular flows."""
        engine = make_engine()
        rust_json = json.dumps({
            "name": "biflow_neg",
            "specs": {"starttime": 0.0, "stoptime": 3.0, "dt": 1.0},
            "entities": {
                "stocks": [
                    {"name": "level", "initial_value": lit(100.0),
                     "equation": ref("bf")},
                ],
                "biflows": [
                    {"name": "bf", "equation": lit(-10.0)},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        results = rust_model.simulate(["bf", "level"])

        # Biflow should be -10 (not clamped to 0)
        for t in range(4):
            t_str = f"{t:.1f}"
            assert results["bf"][t_str] == -10.0
        # Stock should decrease
        assert results["level"]["0.0"] == 100.0
        assert results["level"]["1.0"] == 90.0
        assert results["level"]["2.0"] == 80.0
        assert results["level"]["3.0"] == 70.0

    def test_flow_still_clamped(self):
        """Regular flows remain clamped to 0 — biflow doesn't break this."""
        engine = make_engine()
        rust_json = json.dumps({
            "name": "flow_vs_biflow",
            "specs": {"starttime": 0.0, "stoptime": 3.0, "dt": 1.0},
            "entities": {
                "stocks": [
                    {"name": "stock_flow", "initial_value": lit(100.0),
                     "equation": ref("regular_flow")},
                    {"name": "stock_biflow", "initial_value": lit(100.0),
                     "equation": ref("bi_flow")},
                ],
                "flows": [
                    {"name": "regular_flow", "equation": lit(-10.0)},
                ],
                "biflows": [
                    {"name": "bi_flow", "equation": lit(-10.0)},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        results = rust_model.simulate(["regular_flow", "bi_flow", "stock_flow", "stock_biflow"])

        # Regular flow clamped to 0
        assert results["regular_flow"]["0.0"] == 0.0
        assert results["stock_flow"]["3.0"] == 100.0  # unchanged

        # Biflow not clamped
        assert results["bi_flow"]["0.0"] == -10.0
        assert results["stock_biflow"]["3.0"] == 70.0  # decreased

    def test_biflow_spring_mass(self):
        """Two-stock spring-mass oscillator — classic biflow use case."""
        starttime, stoptime, dt = 0.0, 10.0, 0.25

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="spring_py")
        py_pos = py.stock("position")
        py_vel = py.stock("velocity")
        py_dp = py.biflow("change_in_position")
        py_dv = py.biflow("change_in_velocity")

        py_pos.initial_value = 1.0
        py_vel.initial_value = 0.0
        py_pos.equation = py_dp
        py_vel.equation = py_dv
        py_dp.equation = py_vel
        py_dv.equation = -py_pos

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "spring_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "stocks": [
                    {"name": "position", "initial_value": lit(1.0),
                     "equation": ref("change_in_position")},
                    {"name": "velocity", "initial_value": lit(0.0),
                     "equation": ref("change_in_velocity")},
                ],
                "biflows": [
                    {"name": "change_in_position", "equation": ref("velocity")},
                    {"name": "change_in_velocity", "equation":
                        _unop("neg", ref("position"))},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["position", "velocity"])

        py_elements = {"position": py_pos, "velocity": py_vel}
        for eq_name in ["position", "velocity"]:
            for t in timerange(starttime, stoptime, dt):
                py_val = py_elements[eq_name](t)
                rust_val = rust_results[eq_name][_rust_time_key(t)]
                assert py_val == pytest.approx(rust_val, abs=1e-6), \
                    f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"


# ---------------------------------------------------------------------------
# Parity: ln, log10, floor, ceil
# ---------------------------------------------------------------------------

class TestParityLnLog10FloorCeil:
    """Compare ln, log10, floor, ceil between Python and Rust engines."""

    def test_ln_log10(self):
        starttime, stoptime, dt = 1.0, 10.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="log_py")
        py_input = py.converter("input")
        py_input.equation = sd.time()

        py_ln = py.converter("fn_ln")
        py_ln.equation = sd.ln(py_input)

        py_log10 = py.converter("fn_log10")
        py_log10.equation = sd.log10(py_input)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "log_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "input", "equation": call("time", [])},
                    {"name": "fn_ln", "equation": call("ln", [ref("input")])},
                    {"name": "fn_log10", "equation": call("log10", [ref("input")])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        equations = ["fn_ln", "fn_log10"]
        rust_results = rust_model.simulate(equations)

        py_elements = {"fn_ln": py_ln, "fn_log10": py_log10}
        for eq_name in equations:
            for t in timerange(starttime, stoptime, dt):
                py_val = py_elements[eq_name](t)
                rust_val = rust_results[eq_name][_rust_time_key(t)]
                assert py_val == pytest.approx(rust_val, abs=1e-10), \
                    f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"

    def test_floor_ceil(self):
        starttime, stoptime, dt = 0.0, 5.0, 1.0

        # Python model — use time * 1.7 to get fractional values
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="fc_py")
        py_input = py.converter("input")
        py_input.equation = sd.time() * 1.7 - 3.0

        py_floor = py.converter("fn_floor")
        py_floor.equation = sd.floor(py_input)

        py_ceil = py.converter("fn_ceil")
        py_ceil.equation = sd.ceil(py_input)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "fc_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "input", "equation": binop("sub",
                        binop("mul", call("time", []), lit(1.7)), lit(3.0))},
                    {"name": "fn_floor", "equation": call("floor", [ref("input")])},
                    {"name": "fn_ceil", "equation": call("ceil", [ref("input")])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        equations = ["fn_floor", "fn_ceil"]
        rust_results = rust_model.simulate(equations)

        py_elements = {"fn_floor": py_floor, "fn_ceil": py_ceil}
        for eq_name in equations:
            for t in timerange(starttime, stoptime, dt):
                py_val = py_elements[eq_name](t)
                rust_val = rust_results[eq_name][_rust_time_key(t)]
                assert py_val == pytest.approx(rust_val, abs=1e-10), \
                    f"{eq_name} at t={t}: Python={py_val}, Rust={rust_val}"

    def test_ln_exp_composition(self):
        """Verify ln(exp(x)) ≈ x in both engines."""
        starttime, stoptime, dt = 0.0, 5.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="comp_py")
        py_out = py.converter("roundtrip")
        py_out.equation = sd.ln(sd.exp(sd.time()))

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "comp_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "roundtrip", "equation":
                        call("ln", [call("exp", [call("time", [])])])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["roundtrip"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_out(t)
            rust_val = rust_results["roundtrip"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-10), \
                f"roundtrip at t={t}: Python={py_val}, Rust={rust_val}"
            assert py_val == pytest.approx(t, abs=1e-10), \
                f"ln(exp({t})) should equal {t}, got {py_val}"


# ---------------------------------------------------------------------------
# Parity: Combinatorial & special functions
# ---------------------------------------------------------------------------

class TestParityCombinatorialFunctions:
    """Compare combinatorial and special functions between Python and Rust engines."""

    def test_factorial(self):
        starttime, stoptime, dt = 0.0, 5.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="fact_py")
        py_out = py.converter("x")
        py_out.equation = sd.factorial(sd.time())

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "fact_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("factorial", [call("time", [])])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["x"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_out(t)
            rust_val = rust_results["x"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-6), \
                f"factorial at t={t}: Python={py_val}, Rust={rust_val}"

    def test_factorial_zero(self):
        """factorial(0) = 1."""
        engine = make_engine()
        rust_json = json.dumps({
            "name": "fact0",
            "specs": {"starttime": 0, "stoptime": 1, "dt": 1},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("factorial", [lit(0.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        result = rust_model.simulate(["x"])
        assert result["x"]["0.0"] == pytest.approx(1.0, abs=1e-10)

    def test_combinations(self):
        starttime, stoptime, dt = 0.0, 1.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="comb_py")
        py_out = py.converter("x")
        py_out.equation = sd.combinations(10, 3)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "comb_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("combinations", [lit(10.0), lit(3.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["x"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_out(t)
            rust_val = rust_results["x"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-6), \
                f"combinations at t={t}: Python={py_val}, Rust={rust_val}"

    def test_combinations_edge(self):
        """combinations(5, 0) = 1."""
        engine = make_engine()
        rust_json = json.dumps({
            "name": "comb0",
            "specs": {"starttime": 0, "stoptime": 1, "dt": 1},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("combinations", [lit(5.0), lit(0.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        result = rust_model.simulate(["x"])
        assert result["x"]["0.0"] == pytest.approx(1.0, abs=1e-6)

    def test_permutations(self):
        starttime, stoptime, dt = 0.0, 1.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="perm_py")
        py_out = py.converter("x")
        py_out.equation = sd.permutations(5, 2)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "perm_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("permutations", [lit(5.0), lit(2.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["x"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_out(t)
            rust_val = rust_results["x"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-6), \
                f"permutations at t={t}: Python={py_val}, Rust={rust_val}"

    def test_gammaln(self):
        starttime, stoptime, dt = 1.0, 5.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="gln_py")
        py_out = py.converter("x")
        py_out.equation = sd.gammaln(sd.time())

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "gln_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("gammaln", [call("time", [])])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["x"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_out(t)
            rust_val = rust_results["x"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-10), \
                f"gammaln at t={t}: Python={py_val}, Rust={rust_val}"

    def test_gammaln_one(self):
        """gammaln(1) = 0."""
        engine = make_engine()
        rust_json = json.dumps({
            "name": "gln1",
            "specs": {"starttime": 0, "stoptime": 1, "dt": 1},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("gammaln", [lit(1.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        result = rust_model.simulate(["x"])
        assert result["x"]["0.0"] == pytest.approx(0.0, abs=1e-10)


# ---------------------------------------------------------------------------
# Parity: Inf and Nan
# ---------------------------------------------------------------------------

class TestParityInfNan:
    """Compare Inf and Nan between Python and Rust engines."""

    def test_inf(self):
        starttime, stoptime, dt = 0.0, 1.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="inf_py")
        py_out = py.converter("x")
        py_out.equation = sd.Inf()

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "inf_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("inf", [])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["x"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_out(t)
            rust_val = rust_results["x"][_rust_time_key(t)]
            assert py_val == rust_val == float('inf'), \
                f"inf at t={t}: Python={py_val}, Rust={rust_val}"

    def test_nan(self):
        starttime, stoptime, dt = 0.0, 1.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="nan_py")
        py_out = py.converter("x")
        py_out.equation = sd.nan()

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "nan_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("nan", [])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["x"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_out(t)
            rust_val = rust_results["x"][_rust_time_key(t)]
            assert math.isnan(py_val), f"Python nan at t={t}: {py_val}"
            assert math.isnan(rust_val), f"Rust nan at t={t}: {rust_val}"

    def test_inf_in_expression(self):
        """Inf used in a min() expression: min(value, Inf()) = value."""
        starttime, stoptime, dt = 0.0, 5.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="inf_expr_py")
        py_out = py.converter("x")
        py_out.equation = sd.min(sd.time(), sd.Inf())

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "inf_expr_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("min", [
                        call("time", []), call("inf", [])])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["x"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_out(t)
            rust_val = rust_results["x"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-10), \
                f"min(t, inf) at t={t}: Python={py_val}, Rust={rust_val}"
            assert py_val == pytest.approx(t, abs=1e-10)


# ---------------------------------------------------------------------------
# Parity: Inline lookup points
# ---------------------------------------------------------------------------

class TestParityInlineLookup:
    """Compare inline lookup points between Python and Rust engines."""

    def test_inline_lookup(self):
        starttime, stoptime, dt = 0.0, 10.0, 0.5

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="inline_py")
        py_input = py.converter("input")
        py_input.equation = sd.time() * 0.5

        py_out = py.converter("output")
        py_out.equation = sd.lookup(py_input, [(0, 0), (1, 2), (2, 6), (3, 4), (5, 10)])

        # Rust model — inline points become a named table
        engine = make_engine()
        rust_json = json.dumps({
            "name": "inline_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "input", "equation": binop("mul", call("time", []), lit(0.5))},
                    {"name": "output", "equation": call("lookup", [
                        ref("input"), {"type": "literal", "value": "_test_table"}])},
                ],
            },
            "graphical_functions": {
                "_test_table": {"points": [[0, 0], [1, 2], [2, 6], [3, 4], [5, 10]]},
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["input", "output"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_out(t)
            rust_val = rust_results["output"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-10), \
                f"inline lookup at t={t}: Python={py_val}, Rust={rust_val}"

    def test_inline_lookup_boundary(self):
        """Input outside point range — both engines clamp."""
        starttime, stoptime, dt = 0.0, 10.0, 1.0

        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="bound_py")
        py_input = py.converter("input")
        py_input.equation = sd.time() - 2.0

        py_out = py.converter("output")
        py_out.equation = sd.lookup(py_input, [(0, 0), (5, 10)])

        engine = make_engine()
        rust_json = json.dumps({
            "name": "bound_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "input", "equation": binop("sub", call("time", []), lit(2.0))},
                    {"name": "output", "equation": call("lookup", [
                        ref("input"), {"type": "literal", "value": "_bound_table"}])},
                ],
            },
            "graphical_functions": {
                "_bound_table": {"points": [[0, 0], [5, 10]]},
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["output"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_out(t)
            rust_val = rust_results["output"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-10), \
                f"boundary lookup at t={t}: Python={py_val}, Rust={rust_val}"


# ---------------------------------------------------------------------------
# Parity: Round with digits
# ---------------------------------------------------------------------------

class TestParityRoundDigits:
    """Compare round(x, digits) between Python and Rust engines."""

    def test_round_with_digits(self):
        starttime, stoptime, dt = 0.0, 5.0, 1.0

        # Python model
        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="rnd_py")
        py_out = py.converter("x")
        py_out.equation = sd.round(sd.time() * 0.314159, 2)

        # Rust model
        engine = make_engine()
        rust_json = json.dumps({
            "name": "rnd_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("round", [
                        binop("mul", call("time", []), lit(0.314159)), lit(2.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["x"])

        for t in timerange(starttime, stoptime, dt):
            py_val = py_out(t)
            rust_val = rust_results["x"][_rust_time_key(t)]
            assert py_val == pytest.approx(rust_val, abs=1e-10), \
                f"round at t={t}: Python={py_val}, Rust={rust_val}"

    def test_round_zero_digits(self):
        """round(3.7, 0) = 4.0."""
        engine = make_engine()
        rust_json = json.dumps({
            "name": "rnd0",
            "specs": {"starttime": 0, "stoptime": 1, "dt": 1},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("round", [lit(3.7), lit(0.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        result = rust_model.simulate(["x"])
        assert result["x"]["0.0"] == pytest.approx(4.0, abs=1e-10)


# ---------------------------------------------------------------------------
# Parity: Statistical functions (deterministic)
# ---------------------------------------------------------------------------

class TestParityStatisticalDeterministic:
    """Compare deterministic statistical functions between Python and Rust engines."""

    def test_invnorm_standard(self):
        """invnorm(0.975, 0, 1) ≈ 1.96."""
        starttime, stoptime, dt = 0.0, 1.0, 1.0

        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="invnorm_py")
        py_out = py.converter("x")
        py_out.equation = sd.invnorm(0.975, 0, 1)

        engine = make_engine()
        rust_json = json.dumps({
            "name": "invnorm_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("invnorm", [lit(0.975), lit(0.0), lit(1.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["x"])

        py_val = py_out(0.0)
        rust_val = rust_results["x"]["0.0"]
        assert py_val == pytest.approx(rust_val, abs=1e-6), \
            f"invnorm: Python={py_val}, Rust={rust_val}"
        assert py_val == pytest.approx(1.96, abs=0.01)

    def test_invnorm_custom(self):
        """invnorm(0.5, 100, 15) = 100 (median of normal)."""
        engine = make_engine()
        rust_json = json.dumps({
            "name": "invnorm_custom",
            "specs": {"starttime": 0, "stoptime": 1, "dt": 1},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("invnorm", [lit(0.5), lit(100.0), lit(15.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        result = rust_model.simulate(["x"])
        assert result["x"]["0.0"] == pytest.approx(100.0, abs=1e-6)

    def test_normalcdf(self):
        """normalcdf(-1, 1, 0, 1) ≈ 0.6827 (68-95-99.7 rule)."""
        starttime, stoptime, dt = 0.0, 1.0, 1.0

        py = Model(starttime=starttime, stoptime=stoptime, dt=dt, name="ncdf_py")
        py_out = py.converter("x")
        py_out.equation = sd.normalcdf(-1, 1, 0, 1)

        engine = make_engine()
        rust_json = json.dumps({
            "name": "ncdf_rust",
            "specs": {"starttime": starttime, "stoptime": stoptime, "dt": dt},
            "entities": {
                "converters": [
                    {"name": "x", "equation": call("normalcdf",
                        [lit(-1.0), lit(1.0), lit(0.0), lit(1.0)])},
                ],
            },
        })
        rust_model = engine.load_model(rust_json)
        rust_results = rust_model.simulate(["x"])

        py_val = py_out(0.0)
        rust_val = rust_results["x"]["0.0"]
        assert py_val == pytest.approx(rust_val, abs=1e-6), \
            f"normalcdf: Python={py_val}, Rust={rust_val}"
        assert py_val == pytest.approx(0.6827, abs=0.001)
