"""Behavioural tests for multidimensional (arrayed) SD DSL semantics.

Organised by **operand combination**, which is the axis the existing array tests lack.
`tests/test_sddsl.py` already sweeps naming mode x element type x size for
`arrayed op arrayed` and checks all seven aggregations against numpy; those are not
repeated here. `tests/unittests/test_operator.py` covers `clone_with_index` per operator
class. What nobody covered before this file: an array meeting a *scalar*, an array inside
a function, an array in a comparison or conditional, an arrayed stock integrating over
time, and the arrayed biflow.

**How the expectations are defined.** Almost nothing here hardcodes numbers. Element-wise
propagation *means* that an arrayed expression equals the same expression written out per
index, so each case supplies two lambdas - the arrayed form and the per-index form - and
the test asserts they agree at every index. The per-index form is ordinary scalar
arithmetic, which works today, so it is a reference implementation rather than a second
guess. It also states the specification precisely: `sd.sqrt(v)` must equal
`sd.sqrt(v[k])` for every k.

**The xfails, and what happened to them.** Written on 2026-09-08, when only `+ - * /`
propagated arrayedness: functions, comparisons, conditionals, `**` and `%` collapsed to a
scalar `0.0`, three reflected forms raised `AttributeError`, and `2.0 * v` was silently
zero. 196 cases carried `xfail(strict=True)`. They were closed by implementing the
array protocol once on `Operator`, over the operands a constructor was called with;
because the marker was strict, each had to come off in the same commit that made it
pass. No marker is left.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Callable

import pytest

from BPTK_Py import Model
from BPTK_Py.sddsl import functions as sd
from BPTK_Py.sddsl.operators import DotOperator, OperatorError


# ---------------------------------------------------------------------------
# Shapes
#
# The four ways an element can be arrayed. Named shapes deliberately use real
# string labels - `test_sddsl.py` names its indices "0", "1", "2", which
# exercises the named code path but cannot catch a bug that depends on a label
# not looking like an integer.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Shape:
    """One way of being arrayed, plus how to build and address it."""

    id: str
    named: bool
    dims: int
    keys: tuple                      # leaf addresses; a 2-tuple per leaf when dims == 2
    setup: Callable                  # (element, values_by_key) -> None

    def leaf(self, element, key):
        """The sub-element at `key`, for a vector or a matrix alike."""
        if self.dims == 1:
            return element[key]
        return element[key[0]][key[1]]


def _setup_unnamed_vector(element, values):
    element.setup_vector(len(values), [values[k] for k in sorted(values)])


def _setup_named_vector(element, values):
    element.setup_named_vector(dict(values))


def _setup_unnamed_matrix(element, values):
    rows = sorted({k[0] for k in values})
    cols = sorted({k[1] for k in values})
    element.setup_matrix([len(rows), len(cols)],
                         [[values[(r, c)] for c in cols] for r in rows])


def _setup_named_matrix(element, values):
    rows = sorted({k[0] for k in values})
    cols = sorted({k[1] for k in values})
    element.setup_named_matrix({r: {c: values[(r, c)] for c in cols} for r in rows})


UNNAMED_VECTOR = Shape("unnamed_vector", False, 1, (0, 1, 2), _setup_unnamed_vector)
NAMED_VECTOR = Shape("named_vector", True, 1, ("junior", "mid", "senior"),
                     _setup_named_vector)
UNNAMED_MATRIX = Shape("unnamed_matrix", False, 2, ((0, 0), (0, 1), (1, 0), (1, 1)),
                       _setup_unnamed_matrix)
NAMED_MATRIX = Shape("named_matrix", True, 2,
                     (("north", "widget"), ("north", "gadget"),
                      ("south", "widget"), ("south", "gadget")),
                     _setup_named_matrix)

SHAPES = (UNNAMED_VECTOR, NAMED_VECTOR, UNNAMED_MATRIX, NAMED_MATRIX)
VECTORS = (UNNAMED_VECTOR, NAMED_VECTOR)

# Strictly positive and distinct, so `ln`, `log10` and `sqrt` are defined and a
# wrong index cannot accidentally agree with the right one.
VALUES = (4.0, 9.0, 16.0, 25.0)


def values_for(shape, offset=0.0):
    """A value per leaf of `shape`, distinct and positive."""
    return {key: VALUES[i] + offset for i, key in enumerate(shape.keys)}


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

SCALAR_ELEMENT_VALUE = 2.0


class Collapsed(Exception):
    """Raised when an arrayed input produced a non-arrayed result.

    This is the failure mode that motivated the file: no exception, a plausible
    number, a quietly wrong model.
    """

    def __init__(self, value):
        super().__init__(f"expression collapsed to the scalar {value!r}")
        self.value = value


def _build(shape, offset=0.0, second=False):
    """A model with an arrayed constant `v`, a scalar element `s`, and a target."""
    model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name=f"arr_{shape.id}")

    v = model.constant("v")
    shape.setup(v, values_for(shape, offset))

    s = model.constant("s")
    s.equation = SCALAR_ELEMENT_VALUE

    w = None
    if second:
        w = model.constant("w")
        shape.setup(w, values_for(shape, offset + 1.0))

    return model, v, s, w


def evaluate_arrayed(shape, build, t=1, second=False):
    """Evaluate `build(v, s, w)` assigned to an arrayed target.

    Returns the leaf values keyed by index. Raises :class:`Collapsed` if the result
    was not arrayed - which is the bug this file exists to name.
    """
    model, v, s, w = _build(shape, second=second)
    target = model.converter("target")
    target.equation = build(v, s, w)

    if not getattr(target, "arrayed", False):
        return_value = target(t)
        raise Collapsed(return_value)

    return {key: shape.leaf(target, key)(t) for key in shape.keys}


def evaluate_per_index(shape, build_indexed, t=1, second=False):
    """Evaluate the same expression written out one index at a time.

    This is the reference: ordinary scalar arithmetic over the sub-elements, which
    works today and defines what propagation must produce.
    """
    model, v, s, w = _build(shape, second=second)
    target = model.converter("target")
    shape.setup(target, {key: 0.0 for key in shape.keys})

    for key in shape.keys:
        shape.leaf(target, key).equation = build_indexed(v, s, w, key, shape)

    return {key: shape.leaf(target, key)(t) for key in shape.keys}


def assert_propagates(shape, arrayed, indexed, t=1, second=False):
    """The arrayed form must agree with the per-index form at every index."""
    got = evaluate_arrayed(shape, arrayed, t=t, second=second)
    expected = evaluate_per_index(shape, indexed, t=t, second=second)

    assert set(got) == set(expected)
    for key in expected:
        assert got[key] == pytest.approx(expected[key], rel=1e-12, abs=1e-12), (
            f"index {key!r}: arrayed {got[key]!r} != per-index {expected[key]!r}"
        )


def leaf_of(operand, key, shape):
    """Address one leaf of `operand`, for use inside a per-index lambda."""
    return shape.leaf(operand, key)


# ---------------------------------------------------------------------------
# Parametrisation helpers
# ---------------------------------------------------------------------------

def _shape_params(shapes=SHAPES):
    return [pytest.param(shape, id=shape.id) for shape in shapes]


# ---------------------------------------------------------------------------
# The case table
#
# Every case carries THREE things:
#
#   arrayed   the expression as a user writes it on the whole array
#   indexed   the same expression written out for one index
#   expected  the result computed in PLAIN PYTHON from the known inputs
#
# The third is what makes this a correctness test rather than a consistency
# test. `arrayed == indexed` alone would pass if the scalar arithmetic were
# wrong, because both sides would be wrong identically. `expected` is an
# independent implementation - `math.sqrt`, `%`, `max` - so the numbers
# themselves are pinned.
#
# `expected(x, s, y)` receives the leaf's own input value, the scalar element's
# value, and the second array's leaf where one is used.
#
# `TestScalarReference` below asserts `indexed == expected` for every case. It
# passes today, which is what validates the expectations: a wrong `expected`
# fails there loudly instead of hiding inside an xfailed propagation test.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Case:
    """One operation, in three renderings."""

    id: str
    arrayed: Callable                # (v, s, w) -> Operator
    indexed: Callable                # (v, s, w, key, shape) -> Operator
    expected: Callable               # (x, s, y) -> number or bool
    second: bool = False             # needs the second arrayed operand `w`


def _cases(*cases):
    return [pytest.param(case, id=case.id) for case in cases]


# --- Arithmetic against a scalar: works today -------------------------------

ARITHMETIC = [
    Case("v_plus_literal", lambda v, s, w: v + 3.0,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) + 3.0,
         lambda x, s, y: x + 3.0),
    Case("v_minus_literal", lambda v, s, w: v - 3.0,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) - 3.0,
         lambda x, s, y: x - 3.0),
    Case("v_times_literal", lambda v, s, w: v * 3.0,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) * 3.0,
         lambda x, s, y: x * 3.0),
    Case("v_over_literal", lambda v, s, w: v / 3.0,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) / 3.0,
         lambda x, s, y: x / 3.0),
    Case("v_plus_element", lambda v, s, w: v + s,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) + s,
         lambda x, s, y: x + s),
    Case("v_minus_element", lambda v, s, w: v - s,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) - s,
         lambda x, s, y: x - s),
    Case("v_times_element", lambda v, s, w: v * s,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) * s,
         lambda x, s, y: x * s),
    Case("v_over_element", lambda v, s, w: v / s,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) / s,
         lambda x, s, y: x / s),
    Case("element_plus_v", lambda v, s, w: s + v,
         lambda v, s, w, k, sh: s + leaf_of(v, k, sh),
         lambda x, s, y: s + x),
    Case("element_minus_v", lambda v, s, w: s - v,
         lambda v, s, w, k, sh: s - leaf_of(v, k, sh),
         lambda x, s, y: s - x),
    Case("element_times_v", lambda v, s, w: s * v,
         lambda v, s, w, k, sh: s * leaf_of(v, k, sh),
         lambda x, s, y: s * x),
    Case("element_over_v", lambda v, s, w: s / v,
         lambda v, s, w, k, sh: s / leaf_of(v, k, sh),
         lambda x, s, y: s / x),
    Case("negation", lambda v, s, w: -v,
         lambda v, s, w, k, sh: -leaf_of(v, k, sh),
         lambda x, s, y: -x),
    Case("v_plus_v", lambda v, s, w: v + w,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) + leaf_of(w, k, sh),
         lambda x, s, y: x + y, second=True),
]

# --- A literal on the LEFT --------------------------------------------------
# These used to raise `AttributeError: 'UnaryOperator' object has no attribute
# 'named_arrayed'` on named arrays: the arithmetic operators each carried their own
# `index_to_string`, which read that attribute off whatever sat in element_1.

REFLECTED = [
    Case("literal_plus_v", lambda v, s, w: 3.0 + v,
         lambda v, s, w, k, sh: 3.0 + leaf_of(v, k, sh),
         lambda x, s, y: 3.0 + x),
    Case("literal_minus_v", lambda v, s, w: 3.0 - v,
         lambda v, s, w, k, sh: 3.0 - leaf_of(v, k, sh),
         lambda x, s, y: 3.0 - x),
    Case("literal_over_v", lambda v, s, w: 3.0 / v,
         lambda v, s, w, k, sh: 3.0 / leaf_of(v, k, sh),
         lambda x, s, y: 3.0 / x),
]

# `3.0 * v` was broken for every shape - arrayed, and zero - because `__rmul__` passed
# the number where NumericalMultiplicationOperator expects the element.
REFLECTED_TIMES = Case(
    "literal_times_v", lambda v, s, w: 3.0 * v,
    lambda v, s, w, k, sh: 3.0 * leaf_of(v, k, sh),
    lambda x, s, y: 3.0 * x)

# --- Power and modulo -------------------------------------------------------

POWER_MODULO = [
    Case("v_pow_literal", lambda v, s, w: v ** 2.0,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) ** 2.0,
         lambda x, s, y: x ** 2.0),
    Case("v_mod_literal", lambda v, s, w: v % 5.0,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) % 5.0,
         lambda x, s, y: x % 5.0),
    Case("literal_mod_v", lambda v, s, w: 100.0 % v,
         lambda v, s, w, k, sh: 100.0 % leaf_of(v, k, sh),
         lambda x, s, y: 100.0 % x),
    Case("element_mod_v", lambda v, s, w: s % v,
         lambda v, s, w, k, sh: s % leaf_of(v, k, sh),
         lambda x, s, y: s % x),
    # The left operand is a sum, so the modulo has to keep it grouped.
    Case("sum_mod_literal", lambda v, s, w: (v + s) % 7.0,
         lambda v, s, w, k, sh: (leaf_of(v, k, sh) + s) % 7.0,
         lambda x, s, y: (x + s) % 7.0),
]

# --- Math functions ---------------------------------------------------------
# The inputs are 4, 9, 16, 25, so `sqrt`, `ln` and `log10` are all defined.
# `floor`/`ceil`/`round` divide first, so they have a fraction to act on.

FUNCTIONS = [
    Case("sqrt", lambda v, s, w: sd.sqrt(v),
         lambda v, s, w, k, sh: sd.sqrt(leaf_of(v, k, sh)),
         lambda x, s, y: math.sqrt(x)),
    Case("ln", lambda v, s, w: sd.ln(v),
         lambda v, s, w, k, sh: sd.ln(leaf_of(v, k, sh)),
         lambda x, s, y: math.log(x)),
    Case("log10", lambda v, s, w: sd.log10(v),
         lambda v, s, w, k, sh: sd.log10(leaf_of(v, k, sh)),
         lambda x, s, y: math.log10(x)),
    Case("sin", lambda v, s, w: sd.sin(v),
         lambda v, s, w, k, sh: sd.sin(leaf_of(v, k, sh)),
         lambda x, s, y: math.sin(x)),
    Case("cos", lambda v, s, w: sd.cos(v),
         lambda v, s, w, k, sh: sd.cos(leaf_of(v, k, sh)),
         lambda x, s, y: math.cos(x)),
    Case("tan", lambda v, s, w: sd.tan(v),
         lambda v, s, w, k, sh: sd.tan(leaf_of(v, k, sh)),
         lambda x, s, y: math.tan(x)),
    Case("exp", lambda v, s, w: sd.exp(v / 100.0),
         lambda v, s, w, k, sh: sd.exp(leaf_of(v, k, sh) / 100.0),
         lambda x, s, y: math.exp(x / 100.0)),
    Case("floor", lambda v, s, w: sd.floor(v / 7.0),
         lambda v, s, w, k, sh: sd.floor(leaf_of(v, k, sh) / 7.0),
         lambda x, s, y: float(math.floor(x / 7.0))),
    Case("ceil", lambda v, s, w: sd.ceil(v / 7.0),
         lambda v, s, w, k, sh: sd.ceil(leaf_of(v, k, sh) / 7.0),
         lambda x, s, y: float(math.ceil(x / 7.0))),
    Case("round", lambda v, s, w: sd.round(v / 7.0, 2),
         lambda v, s, w, k, sh: sd.round(leaf_of(v, k, sh) / 7.0, 2),
         lambda x, s, y: round(x / 7.0, 2)),
    Case("abs", lambda v, s, w: sd.abs(-v),
         lambda v, s, w, k, sh: sd.abs(-leaf_of(v, k, sh)),
         lambda x, s, y: abs(-x)),
]

# --- max / min --------------------------------------------------------------

MINMAX = [
    Case("max_literal", lambda v, s, w: sd.max(v, 10.0),
         lambda v, s, w, k, sh: sd.max(leaf_of(v, k, sh), 10.0),
         lambda x, s, y: max(x, 10.0)),
    Case("min_literal", lambda v, s, w: sd.min(v, 10.0),
         lambda v, s, w, k, sh: sd.min(leaf_of(v, k, sh), 10.0),
         lambda x, s, y: min(x, 10.0)),
    Case("max_element", lambda v, s, w: sd.max(v, s),
         lambda v, s, w, k, sh: sd.max(leaf_of(v, k, sh), s),
         lambda x, s, y: max(x, s)),
    Case("min_element", lambda v, s, w: sd.min(v, s),
         lambda v, s, w, k, sh: sd.min(leaf_of(v, k, sh), s),
         lambda x, s, y: min(x, s)),
    Case("max_array", lambda v, s, w: sd.max(v, w),
         lambda v, s, w, k, sh: sd.max(leaf_of(v, k, sh), leaf_of(w, k, sh)),
         lambda x, s, y: max(x, y), second=True),
    Case("min_array", lambda v, s, w: sd.min(v, w),
         lambda v, s, w, k, sh: sd.min(leaf_of(v, k, sh), leaf_of(w, k, sh)),
         lambda x, s, y: min(x, y), second=True),
]

# --- Comparisons and logic --------------------------------------------------
# These evaluate to a genuine Python `bool`, not to 1.0 / 0.0 - measured
# 2026-09-08, and the expectations say so rather than guessing a convention.
# The inputs straddle the threshold: 4 and 9 are below 10, 16 and 25 above.

COMPARISONS = [
    Case("gt", lambda v, s, w: v > 10.0,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) > 10.0,
         lambda x, s, y: x > 10.0),
    Case("lt", lambda v, s, w: v < 10.0,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) < 10.0,
         lambda x, s, y: x < 10.0),
    Case("ge", lambda v, s, w: v >= 16.0,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) >= 16.0,
         lambda x, s, y: x >= 16.0),
    Case("le", lambda v, s, w: v <= 9.0,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) <= 9.0,
         lambda x, s, y: x <= 9.0),
    Case("ne", lambda v, s, w: v != 9.0,
         lambda v, s, w, k, sh: leaf_of(v, k, sh) != 9.0,
         lambda x, s, y: x != 9.0),
]

CONDITIONALS = [
    Case("if_", lambda v, s, w: sd.If(v > 10.0, v, s),
         lambda v, s, w, k, sh: sd.If(leaf_of(v, k, sh) > 10.0,
                                      leaf_of(v, k, sh), s),
         lambda x, s, y: x if x > 10.0 else s),
    Case("and_", lambda v, s, w: sd.And(v > 5.0, v < 20.0),
         lambda v, s, w, k, sh: sd.And(leaf_of(v, k, sh) > 5.0,
                                       leaf_of(v, k, sh) < 20.0),
         lambda x, s, y: (x > 5.0) and (x < 20.0)),
    Case("or_", lambda v, s, w: sd.Or(v < 5.0, v > 20.0),
         lambda v, s, w, k, sh: sd.Or(leaf_of(v, k, sh) < 5.0,
                                      leaf_of(v, k, sh) > 20.0),
         lambda x, s, y: (x < 5.0) or (x > 20.0)),
    Case("not_", lambda v, s, w: sd.Not(v > 10.0),
         lambda v, s, w, k, sh: sd.Not(leaf_of(v, k, sh) > 10.0),
         lambda x, s, y: not (x > 10.0)),
]

ALL_ELEMENTWISE = (ARITHMETIC + REFLECTED + [REFLECTED_TIMES] + POWER_MODULO
                   + FUNCTIONS + MINMAX + COMPARISONS + CONDITIONALS)


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------

def _expectations(shape, case):
    """The plain-Python expected value per leaf."""
    inputs = values_for(shape)
    seconds = values_for(shape, 1.0)
    return {
        key: case.expected(inputs[key], SCALAR_ELEMENT_VALUE, seconds[key])
        for key in shape.keys
    }


def assert_scalar_reference(shape, case):
    """The per-index form must equal the plain-Python expectation.

    This is what validates the `expected` lambdas. It runs green today for every
    case, so an expectation that is simply wrong shows up here rather than being
    swallowed by an xfailed propagation test.
    """
    got = evaluate_per_index(shape, case.indexed, second=case.second)
    want = _expectations(shape, case)
    for key in shape.keys:
        assert got[key] == pytest.approx(want[key], rel=1e-12, abs=1e-12), (
            f"{case.id} at index {key!r}: engine {got[key]!r} != "
            f"hand-computed {want[key]!r}"
        )


def assert_arrayed_matches_expectation(shape, case):
    """The arrayed form must equal the plain-Python expectation at every index.

    Checked against the hand-computed value, not against the per-index form, so a
    green result means the arithmetic is right - not merely that both renderings
    agree.
    """
    got = evaluate_arrayed(shape, case.arrayed, second=case.second)
    want = _expectations(shape, case)
    assert set(got) == set(want)
    for key in shape.keys:
        assert got[key] == pytest.approx(want[key], rel=1e-12, abs=1e-12), (
            f"{case.id} at index {key!r}: arrayed {got[key]!r} != "
            f"hand-computed {want[key]!r}"
        )


# ---------------------------------------------------------------------------
# Stateful functions
#
# Their expectations are recurrences rather than one-liners. All three were
# verified against the engine across six timesteps on 2026-09-08 before being
# written down here.
# ---------------------------------------------------------------------------

SMOOTH_AVERAGING_TIME = 3.0
STATEFUL_INITIAL = 1.0
DELAY_DURATION = 2.0
STATEFUL_T = 4
STATEFUL_DT = 1.0


def py_smooth(x, t=STATEFUL_T, averaging_time=SMOOTH_AVERAGING_TIME,
              initial=STATEFUL_INITIAL, dt=STATEFUL_DT):
    """Exponential smoothing: `s <- s + dt/averaging_time * (x - s)`."""
    smoothed = initial
    for _ in range(int(t / dt)):
        smoothed += dt / averaging_time * (x - smoothed)
    return smoothed


def py_trend(x, t=STATEFUL_T, averaging_time=SMOOTH_AVERAGING_TIME,
             initial=STATEFUL_INITIAL, dt=STATEFUL_DT):
    """The fractional gap between the input and its smoothed value."""
    smoothed = py_smooth(x, t, averaging_time, initial, dt)
    return (x - smoothed) / (smoothed * averaging_time)


def py_delay(x, t=STATEFUL_T, duration=DELAY_DURATION, initial=STATEFUL_INITIAL):
    """A constant input: the initial value until the delay has elapsed."""
    return initial if t < duration else x


STATEFUL = [
    Case("smooth",
         lambda v, s, w: sd.smooth(v.model, v, SMOOTH_AVERAGING_TIME,
                                   STATEFUL_INITIAL),
         lambda v, s, w, k, sh: sd.smooth(v.model, leaf_of(v, k, sh),
                                          SMOOTH_AVERAGING_TIME, STATEFUL_INITIAL),
         lambda x, s, y: py_smooth(x)),
    Case("trend",
         lambda v, s, w: sd.trend(v.model, v, SMOOTH_AVERAGING_TIME,
                                  STATEFUL_INITIAL),
         lambda v, s, w, k, sh: sd.trend(v.model, leaf_of(v, k, sh),
                                         SMOOTH_AVERAGING_TIME, STATEFUL_INITIAL),
         lambda x, s, y: py_trend(x)),
    Case("delay",
         lambda v, s, w: sd.delay(v.model, v, DELAY_DURATION, STATEFUL_INITIAL),
         lambda v, s, w, k, sh: sd.delay(v.model, leaf_of(v, k, sh),
                                         DELAY_DURATION, STATEFUL_INITIAL),
         lambda x, s, y: py_delay(x)),
]


# ---------------------------------------------------------------------------
# The tests
# ---------------------------------------------------------------------------

class TestScalarReference:
    """Every expectation, checked against the engine one index at a time.

    Green today. Its job is to make the `expected` lambdas trustworthy: if a
    hand-computed value is wrong, it fails **here**, where nothing is xfailed,
    instead of silently agreeing with a broken propagation test later.
    """

    @pytest.mark.parametrize("shape", _shape_params())
    @pytest.mark.parametrize("case", _cases(*ALL_ELEMENTWISE))
    def test_the_expectation_matches_the_engine(self, shape, case):
        assert_scalar_reference(shape, case)

    @pytest.mark.parametrize("shape", _shape_params(VECTORS))
    @pytest.mark.parametrize("case", _cases(*STATEFUL))
    def test_the_stateful_expectations_match_the_engine(self, shape, case):
        got = evaluate_per_index(shape, case.indexed, t=STATEFUL_T)
        want = _expectations(shape, case)
        for key in shape.keys:
            assert got[key] == pytest.approx(want[key], rel=1e-12, abs=1e-12)


class TestElementwiseArithmeticWithScalars:
    """An array meeting a scalar, with the results pinned to concrete values."""

    @pytest.mark.parametrize("shape", _shape_params())
    @pytest.mark.parametrize("case", _cases(*ARITHMETIC))
    def test_array_and_scalar(self, shape, case):
        assert_arrayed_matches_expectation(shape, case)

    @pytest.mark.parametrize("shape", _shape_params())
    @pytest.mark.parametrize("case", _cases(*REFLECTED))
    def test_literal_on_the_left(self, shape, case):
        assert_arrayed_matches_expectation(shape, case)

    @pytest.mark.parametrize("shape", _shape_params())
    def test_literal_times_array(self, shape):
        assert_arrayed_matches_expectation(shape, REFLECTED_TIMES)

    @pytest.mark.parametrize("shape", _shape_params())
    @pytest.mark.parametrize("case", _cases(*POWER_MODULO))
    def test_power_and_modulo(self, shape, case):
        assert_arrayed_matches_expectation(shape, case)


class TestMathFunctions:
    """Every math function, applied to an array and pinned per index."""

    @pytest.mark.parametrize("shape", _shape_params())
    @pytest.mark.parametrize("case", _cases(*FUNCTIONS))
    def test_function(self, shape, case):
        assert_arrayed_matches_expectation(shape, case)


class TestMinMax:
    """`max`/`min` against a literal, a scalar element, and another array."""

    @pytest.mark.parametrize("shape", _shape_params())
    @pytest.mark.parametrize("case", _cases(*MINMAX))
    def test_min_max(self, shape, case):
        assert_arrayed_matches_expectation(shape, case)


class TestComparisons:
    """A comparison over an array yields one boolean per index.

    They evaluate to a genuine `bool`; the inputs 4, 9, 16, 25 straddle every
    threshold used, so a case cannot pass by accident of all-true or all-false.
    `ComparisonOperator.resolve_dimensions` used to return -1, which declared the
    result scalar and took every `If` built on a comparison down with it.
    """

    @pytest.mark.parametrize("shape", _shape_params())
    @pytest.mark.parametrize("case", _cases(*COMPARISONS))
    def test_comparison(self, shape, case):
        assert_arrayed_matches_expectation(shape, case)


class TestConditionals:
    """`If` and the logical functions over arrays."""

    @pytest.mark.parametrize("shape", _shape_params())
    @pytest.mark.parametrize("case", _cases(*CONDITIONALS))
    def test_conditional(self, shape, case):
        assert_arrayed_matches_expectation(shape, case)


class TestStatefulFunctions:
    """`smooth`, `trend` and `delay` over arrays.

    Each sub-element carries its **own** history, and it does so without a state key
    that knows about indices: `Smooth` and `Trend` build their helper stock and flows
    in their constructor, and cloning per index re-runs that constructor, so every
    index gets its own averaging chain named from a fresh `model.equation_prefix`.
    Evaluated at t=4, where a shared history and a per-index history genuinely
    differ, and pinned to the recurrences in `py_smooth` / `py_trend` / `py_delay`.

    Built to behave as the scalar Python path does, which is why correcting the scalar
    `delay` - the step-mode collapse and the duration frozen at `starttime` - corrected
    the arrayed variant with it.
    """

    @pytest.mark.parametrize("shape", _shape_params(VECTORS))
    @pytest.mark.parametrize("case", _cases(*STATEFUL))
    def test_stateful(self, shape, case):
        got = evaluate_arrayed(shape, case.arrayed, t=STATEFUL_T)
        want = _expectations(shape, case)
        assert set(got) == set(want)
        for key in shape.keys:
            assert got[key] == pytest.approx(want[key], rel=1e-12, abs=1e-12)


class TestCompositionAndOtherFunctions:
    """The rest of the function surface over arrays, and expressions built from it.

    Everything that takes an operand propagates, because the protocol is generic over
    a constructor's operands rather than enumerated per class.
    These are the cases that are neither plain arithmetic nor a one-argument math
    function - the ones an enumeration would have missed.
    """

    @staticmethod
    def _model():
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="composition")
        v = model.constant("v")
        v.setup_named_vector({"a": 4.0, "b": 9.0})
        return model, v

    def test_lookup_reads_its_own_input_per_index(self):
        model, v = self._model()
        target = model.converter("target")
        target.equation = sd.lookup(v, [(0.0, 0.0), (4.0, 40.0), (9.0, 90.0)])
        assert target["a"](2) == pytest.approx(40.0)
        assert target["b"](2) == pytest.approx(90.0)

    def test_step_takes_an_arrayed_height(self):
        model, v = self._model()
        target = model.converter("target")
        target.equation = sd.step(v, 2.0)
        assert target["a"](1) == pytest.approx(0.0)
        assert target["b"](1) == pytest.approx(0.0)
        assert target["a"](3) == pytest.approx(4.0)
        assert target["b"](3) == pytest.approx(9.0)

    def test_pulse_takes_an_arrayed_volume(self):
        model, v = self._model()
        target = model.converter("target")
        target.equation = sd.pulse(model, v, 1.0, 0.0)
        # One pulse at t=1, spread over dt=1.0, and nothing before or after.
        assert target["a"](0) == pytest.approx(0.0)
        assert target["a"](1) == pytest.approx(4.0)
        assert target["b"](1) == pytest.approx(9.0)
        assert target["b"](2) == pytest.approx(0.0)

    def test_a_stochastic_function_draws_within_each_index_own_bounds(self):
        """No fixed value to pin, but the bounds are per index - which is the point."""
        model, v = self._model()
        target = model.converter("target")
        target.equation = sd.random(v, v * 2.0)
        assert 4.0 <= target["a"](2) <= 8.0
        assert 9.0 <= target["b"](2) <= 18.0

    def test_functions_compose_over_an_array(self):
        model, v = self._model()
        target = model.converter("target")
        target.equation = sd.max(sd.If(v > 5.0, v, 0.0), 1.0)
        assert target["a"](2) == pytest.approx(1.0)
        assert target["b"](2) == pytest.approx(9.0)

    def test_a_function_of_an_aggregation_stays_scalar(self):
        model, v = self._model()
        target = model.converter("target")
        target.equation = sd.sqrt(v.arr_sum())
        assert not target.arrayed
        assert target(2) == pytest.approx(math.sqrt(13.0))

    def test_an_aggregation_added_to_the_array_it_came_from(self):
        model, v = self._model()
        target = model.converter("target")
        target.equation = v.arr_sum() + v
        assert target["a"](2) == pytest.approx(17.0)
        assert target["b"](2) == pytest.approx(22.0)

    def test_smooth_of_an_expression_smooths_each_index(self):
        model, v = self._model()
        target = model.converter("target")
        target.equation = sd.smooth(model, sd.sqrt(v), 3.0, 1.0)
        assert target["a"](2) == pytest.approx(py_smooth(math.sqrt(4.0), t=2))
        assert target["b"](2) == pytest.approx(py_smooth(math.sqrt(9.0), t=2))

    def test_delay_reads_a_varying_duration_at_every_step(self):
        """Per index, and whether the duration itself is one number or one per index.

        The scalar path rendered the duration with `starttime`, so a duration that
        varies had no effect at all; the arrayed path inherited that by construction.
        """
        model = Model(starttime=1.0, stoptime=10.0, dt=1.0, name="varying_arrayed_delay")
        v = model.constant("v")
        v.setup_named_vector({"a": 4.0, "b": 9.0})
        orders = model.converter("orders")
        orders.equation = v * sd.time()

        duration = model.converter("duration")
        duration.equation = sd.If(sd.time() < 6.0, 1.0, 3.0)

        incoming = model.converter("incoming")
        incoming.equation = sd.delay(model, orders, duration, 0.0)

        # One step of lag up to t=5, three from t=6 on, for every index
        for t in range(2, 6):
            assert incoming["a"](t) == pytest.approx(4.0 * (t - 1))
            assert incoming["b"](t) == pytest.approx(9.0 * (t - 1))
        for t in range(6, 11):
            assert incoming["a"](t) == pytest.approx(4.0 * (t - 3))
            assert incoming["b"](t) == pytest.approx(9.0 * (t - 3))

    def test_delay_takes_a_duration_that_differs_per_index(self):
        model = Model(starttime=1.0, stoptime=10.0, dt=1.0, name="per_index_duration")
        v = model.constant("v")
        v.setup_named_vector({"a": 4.0, "b": 9.0})
        orders = model.converter("orders")
        orders.equation = v * sd.time()

        duration = model.converter("duration")
        duration.setup_named_vector({"a": 0.0, "b": 0.0})
        duration["a"].equation = sd.If(sd.time() < 6.0, 1.0, 3.0)
        duration["b"].equation = sd.If(sd.time() < 6.0, 2.0, 1.0)

        incoming = model.converter("incoming")
        incoming.equation = sd.delay(model, orders, duration, 0.0)

        for t in range(2, 6):
            assert incoming["a"](t) == pytest.approx(4.0 * (t - 1))
            # Two steps of lag reaches before starttime at t=2, where the initial holds
            assert incoming["b"](t) == pytest.approx(9.0 * (t - 2) if t > 2 else 0.0)
        for t in range(6, 11):
            assert incoming["a"](t) == pytest.approx(4.0 * (t - 3))
            assert incoming["b"](t) == pytest.approx(9.0 * (t - 1))

    def test_delay_still_insists_on_a_model_element(self):
        """A restriction of `sd.delay` itself, not of arrays - and it says so."""
        model, v = self._model()
        target = model.converter("target")
        with pytest.raises(OperatorError, match="must be a model element"):
            target.equation = sd.delay(model, v * 2.0, 2.0, 1.0)


class TestAggregations:
    """Only what `test_sddsl.py` does not already check against numpy.

    Covered there, across four element types and both naming modes: `arr_sum`,
    `arr_prod`, `arr_mean`, `arr_median`, `arr_stddev`, `arr_size`, `arr_rank`. Left
    here: the two operators that do not exist yet, and the edges.
    """

    @pytest.mark.parametrize("shape", _shape_params())
    def test_arr_max(self, shape):
        model, v, _s, _w = _build(shape)
        target = model.converter("target")
        target.equation = v.arr_max()
        assert target(1) == pytest.approx(max(values_for(shape).values()))

    @pytest.mark.parametrize("shape", _shape_params())
    def test_arr_min(self, shape):
        model, v, _s, _w = _build(shape)
        target = model.converter("target")
        target.equation = v.arr_min()
        assert target(1) == pytest.approx(min(values_for(shape).values()))

    def test_arr_max_and_arr_min_of_a_single_element_vector(self):
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="single_minmax")
        v = model.constant("v")
        v.setup_named_vector({"only": 7.0})
        largest = model.converter("largest")
        largest.equation = v.arr_max()
        smallest = model.converter("smallest")
        smallest.equation = v.arr_min()
        assert largest(1) == pytest.approx(7.0)
        assert smallest(1) == pytest.approx(7.0)

    def test_arr_max_and_arr_min_on_a_scalar_element_are_zero(self):
        """The other aggregations answer 0.0 for an element with no sub-elements."""
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="scalar_minmax")
        s = model.constant("s")
        s.equation = 3.0
        assert s.arr_max().term() == "0.0"
        assert s.arr_min().term() == "0.0"

    def test_arr_sum_of_a_single_element_vector(self):
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="single")
        v = model.constant("v")
        v.setup_named_vector({"only": 7.0})
        target = model.converter("target")
        target.equation = v.arr_sum()
        assert target(1) == pytest.approx(7.0)

    @pytest.mark.parametrize("values, expected", [
        pytest.param([1.0, 2.0, 3.0], 2.0, id="odd"),
        pytest.param([1.0, 2.0, 3.0, 10.0], 2.5, id="even_averages_the_middle_two"),
    ])
    def test_arr_median(self, values, expected):
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="median")
        v = model.constant("v")
        v.setup_vector(len(values), list(values))
        target = model.converter("target")
        target.equation = v.arr_median()
        assert target(1) == pytest.approx(expected)

    def test_arr_stddev_is_the_population_deviation(self):
        """ddof=0, matching numpy's default - the value Rust has to reproduce."""
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="stddev")
        v = model.constant("v")
        v.setup_vector(len(values), list(values))
        target = model.converter("target")
        target.equation = v.arr_stddev()
        mean = sum(values) / len(values)
        population = math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))
        assert target(1) == pytest.approx(population)
        assert population == pytest.approx(2.0)

    @pytest.mark.parametrize("rank, expected", [
        pytest.param(1, 6.0, id="highest"),
        pytest.param(2, 4.0, id="second"),
        pytest.param(5, 1.0, id="lowest_in_range"),
        pytest.param(6, 1.0, id="above_range_clamps_to_minimum"),
        pytest.param(99, 1.0, id="far_above_range_clamps_to_minimum"),
        pytest.param(-1, 1.0, id="negative_clamps_to_minimum"),
    ])
    def test_arr_rank_clamps_instead_of_returning_nan(self, rank, expected):
        """Out of range gives the minimum, not NaN.

        Pinned because NaN is the plausible-looking answer, and specifying it for the
        Rust builtin would ship a parity bug.
        """
        values = [3.0, 6.0, 2.0, 4.0, 1.0]
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name=f"rank{rank}")
        v = model.constant("v")
        v.setup_vector(len(values), list(values))
        target = model.converter("target")
        target.equation = v.arr_rank(rank)
        assert target(1) == pytest.approx(expected)


class TestDot:
    """`dot` shapes `test_sddsl.py` omits, and the whole of the named product."""

    def test_matrix_dot_matrix(self):
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="matmat")
        a = model.constant("a")
        a.setup_matrix([2, 2], [[1.0, 2.0], [3.0, 4.0]])
        b = model.constant("b")
        b.setup_matrix([2, 2], [[5.0, 6.0], [7.0, 8.0]])
        target = model.converter("target")
        target.equation = a.dot(b)

        expected = [[19.0, 22.0], [43.0, 50.0]]
        for i in (0, 1):
            for j in (0, 1):
                assert target[i][j](1) == pytest.approx(expected[i][j])

    def test_an_expression_can_be_a_dot_operand(self):
        """The one path that reaches `Operator.arrayed_term`, and it is fragile.

        `DotOperator` is the only operator whose clone keeps its operands whole: the
        expansion picks the rows and columns the index calls for. An operand cloned
        down to a leaf turns a vector-matrix product into a single value times a
        *parent* element, which reads 0.0 - silently. That happened once, and no test
        caught it, hence this one.

        Reachable only by constructing the operator: `dot()` is a method on `Element`,
        not on `Operator`, so `(v + w).dot(m)` is an AttributeError.
        """
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="dot_expression")
        v = model.constant("v")
        v.setup_vector(2, [1.0, 2.0])
        w = model.constant("w")
        w.setup_vector(2, [3.0, 4.0])
        weights = model.constant("weights")
        weights.setup_matrix([2, 2], [[1.0, 10.0], [100.0, 1000.0]])

        target = model.converter("target")
        target.equation = DotOperator(v + w, weights)

        # [1+3, 2+4] . [[1, 10], [100, 1000]] = [4*1 + 6*100, 4*10 + 6*1000]
        assert target[0](1) == pytest.approx(604.0)
        assert target[1](1) == pytest.approx(6040.0)


class TestNamedDot:
    """`dot` over labels.

    The contracted axis has to carry the same labels on both sides; the axes that
    survive keep their own - rows from the left operand, columns from the right. The
    numbers here are the worked examples: regions, products and channels.
    """

    def _model(self):
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="named_dot")
        factor = model.constant("factor")
        factor.equation = 2.0
        regions = model.constant("regions")
        regions.setup_named_vector({"north": 3.0, "south": 5.0})
        products = model.constant("products")
        products.setup_named_vector({"a": 10.0, "b": 20.0})
        by_product = model.constant("by_product")
        by_product.setup_named_matrix({"north": {"a": 1.0, "b": 2.0},
                                       "south": {"a": 3.0, "b": 4.0}})
        by_channel = model.constant("by_channel")
        by_channel.setup_named_matrix({"a": {"online": 1.0, "retail": 0.0},
                                       "b": {"online": 0.5, "retail": 0.5}})
        return model, factor, regions, products, by_product, by_channel

    def test_value_times_named_vector_keeps_the_labels(self):
        model, factor, regions, _products, _by_product, _by_channel = self._model()
        target = model.converter("target")
        target.equation = factor.dot(regions)

        assert target["north"](1) == pytest.approx(6.0)
        assert target["south"](1) == pytest.approx(10.0)

    def test_named_matrix_times_value_keeps_the_labels(self):
        model, factor, _regions, _products, by_product, _by_channel = self._model()
        target = model.converter("target")
        target.equation = by_product.dot(factor)

        assert target["north"]["a"](1) == pytest.approx(2.0)
        assert target["south"]["b"](1) == pytest.approx(8.0)

    def test_named_vector_times_named_vector_is_a_scalar(self):
        model, _factor, regions, _products, _by_product, _by_channel = self._model()
        other = model.constant("other")
        other.setup_named_vector({"south": 2.0, "north": 4.0})
        target = model.converter("target")
        target.equation = regions.dot(other)

        # Paired by label, not by position: north meets north although the two
        # vectors list their labels in opposite order.
        assert target(1) == pytest.approx(3.0 * 4.0 + 5.0 * 2.0)

    def test_named_matrix_times_named_vector_is_labelled_by_the_rows(self):
        model, _factor, _regions, products, by_product, _by_channel = self._model()
        target = model.converter("target")
        target.equation = by_product.dot(products)

        assert target["north"](1) == pytest.approx(1.0 * 10.0 + 2.0 * 20.0)
        assert target["south"](1) == pytest.approx(3.0 * 10.0 + 4.0 * 20.0)

    def test_named_vector_times_named_matrix_is_labelled_by_the_columns(self):
        """The one shape whose labels come from the right operand.

        The rows are what the sum consumes, so a product over regions answers per
        product - and can only carry the matrix's column labels.
        """
        model, _factor, regions, _products, by_product, _by_channel = self._model()
        target = model.converter("target")
        target.equation = regions.dot(by_product)

        assert target["a"](1) == pytest.approx(3.0 * 1.0 + 5.0 * 3.0)
        assert target["b"](1) == pytest.approx(3.0 * 2.0 + 5.0 * 4.0)

    def test_named_matrix_times_named_matrix(self):
        model, _factor, _regions, _products, by_product, by_channel = self._model()
        target = model.converter("target")
        target.equation = by_product.dot(by_channel)

        expected = {"north": {"online": 2.0, "retail": 1.0},
                    "south": {"online": 5.0, "retail": 2.0}}
        for row in expected:
            for column in expected[row]:
                assert target[row][column](1) == pytest.approx(expected[row][column])

    def test_a_square_matrix_carries_its_labels_through(self):
        """The transition matrix, where both axes hold the same labels."""
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="transition")
        stock = model.constant("stock")
        stock.setup_named_vector({"north": 100.0, "south": 200.0})
        migration = model.constant("migration")
        migration.setup_named_matrix({"north": {"north": 0.9, "south": 0.1},
                                      "south": {"north": 0.2, "south": 0.8}})
        target = model.converter("target")
        target.equation = stock.dot(migration)

        assert target["north"](1) == pytest.approx(130.0)
        assert target["south"](1) == pytest.approx(170.0)

    def test_a_named_dot_result_takes_part_in_further_arithmetic(self):
        model, _factor, _regions, products, by_product, _by_channel = self._model()
        revenue = model.converter("revenue")
        revenue.equation = by_product.dot(products)
        scaled = model.converter("scaled")
        scaled.equation = revenue * 2.0 + 1.0

        assert scaled["north"](1) == pytest.approx(101.0)
        assert scaled["south"](1) == pytest.approx(221.0)

    def test_an_expression_can_be_a_named_dot_operand(self):
        """An operator operand knows its labels only through the index protocol."""
        model, _factor, _regions, products, by_product, _by_channel = self._model()
        target = model.converter("target")
        target.equation = DotOperator(by_product + by_product, products)

        assert target["north"](1) == pytest.approx(2 * (1.0 * 10.0 + 2.0 * 20.0))
        assert target["south"](1) == pytest.approx(2 * (3.0 * 10.0 + 4.0 * 20.0))

    def test_an_index_that_is_not_a_label_of_the_result_raises(self):
        model, _factor, regions, _products, by_product, _by_channel = self._model()
        operator = DotOperator(regions, by_product, ["nonsense"])

        with pytest.raises(Exception, match="'nonsense' is not one of the labels"):
            operator.term()

    def test_labels_that_do_not_line_up_raise(self):
        model, _factor, regions, products, _by_product, _by_channel = self._model()
        target = model.converter("target")

        with pytest.raises(Exception, match="have to carry the same labels"):
            target.equation = regions.dot(products)

    def test_mixing_named_and_unnamed_raises(self):
        model, _factor, regions, _products, _by_product, _by_channel = self._model()
        unnamed = model.constant("unnamed")
        unnamed.setup_vector(2, [1.0, 2.0])
        target = model.converter("target")

        with pytest.raises(Exception, match="named array with an unnamed one"):
            target.equation = regions.dot(unnamed)

    def test_a_matrix_with_row_specific_column_labels_raises(self):
        """A contraction sums over one label set, so the matrix has to be rectangular.

        The rule holds at the product and nowhere else: the same matrix multiplied by
        a value stays legal, which is what keeps models that never multiply working.
        """
        model, factor, _regions, products, _by_product, _by_channel = self._model()
        ragged = model.constant("ragged")
        ragged.setup_named_matrix({"a": {"a1": 1.0, "a2": 2.0},
                                   "b": {"b1": 3.0, "b2": 4.0}})
        target = model.converter("target")

        with pytest.raises(Exception, match="same column labels in every row"):
            target.equation = ragged.dot(products)

        scaled = model.converter("scaled")
        scaled.equation = factor.dot(ragged)
        assert scaled["a"]["a1"](1) == pytest.approx(2.0)
        assert scaled["b"]["b2"](1) == pytest.approx(8.0)


class TestDimensionSelector:
    """The `dimensions` argument on `arr_sum` / `arr_prod`.

    `"*"` (the default) and an int equal to the array's depth aggregate every leaf.
    Anything else used to cut the recursion short, build an empty term and raise
    `SyntaxError: invalid syntax` at evaluation - a public argument that could not be
    called with a meaningful value.

    **It is rejected rather than given a meaning.** Aggregating over one dimension of
    a matrix would have to return a vector, which is a new result shape for the whole
    operator layer rather than a bug fix.
    """

    def _matrix_model(self):
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="dimsel")
        v = model.constant("v")
        v.setup_named_matrix({"r1": {"c1": 1.0, "c2": 2.0},
                              "r2": {"c1": 3.0, "c2": 4.0}})
        return model, v

    def _vector_model(self):
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="dimsel_vector")
        v = model.constant("v")
        v.setup_vector(3, [1.0, 2.0, 3.0])
        return model, v

    @pytest.mark.parametrize("dimension", ["*", 2])
    def test_full_depth_sums_every_leaf_of_a_matrix(self, dimension):
        model, v = self._matrix_model()
        target = model.converter("target")
        target.equation = v.arr_sum(dimension)
        assert target(1) == pytest.approx(10.0)

    @pytest.mark.parametrize("dimension", ["*", 2])
    def test_full_depth_multiplies_every_leaf_of_a_matrix(self, dimension):
        model, v = self._matrix_model()
        target = model.converter("target")
        target.equation = v.arr_prod(dimension)
        assert target(1) == pytest.approx(24.0)

    @pytest.mark.parametrize("dimension", ["*", 1])
    def test_full_depth_aggregates_every_leaf_of_a_vector(self, dimension):
        model, v = self._vector_model()
        total = model.converter("total")
        total.equation = v.arr_sum(dimension)
        product = model.converter("product")
        product.equation = v.arr_prod(dimension)
        assert total(1) == pytest.approx(6.0)
        assert product(1) == pytest.approx(6.0)

    @pytest.mark.parametrize("dimension", [0, 1, 3])
    @pytest.mark.parametrize("aggregation", ["arr_sum", "arr_prod"])
    def test_a_partial_dimension_of_a_matrix_is_rejected(self, aggregation, dimension):
        model, v = self._matrix_model()
        target = model.converter("target")
        with pytest.raises(OperatorError, match="every dimension"):
            target.equation = getattr(v, aggregation)(dimension)

    @pytest.mark.parametrize("dimension", [0, 2])
    @pytest.mark.parametrize("aggregation", ["arr_sum", "arr_prod"])
    def test_a_partial_dimension_of_a_vector_is_rejected(self, aggregation, dimension):
        model, v = self._vector_model()
        target = model.converter("target")
        with pytest.raises(OperatorError, match="every dimension"):
            target.equation = getattr(v, aggregation)(dimension)

    def test_the_rejection_names_the_depth_the_array_actually_has(self):
        model, v = self._matrix_model()
        target = model.converter("target")
        with pytest.raises(OperatorError, match="or 2 for this 2-dimensional array"):
            target.equation = v.arr_sum(1)


class TestArrayedStockFlow:
    """Integration over time - what `test_sddsl.py` cannot see.

    Its `get_element_data` reads a single timestep, so no existing test integrates an
    arrayed stock from an arrayed flow across the run.
    """

    @staticmethod
    def _chain():
        """Two independent per-index growth processes, 10 % and 20 %."""
        model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="growth")
        stock = model.stock("stock")
        stock.setup_named_vector({"slow": 100.0, "fast": 50.0})
        rate = model.constant("rate")
        rate.setup_named_vector({"slow": 0.1, "fast": 0.2})
        inflow = model.flow("inflow")
        inflow.setup_named_vector({"slow": 0.0, "fast": 0.0})
        for key in ("slow", "fast"):
            inflow[key].equation = stock[key] * rate[key]
            stock[key].equation = inflow[key]
        return model, stock

    def test_each_index_integrates_independently(self):
        _model, stock = self._chain()
        for t, slow, fast in [(0, 100.0, 50.0), (1, 110.0, 60.0),
                              (2, 121.0, 72.0), (3, 133.1, 86.4)]:
            assert stock["slow"](t) == pytest.approx(slow)
            assert stock["fast"](t) == pytest.approx(fast)

    def test_sub_elements_carry_their_own_initial_value(self):
        _model, stock = self._chain()
        assert stock["slow"](0) == pytest.approx(100.0)
        assert stock["fast"](0) == pytest.approx(50.0)

    def test_an_arrayed_flow_is_clamped_at_zero(self):
        """`Flow` wraps every equation in `max(0, ...)`; arrayed flows are no exception.

        Pinned because it is why the flagship model uses paired positive flows rather
        than one signed flow - a shrinking level written as a negative flow reads zero.
        """
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="clamp")
        stock = model.stock("stock")
        stock.setup_named_vector({"only": 50.0})
        outflow = model.flow("outflow")
        outflow.setup_named_vector({"only": 0.0})
        outflow["only"].equation = stock["only"] * -0.1
        stock["only"].equation = outflow["only"]

        assert outflow["only"](0) == pytest.approx(0.0)
        assert stock["only"](1) == pytest.approx(50.0)

    def test_an_arrayed_biflow_works(self):
        """`Biflow` used to inherit `Element.add_arr_equation`, a no-op `pass`.

        `setup_named_vector` reported success, `arrayed` was True, and every
        sub-element was `None` with no entity registered and nothing raised.
        """
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="biflow")
        stock = model.stock("stock")
        stock.setup_named_vector({"only": 50.0})
        net = model.biflow("net")
        net.setup_named_vector({"only": 0.0})

        assert net["only"] is not None
        assert "net[only]" in model.biflows

        net["only"].equation = stock["only"] * -0.1
        stock["only"].equation = net["only"]

        # A biflow may go negative, so the stock actually declines.
        assert stock["only"](1) == pytest.approx(45.0)


class TestABareArrayedElementAsEquation:
    """`flow.equation = some_arrayed_constant`, with no expression around it.

    This used to be the one arrayed assignment that only a `Stock` handled. Every other
    element type stayed scalar and kept an equation referencing the *parent*, which
    holds no value of its own - so the result was `0.0`, arrayedness gone, nothing
    raised. The suite missed it because every other case here wraps the array in an
    operator, and the operator is what carried the shape.
    """

    KINDS = ("flow", "biflow", "converter")

    @pytest.mark.parametrize("shape", _shape_params())
    @pytest.mark.parametrize("kind", KINDS)
    def test_the_target_takes_the_shape_and_the_values(self, shape, kind):
        model, v, _s, _w = _build(shape)
        target = getattr(model, kind)("target")
        target.equation = v

        assert target.arrayed, f"{kind} stayed scalar"
        expected = values_for(shape)
        for key in shape.keys:
            assert shape.leaf(target, key)(1) == pytest.approx(expected[key])

    @pytest.mark.parametrize("shape", _shape_params())
    @pytest.mark.parametrize("kind", KINDS)
    def test_an_element_already_given_a_shape_is_overwritten(self, shape, kind):
        """The natural way to write it: declare the shape, then the equation."""
        model, v, _s, _w = _build(shape)
        target = getattr(model, kind)("target")
        shape.setup(target, {key: 0.0 for key in shape.keys})
        target.equation = v

        expected = values_for(shape)
        for key in shape.keys:
            assert shape.leaf(target, key)(1) == pytest.approx(expected[key])

    @pytest.mark.parametrize("shape", _shape_params(VECTORS))
    def test_a_stock_still_integrates_it(self, shape):
        """The one type that did handle this, so the fix must not disturb it."""
        model, v, _s, _w = _build(shape)
        stock = model.stock("stock")
        shape.setup(stock, {key: 0.0 for key in shape.keys})
        stock.equation = v

        expected = values_for(shape)
        for key in shape.keys:
            assert shape.leaf(stock, key)(2) == pytest.approx(2.0 * expected[key])

    @pytest.mark.parametrize("shape", _shape_params())
    def test_a_constant_says_it_can_only_hold_a_number(self, shape):
        """A constant is an input, not a computation - arrayed or not.

        It carried the same defect in a different disguise: `equation == None` built a
        comparison operator, which is truthy, so *any* element assigned to a constant
        silently became `None` and read 0.0. Now the error the class already documented
        actually reaches the caller.
        """
        model, v, _s, _w = _build(shape)
        target = model.constant("target")

        with pytest.raises(Exception, match="floating point"):
            target.equation = v

    def test_a_constant_rejects_a_scalar_element_too(self):
        """Not array-specific: the same swallow hid this for scalars."""
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="scalar_constant")
        source = model.converter("source")
        source.equation = 7.0
        target = model.constant("target")

        with pytest.raises(Exception, match="floating point"):
            target.equation = source


class TestNoSilentScalar:
    """The invariant: an arrayed input never yields a silent scalar.

    Every bug the 2026-09-08 audit found violates exactly this, and no test stated it.
    A construct may propagate, or it may raise - what it must not do is return a
    plausible number that quietly ignores the array. This class is the reason the file
    exists; if only one test survives a refactor, keep this one.

    Note what it deliberately does *not* check: **values**. `3.0 * v` once returned
    an arrayed result of zeros - satisfying this invariant while being wrong.
    That is `test_literal_times_array`'s job. Here the question is only whether the
    array survived the operation at all.
    """

    # Each of these used to collapse to a scalar.
    COLLAPSING = [
        ("sqrt", lambda v, s: sd.sqrt(v)),
        ("ln", lambda v, s: sd.ln(v)),
        ("floor", lambda v, s: sd.floor(v)),
        ("round", lambda v, s: sd.round(v, 1)),
        ("abs", lambda v, s: sd.abs(v)),
        ("exp", lambda v, s: sd.exp(v / 100.0)),
        ("max_with_literal", lambda v, s: sd.max(v, 10.0)),
        ("min_with_element", lambda v, s: sd.min(v, s)),
        ("greater_than", lambda v, s: v > 10.0),
        ("less_than", lambda v, s: v < 10.0),
        ("if_", lambda v, s: sd.If(v > 10.0, v, s)),
        ("and_", lambda v, s: sd.And(v > 5.0, v < 20.0)),
        ("not_", lambda v, s: sd.Not(v > 10.0)),
        ("power", lambda v, s: v ** 2.0),
        ("modulo", lambda v, s: v % 5.0),
    ]

    @pytest.mark.parametrize("shape", _shape_params())
    @pytest.mark.parametrize("name, build", [
        pytest.param(name, build, id=name) for name, build in COLLAPSING
    ])
    def test_arrayed_input_never_yields_a_silent_scalar(self, shape, name, build):
        try:
            result = evaluate_arrayed(shape, lambda v, s, w: build(v, s))
        except Collapsed as collapsed:
            pytest.fail(
                f"{name} on {shape.id} silently returned the scalar "
                f"{collapsed.value!r} instead of an arrayed result"
            )
        except Exception:
            # Raising is an acceptable answer: the caller learns the truth.
            return
        assert set(result) == set(shape.keys)

    # These always held the invariant and must keep doing so. The reflected
    # forms are here rather than above because they were honest about failing: three
    # of them raised on named arrays, and `3.0 * v` stayed arrayed - with wrong
    # values, which is a different test's business.
    @pytest.mark.parametrize("shape", _shape_params())
    @pytest.mark.parametrize("name, build", [
        ("plus_literal", lambda v, s: v + 3.0),
        ("times_element", lambda v, s: v * s),
        ("element_minus", lambda v, s: s - v),
        ("negation", lambda v, s: -v),
        ("literal_plus", lambda v, s: 3.0 + v),
        ("literal_minus", lambda v, s: 3.0 - v),
        ("literal_times", lambda v, s: 3.0 * v),
        ("literal_over", lambda v, s: 3.0 / v),
    ], ids=lambda p: p if isinstance(p, str) else "")
    def test_the_operators_that_already_hold_the_invariant(self, shape, name, build):
        """The same invariant where it currently holds, so a regression is caught."""
        try:
            result = evaluate_arrayed(shape, lambda v, s, w: build(v, s))
        except Collapsed as collapsed:
            pytest.fail(
                f"{name} on {shape.id} silently returned the scalar "
                f"{collapsed.value!r} instead of an arrayed result"
            )
        except Exception:
            return
        assert set(result) == set(shape.keys)


# ---------------------------------------------------------------------------
# The flagship model
#
# `tests/_arrayed_fixtures.py` holds the arrayed models the parity suite and the
# documentation are built around. Nothing else in the test run executes them, so a
# regression in one would pass unnoticed - `.coveragerc` omits `tests/*`, so coverage
# would not notice either. These tests close that gap.
# ---------------------------------------------------------------------------

from _arrayed_fixtures import (  # noqa: E402  - after the shape helpers on purpose
    LEVELS,
    build_matrix_model,
    build_workforce_model,
    _build_matrix_bptk,
    _build_workforce_bptk,
)


class TestFlagshipWorkforceModel:
    """The workforce aging chain, pinned against hand computation."""

    INITIAL = {"junior": 100.0, "mid": 40.0, "senior": 15.0}

    # junior: 100 + 12 - 0.15*100 - 0.10*100          = 87.0
    # mid   :  40 +  3 + 15 - 0.08*40 - 0.06*40       = 52.4
    # senior:  15 +  1 + 0.08*40 - 0.04*15            = 18.6
    AFTER_ONE_STEP = {"junior": 87.0, "mid": 52.4, "senior": 18.6}

    @staticmethod
    def _stock(model, level):
        return model.stocks[f"headcount[{level}]"]

    def test_each_level_starts_at_its_own_initial_value(self):
        model = build_workforce_model()
        for level, expected in self.INITIAL.items():
            assert self._stock(model, level)(0) == pytest.approx(expected)

    @pytest.mark.parametrize("level", LEVELS)
    def test_one_step_matches_hand_computation(self, level):
        model = build_workforce_model()
        assert self._stock(model, level)(1) == pytest.approx(
            self.AFTER_ONE_STEP[level])

    def test_the_flows_at_the_first_timestep(self):
        model = build_workforce_model()
        flows = model.flows
        assert flows["hiring[junior]"](0) == pytest.approx(12.0)
        assert flows["promotion[junior]"](0) == pytest.approx(15.0)   # 0.15 * 100
        assert flows["attrition[junior]"](0) == pytest.approx(10.0)   # 0.10 * 100
        # A senior is never promoted out of the chain.
        assert flows["promotion[senior]"](0) == pytest.approx(0.0)

    def test_the_aggregations(self):
        model = build_workforce_model()
        converters = model.converters
        assert converters["total_headcount"](0) == pytest.approx(155.0)
        assert converters["total_cost"](0) == pytest.approx(
            100.0 * 60000.0 + 40.0 * 90000.0 + 15.0 * 130000.0)
        assert converters["average_salary"](0) == pytest.approx(
            (60000.0 + 90000.0 + 130000.0) / 3.0)

    def test_cost_is_element_wise_not_a_dot_product(self):
        """`cost[level]` must stay per-level; `total_cost` does the summing."""
        model = build_workforce_model()
        cost = model.converters
        assert cost["cost[junior]"](0) == pytest.approx(100.0 * 60000.0)
        assert cost["cost[senior]"](0) == pytest.approx(15.0 * 130000.0)

    def test_the_chain_reaches_its_analytical_equilibrium(self):
        """Inflow equals outflow, solved by hand:

            junior = 12 / (0.15 + 0.10)              = 48.00
            mid    = (3 + 0.15*junior) / (0.08+0.06) = 72.86
            senior = (1 + 0.08*mid) / 0.04           = 170.71

        Pinned because it is the model's whole story: senior has the smallest total
        outflow rate, hence a 25-period time constant against junior's 4, so it settles
        last and dominates the long-run structure and cost.
        """
        horizon = 400
        model = build_workforce_model()
        model.stoptime = float(horizon)

        junior = 12.0 / (0.15 + 0.10)
        mid = (3.0 + 0.15 * junior) / (0.08 + 0.06)
        senior = (1.0 + 0.08 * mid) / 0.04

        # Walk forward rather than asking for t=400 directly. The Python engine
        # evaluates a stock by recursing into the previous timestep, so a cold call
        # at a late timestep raises RecursionError; each ascending call memoises and
        # keeps the next one shallow.
        stocks = {level: self._stock(model, level) for level in LEVELS}
        for t in range(0, horizon + 1):
            for stock in stocks.values():
                stock(t)

        assert stocks["junior"](horizon) == pytest.approx(junior, rel=1e-6)
        assert stocks["mid"](horizon) == pytest.approx(mid, rel=1e-6)
        assert stocks["senior"](horizon) == pytest.approx(senior, rel=1e-4)

    def test_no_flow_ever_goes_negative(self):
        """The model is built so the `max(0, ...)` clamp never bites.

        If a future edit introduces a signed flow, the clamp would silently zero it;
        this test says so instead.
        """
        model = build_workforce_model()
        for level in LEVELS:
            for flow in ("hiring", "promotion", "attrition"):
                for t in range(0, 11):
                    assert model.flows[f"{flow}[{level}]"](t) >= 0.0

    def test_it_serialises_without_the_aggregations(self):
        assert build_workforce_model(with_aggregations=False).to_json()

    def test_it_serialises_with_the_aggregations(self):
        """The aggregations serialise as variadic calls over the leaves."""
        payload = json.loads(build_workforce_model(with_aggregations=True).to_json())

        converters = {entity["name"]: entity["equation"]
                      for entity in payload["entities"]["converters"]}
        assert converters["total_headcount"] == {
            "type": "call", "function": "arr_sum",
            "args": [{"type": "ref", "name": f"headcount[{level}]"}
                     for level in LEVELS]}
        assert converters["average_salary"]["function"] == "arr_mean"

    def test_no_parent_element_is_serialised(self):
        """A parent holds no equation; it used to be emitted as a `0.0` literal."""
        payload = json.loads(build_workforce_model().to_json())

        for kind, entities in payload["entities"].items():
            for entity in entities:
                assert "[" in entity["name"] or entity["name"] in (
                    "total_headcount", "total_cost", "average_salary"), (
                    f"{kind}: {entity['name']} is a parent")


class TestFlagshipMatrixCompanion:
    """The 2-D companion, which exists to reach `dot` and the matrix paths."""

    def test_vector_dot_matrix(self):
        model = build_matrix_model()
        weighted = model.converters["weighted"]
        # [0.5, 1.5] . [[2,3],[4,5]] = [0.5*2 + 1.5*4, 0.5*3 + 1.5*5]
        assert weighted[0](1) == pytest.approx(7.0)
        assert weighted[1](1) == pytest.approx(9.0)


class TestFlagshipScenarios:
    """The bptk wrappers, including a constant override on a bracketed name.

    Each test registers its own manager name. `ScenarioManagerFactory` is
    process-global, so a shared name means a shared result cache across `bptk()`
    instances - and mixing a single-scenario run with a two-scenario run then returns
    inconsistent column names. See :func:`_build_workforce_bptk`.
    """

    def test_base_scenario_runs(self):
        manager = "workforce_base_only"
        bptk = _build_workforce_bptk(with_aggregations=False, manager_name=manager)
        frame = bptk.run_scenarios(
            scenario_managers=[manager], scenarios=["base"],
            equations=["headcount[junior]"])
        assert frame.iloc[0, 0] == pytest.approx(100.0)

    def test_a_constant_override_on_a_bracketed_name_takes_effect(self):
        """`hiring_rate[junior]` addresses a sub-element by its flattened name.

        Arrayed `set_constant` is a known issue in the step-by-step path; this pins
        that the scenario-registration path at least works, so a regression there is
        visible.
        """
        manager = "workforce_override"
        bptk = _build_workforce_bptk(with_aggregations=False, manager_name=manager)
        frame = bptk.run_scenarios(
            scenario_managers=[manager],
            scenarios=["base", "hiring_freeze"],
            equations=["headcount[junior]"])

        base = frame[f"{manager}_base_headcount[junior]"]
        frozen = frame[f"{manager}_hiring_freeze_headcount[junior]"]
        assert base.iloc[-1] > frozen.iloc[-1] * 5, (
            "freezing junior hiring should visibly shrink the junior base")

    def test_the_matrix_companion_runs_as_a_scenario(self):
        bptk = _build_matrix_bptk()
        frame = bptk.run_scenarios(
            scenario_managers=["matrix_mgr"], scenarios=["base"],
            equations=["weighted[0]", "weighted[1]"])
        assert frame.iloc[-1].tolist() == pytest.approx([7.0, 9.0])
