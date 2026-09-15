"""Python-vs-Rust parity for multidimensional (arrayed) models.

`tests/test_parity.py` compares the two engines over scalar models; this file does the
same for arrays, across every operand combination and every operator that can meet one.
It is the layer neither of the other array files covers: `test_sddsl.py` and
`test_multidimensional_sddsl.py` check the Python engine against hand-computed values,
and the serializer tests check the JSON shape - but nothing compared the two engines on
an arrayed model.

**The axes, all crossed:**

* Four shapes - unnamed vector, named vector, unnamed matrix, named matrix.
* Six operand pairings, in **both** orders: array/array, array/element, element/array,
  array/literal, literal/array, and the array alone.
* Arithmetic, power, modulo, every math function, every comparison, the logical
  functions, `max`/`min`, `lookup`, `step`, `pulse`, the stateful three, all nine
  aggregations, and `dot` in its four shapes.

**Why the Rust results are trustworthy here.** `run_parity` loads the model into the
engine directly, so a model the engine cannot express raises instead of falling back -
there is no way for a "parity" test in this file to end up comparing Python with Python.

**Stochastic functions are not value-comparable** and live in their own class: the two
engines draw from different generators, so the same distribution gives different
numbers. What is asserted there is what parity can mean for a draw - each index draws
within its own bounds, and the indices are independent.
"""

import math

import pytest

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
from BPTK_Py.sddsl.operators import DotOperator

from test_parity import run_parity


# ---------------------------------------------------------------------------
# Shapes
#
# Purpose-built for parity: what matters is building the shape and naming its
# leaves, because the leaf names are the entities the Rust engine knows.
# ---------------------------------------------------------------------------

VECTOR_VALUES = [4.0, 9.0, 16.0]
MATRIX_VALUES = [[4.0, 9.0], [16.0, 25.0]]
VECTOR_LABELS = ["junior", "mid", "senior"]
MATRIX_LABELS = (["north", "south"], ["widget", "gadget"])

SCALAR_ELEMENT_VALUE = 2.0
LITERAL = 3.0

SHAPES = ("unnamed_vector", "named_vector", "unnamed_matrix", "named_matrix")
VECTORS = ("unnamed_vector", "named_vector")
MATRICES = ("unnamed_matrix", "named_matrix")


def setup(element, shape, offset=0.0):
    """Give `element` the requested shape, with distinct positive values."""
    if shape == "unnamed_vector":
        element.setup_vector(len(VECTOR_VALUES), [v + offset for v in VECTOR_VALUES])
    elif shape == "named_vector":
        element.setup_named_vector(
            {label: value + offset
             for label, value in zip(VECTOR_LABELS, VECTOR_VALUES)})
    elif shape == "unnamed_matrix":
        element.setup_matrix([2, 2], [[v + offset for v in row] for row in MATRIX_VALUES])
    elif shape == "named_matrix":
        rows, columns = MATRIX_LABELS
        element.setup_named_matrix(
            {row: {column: MATRIX_VALUES[i][j] + offset
                   for j, column in enumerate(columns)}
             for i, row in enumerate(rows)})
    else:
        raise ValueError(shape)


def leaf_names(element):
    """The flattened entity names of an arrayed element, in declaration order."""
    if element._elements.vector_size() == 0:
        return [element.name]

    names = []
    for key in element._elements.equations:
        names.extend(leaf_names(element[key]))
    return names


def build(shape, name="parity", second=False):
    """A model with an arrayed `v`, a scalar element `s`, and optionally a second `w`."""
    model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name=f"{name}_{shape}")

    v = model.constant("v")
    setup(v, shape)

    s = model.constant("s")
    s.equation = SCALAR_ELEMENT_VALUE

    w = None
    if second:
        w = model.constant("w")
        setup(w, shape, offset=1.0)

    return model, v, s, w


def check(shape, expression, second=False, kind="converter", atol=1e-10):
    """Assign `expression(v, s, w)` to an arrayed target and compare both engines."""
    model, v, s, w = build(shape, second=second)
    target = getattr(model, kind)("target")
    target.equation = expression(v, s, w)

    assert target.arrayed, "the expression collapsed to a scalar - nothing to compare"
    run_parity(model, leaf_names(target), atol=atol)


def check_scalar(shape, expression, second=False, atol=1e-10):
    """The same, for an expression that deliberately yields one number."""
    model, v, s, w = build(shape, second=second)
    target = model.converter("target")
    target.equation = expression(v, s, w)

    assert not target.arrayed, "expected a scalar result"
    run_parity(model, ["target"], atol=atol)


# ---------------------------------------------------------------------------
# Element-wise arithmetic, every operand pairing in both orders
# ---------------------------------------------------------------------------

ARITHMETIC = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "div": lambda a, b: a / b,
}


class TestArithmeticOperandPairings:
    """`+ - * /` for array/array, array/element, element/array, array/literal,
    literal/array - the axis that decides whether propagation and serialization agree
    on which operand is which."""

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("operator", sorted(ARITHMETIC))
    def test_array_and_array(self, shape, operator):
        check(shape, lambda v, s, w: ARITHMETIC[operator](v, w), second=True)

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("operator", sorted(ARITHMETIC))
    def test_array_and_element(self, shape, operator):
        check(shape, lambda v, s, w: ARITHMETIC[operator](v, s))

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("operator", sorted(ARITHMETIC))
    def test_element_and_array(self, shape, operator):
        check(shape, lambda v, s, w: ARITHMETIC[operator](s, v))

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("operator", sorted(ARITHMETIC))
    def test_array_and_literal(self, shape, operator):
        check(shape, lambda v, s, w: ARITHMETIC[operator](v, LITERAL))

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("operator", sorted(ARITHMETIC))
    def test_literal_and_array(self, shape, operator):
        check(shape, lambda v, s, w: ARITHMETIC[operator](LITERAL, v))

    @pytest.mark.parametrize("shape", SHAPES)
    def test_negation(self, shape):
        check(shape, lambda v, s, w: -v)

    @pytest.mark.parametrize("shape", SHAPES)
    def test_a_chain_of_mixed_operands(self, shape):
        check(shape, lambda v, s, w: (v + w) * s / LITERAL - v, second=True)


class TestABareArrayedElement:
    """The array assigned as an equation with no expression around it.

    Worth its own parity case because the target's shape is built by the assignment
    rather than by an operator, so the entities the serializer sees come from a
    different path.
    """

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("kind", ["converter", "flow", "biflow"])
    def test_the_target_mirrors_the_source(self, shape, kind):
        check(shape, lambda v, s, w: v, kind=kind)

    @pytest.mark.parametrize("shape", SHAPES)
    def test_a_stock_integrating_a_bare_arrayed_flow(self, shape):
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name=f"bare_{shape}")
        rate = model.constant("rate")
        setup(rate, shape)
        inflow = model.flow("inflow")
        inflow.equation = rate
        stock = model.stock("stock")
        setup(stock, shape)
        stock.equation = inflow

        run_parity(model, leaf_names(stock) + leaf_names(inflow))


class TestPowerAndModulo:
    @pytest.mark.parametrize("shape", SHAPES)
    def test_power_of_a_literal(self, shape):
        check(shape, lambda v, s, w: v ** 2.0)

    @pytest.mark.parametrize("shape", SHAPES)
    def test_power_of_an_element(self, shape):
        check(shape, lambda v, s, w: v ** s)

    @pytest.mark.parametrize("shape", SHAPES)
    def test_modulo_of_a_literal(self, shape):
        check(shape, lambda v, s, w: v % 5.0)

    @pytest.mark.parametrize("shape", SHAPES)
    def test_modulo_of_an_element(self, shape):
        check(shape, lambda v, s, w: v % s)

    @pytest.mark.parametrize("shape", SHAPES)
    def test_modulo_with_a_literal_on_the_left(self, shape):
        check(shape, lambda v, s, w: 100.0 % v)

    @pytest.mark.parametrize("shape", SHAPES)
    def test_modulo_of_a_compound_operand(self, shape):
        check(shape, lambda v, s, w: (v + s) % 7.0)


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

# The inputs are 4, 9, 16, 25, so the domains need care: arcsin and arccos take
# a ratio, and floor/ceil/round need a fraction to act on.
FUNCTIONS = {
    "sqrt": lambda v: sd.sqrt(v),
    "exp": lambda v: sd.exp(v / 100.0),
    "ln": lambda v: sd.ln(v),
    "log10": lambda v: sd.log10(v),
    "sin": lambda v: sd.sin(v),
    "cos": lambda v: sd.cos(v),
    "tan": lambda v: sd.tan(v),
    "arcsin": lambda v: sd.arcsin(v / 100.0),
    "arccos": lambda v: sd.arccos(v / 100.0),
    "arctan": lambda v: sd.arctan(v),
    "abs": lambda v: sd.abs(-v),
    "floor": lambda v: sd.floor(v / 7.0),
    "ceil": lambda v: sd.ceil(v / 7.0),
    "round": lambda v: sd.round(v / 7.0, 2),
    "sinwave": lambda v: sd.sinwave(v, 4.0),
    "coswave": lambda v: sd.coswave(v, 4.0),
}


class TestMathFunctions:
    """Every math function, applied to a whole array."""

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("function", sorted(FUNCTIONS))
    def test_function(self, shape, function):
        check(shape, lambda v, s, w: FUNCTIONS[function](v))

    @pytest.mark.parametrize("shape", SHAPES)
    def test_functions_nest(self, shape):
        check(shape, lambda v, s, w: sd.sqrt(sd.abs(-v) + s) * sd.exp(v / 100.0))


class TestMinMax:
    """`max`/`min` against a literal, a scalar element and another array, both ways."""

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("function", ["max", "min"])
    def test_against_a_literal(self, shape, function):
        check(shape, lambda v, s, w: getattr(sd, function)(v, 10.0))

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("function", ["max", "min"])
    def test_literal_first(self, shape, function):
        check(shape, lambda v, s, w: getattr(sd, function)(10.0, v))

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("function", ["max", "min"])
    def test_against_an_element(self, shape, function):
        check(shape, lambda v, s, w: getattr(sd, function)(v, s))

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("function", ["max", "min"])
    def test_element_first(self, shape, function):
        check(shape, lambda v, s, w: getattr(sd, function)(s, v))

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("function", ["max", "min"])
    def test_against_another_array(self, shape, function):
        check(shape, lambda v, s, w: getattr(sd, function)(v, w), second=True)


COMPARISONS = {
    "gt": lambda a, b: a > b,
    "lt": lambda a, b: a < b,
    "gte": lambda a, b: a >= b,
    "lte": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
    "neq": lambda a, b: a != b,
}


class TestComparisons:
    """A comparison over an array is one boolean per index.

    The threshold 10.0 sits between the inputs 4, 9 and 16, 25, so a case cannot pass
    by being all-true or all-false. The Python engine yields a genuine `bool` and the
    engine a 1.0/0.0 - which compare equal, and that equality is part of the contract.
    """

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("comparison", sorted(COMPARISONS))
    def test_against_a_literal(self, shape, comparison):
        check(shape, lambda v, s, w: COMPARISONS[comparison](v, 9.0))

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("comparison", sorted(COMPARISONS))
    def test_literal_first(self, shape, comparison):
        check(shape, lambda v, s, w: COMPARISONS[comparison](9.0, v))

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("comparison", sorted(COMPARISONS))
    def test_against_an_element(self, shape, comparison):
        check(shape, lambda v, s, w: COMPARISONS[comparison](v, s))

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("comparison", sorted(COMPARISONS))
    def test_against_another_array(self, shape, comparison):
        check(shape, lambda v, s, w: COMPARISONS[comparison](v, w), second=True)


class TestConditionals:
    @pytest.mark.parametrize("shape", SHAPES)
    def test_if_with_an_arrayed_condition_and_branches(self, shape):
        check(shape, lambda v, s, w: sd.If(v > 10.0, v, s))

    @pytest.mark.parametrize("shape", SHAPES)
    def test_if_with_arrayed_branches_only(self, shape):
        check(shape, lambda v, s, w: sd.If(s > 1.0, v, w), second=True)

    @pytest.mark.parametrize("shape", SHAPES)
    def test_and(self, shape):
        check(shape, lambda v, s, w: sd.And(v > 5.0, v < 20.0))

    @pytest.mark.parametrize("shape", SHAPES)
    def test_or(self, shape):
        check(shape, lambda v, s, w: sd.Or(v < 5.0, v > 20.0))

    @pytest.mark.parametrize("shape", SHAPES)
    def test_not(self, shape):
        check(shape, lambda v, s, w: sd.Not(v > 10.0))

    @pytest.mark.parametrize("shape", SHAPES)
    def test_nested_conditionals(self, shape):
        check(shape, lambda v, s, w: sd.If(sd.And(v > 5.0, v < 20.0),
                                           sd.max(v, w), sd.min(v, s)), second=True)


class TestTimeAndTableFunctions:
    @pytest.mark.parametrize("shape", SHAPES)
    def test_lookup_per_index(self, shape):
        check(shape, lambda v, s, w: sd.lookup(
            v, [(0.0, 0.0), (4.0, 40.0), (9.0, 90.0), (25.0, 250.0)]))

    @pytest.mark.parametrize("shape", SHAPES)
    def test_step_with_an_arrayed_height(self, shape):
        check(shape, lambda v, s, w: sd.step(v, 2.0))

    @pytest.mark.parametrize("shape", SHAPES)
    def test_pulse_with_an_arrayed_volume(self, shape):
        check(shape, lambda v, s, w: sd.pulse(v.model, v, 1.0, 0.0))

    @pytest.mark.parametrize("shape", SHAPES)
    def test_time_functions_inside_an_arrayed_expression(self, shape):
        check(shape, lambda v, s, w: v * sd.time() + sd.dt(v.model))


class TestStatefulFunctions:
    """`smooth`, `trend` and `delay`, each index with its own history.

    They expand into helper stocks and flows per index, so what is compared here is
    whether that whole generated substructure serialises and integrates identically.
    """

    @pytest.mark.parametrize("shape", SHAPES)
    def test_smooth(self, shape):
        check(shape, lambda v, s, w: sd.smooth(v.model, v, 3.0, 1.0))

    @pytest.mark.parametrize("shape", SHAPES)
    def test_trend(self, shape):
        check(shape, lambda v, s, w: sd.trend(v.model, v, 3.0, 1.0))

    @pytest.mark.parametrize("shape", SHAPES)
    def test_delay(self, shape):
        check(shape, lambda v, s, w: sd.delay(v.model, v, 2.0, 1.0))

    @pytest.mark.parametrize("shape", VECTORS)
    def test_smooth_of_an_expression(self, shape):
        check(shape, lambda v, s, w: sd.smooth(v.model, v * s + w, 2.0, 0.0),
              second=True)


# ---------------------------------------------------------------------------
# Aggregations: the array in, one number out
# ---------------------------------------------------------------------------

AGGREGATIONS = ["arr_sum", "arr_prod", "arr_mean", "arr_median", "arr_stddev",
                "arr_max", "arr_min"]


class TestAggregations:
    """The nine aggregations, which are the only array feature with a Rust builtin.

    `arr_size` folds to a literal at serialization time, so it is checked as a value
    rather than as a call.
    """

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("aggregation", AGGREGATIONS)
    def test_aggregation(self, shape, aggregation):
        check_scalar(shape, lambda v, s, w: getattr(v, aggregation)())

    @pytest.mark.parametrize("shape", SHAPES)
    @pytest.mark.parametrize("rank", [1, 2, 3, 4, 99, 0, -1])
    def test_arr_rank(self, shape, rank):
        check_scalar(shape, lambda v, s, w: v.arr_rank(rank))

    @pytest.mark.parametrize("shape", SHAPES)
    def test_arr_size(self, shape):
        check_scalar(shape, lambda v, s, w: v.arr_size() * 1.0)

    @pytest.mark.parametrize("shape", SHAPES)
    def test_an_aggregation_inside_an_expression(self, shape):
        check_scalar(shape, lambda v, s, w: sd.sqrt(v.arr_sum()) + v.arr_mean() * s)

    @pytest.mark.parametrize("shape", SHAPES)
    def test_an_aggregation_meeting_the_array_it_came_from(self, shape):
        check(shape, lambda v, s, w: v / v.arr_sum())

    @pytest.mark.parametrize("shape", SHAPES)
    def test_an_aggregation_of_an_expression(self, shape):
        model, v, s, w = build(shape, second=True)
        combined = model.converter("combined")
        combined.equation = v * s + w
        total = model.converter("total")
        total.equation = combined.arr_sum()

        run_parity(model, ["total"] + leaf_names(combined))


class TestDot:
    """`dot` in its four shapes. It has no Rust builtin: the serializer expands it
    into a sum of products, so what is compared is that expansion."""

    def _model(self):
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="dot_parity")
        vector = model.constant("vector")
        vector.setup_vector(2, [0.5, 1.5])
        other = model.constant("other")
        other.setup_vector(2, [3.0, 4.0])
        matrix = model.constant("matrix")
        matrix.setup_matrix([2, 2], [[2.0, 3.0], [4.0, 5.0]])
        second = model.constant("second")
        second.setup_matrix([2, 2], [[5.0, 6.0], [7.0, 8.0]])
        return model, vector, other, matrix, second

    def test_vector_dot_vector(self):
        model, vector, other, _matrix, _second = self._model()
        target = model.converter("target")
        target.equation = vector.dot(other)
        run_parity(model, ["target"])

    def test_vector_dot_matrix(self):
        model, vector, _other, matrix, _second = self._model()
        target = model.converter("target")
        target.equation = vector.dot(matrix)
        run_parity(model, leaf_names(target))

    def test_matrix_dot_vector(self):
        model, vector, _other, matrix, _second = self._model()
        target = model.converter("target")
        target.equation = matrix.dot(vector)
        run_parity(model, leaf_names(target))

    def test_matrix_dot_matrix(self):
        model, _vector, _other, matrix, second = self._model()
        target = model.converter("target")
        target.equation = matrix.dot(second)
        run_parity(model, leaf_names(target))

    def test_an_expression_as_a_dot_operand(self):
        model, vector, other, matrix, _second = self._model()
        target = model.converter("target")
        target.equation = DotOperator(vector + other, matrix)
        run_parity(model, leaf_names(target))

    def test_a_dot_result_used_in_further_arithmetic(self):
        model, vector, _other, matrix, _second = self._model()
        weighted = model.converter("weighted")
        weighted.equation = vector.dot(matrix)
        scaled = model.converter("scaled")
        scaled.equation = weighted * 2.0 + 1.0
        run_parity(model, leaf_names(weighted) + leaf_names(scaled))


# ---------------------------------------------------------------------------
# Arrayed stocks, flows and biflows over time
# ---------------------------------------------------------------------------

class TestArrayedIntegration:
    """The dynamics, not just the expressions: each index integrates on its own."""

    @pytest.mark.parametrize("shape", SHAPES)
    def test_a_stock_fed_by_an_arrayed_flow(self, shape):
        model = Model(starttime=0.0, stoptime=6.0, dt=1.0, name=f"integrate_{shape}")
        stock = model.stock("stock")
        setup(stock, shape)
        rate = model.constant("rate")
        setup(rate, shape)
        inflow = model.flow("inflow")
        setup(inflow, shape)

        for name, leaf in zip(leaf_names(stock), leaf_names(inflow)):
            model.flows[leaf].equation = model.stocks[name] * 0.05
            model.stocks[name].equation = model.flows[leaf]

        run_parity(model, leaf_names(stock) + leaf_names(inflow))

    @pytest.mark.parametrize("shape", VECTORS)
    def test_an_arrayed_biflow_can_go_negative(self, shape):
        model = Model(starttime=0.0, stoptime=6.0, dt=1.0, name=f"biflow_{shape}")
        stock = model.stock("stock")
        setup(stock, shape)
        net = model.biflow("net")
        setup(net, shape)

        for name, leaf in zip(leaf_names(stock), leaf_names(net)):
            model.biflows[leaf].equation = model.stocks[name] * -0.1
            model.stocks[name].equation = model.biflows[leaf]

        run_parity(model, leaf_names(stock) + leaf_names(net))

    @pytest.mark.parametrize("shape", VECTORS)
    def test_the_flow_clamp_holds_on_both_engines(self, shape):
        """`Flow` wraps its equation in `max(0, ...)`, and the JSON has to carry that.

        A negative rate is the case where a missing clamp would show, so the parity
        here is about the clamp rather than about the arithmetic.
        """
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name=f"clamp_{shape}")
        stock = model.stock("stock")
        setup(stock, shape)
        outflow = model.flow("outflow")
        setup(outflow, shape)

        for name, leaf in zip(leaf_names(stock), leaf_names(outflow)):
            model.flows[leaf].equation = model.stocks[name] * -0.1
            model.stocks[name].equation = model.flows[leaf]

        run_parity(model, leaf_names(stock) + leaf_names(outflow))

    def test_a_chain_that_crosses_indices(self):
        """An aging chain: what leaves one index enters the next."""
        model = Model(starttime=0.0, stoptime=8.0, dt=1.0, name="aging_chain")
        levels = ["a", "b", "c"]
        stock = model.stock("level")
        stock.setup_named_vector({level: 100.0 for level in levels})
        move = model.flow("move")
        move.setup_named_vector({level: 0.0 for level in levels})

        for level in levels:
            move[level].equation = stock[level] * 0.2
        stock["a"].equation = -move["a"]
        stock["b"].equation = move["a"] - move["b"]
        stock["c"].equation = move["b"] - move["c"]

        run_parity(model, leaf_names(stock) + leaf_names(move))

    @pytest.mark.parametrize("shape", MATRICES)
    def test_a_matrix_of_stocks(self, shape):
        model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name=f"matrix_stock_{shape}")
        stock = model.stock("stock")
        setup(stock, shape)
        growth = model.flow("growth")
        setup(growth, shape)

        for name, leaf in zip(leaf_names(stock), leaf_names(growth)):
            model.flows[leaf].equation = model.stocks[name] * 0.1
            model.stocks[name].equation = model.flows[leaf]

        run_parity(model, leaf_names(stock))


# ---------------------------------------------------------------------------
# Mixed models, and the shapes both engines must refuse
# ---------------------------------------------------------------------------

class TestMixedAndRejected:
    @pytest.mark.parametrize("shape", SHAPES)
    def test_arrayed_and_scalar_entities_in_one_model(self, shape):
        model, v, s, w = build(shape, second=True)
        scaled = model.converter("scaled")
        scaled.equation = v * s
        total = model.converter("total")
        total.equation = scaled.arr_sum()
        share = model.converter("share")
        share.equation = total / v.arr_size()
        headroom = model.converter("headroom")
        headroom.equation = sd.max(total - s, 0.0)

        run_parity(model, leaf_names(scaled) + ["total", "share", "headroom"])

    def test_a_named_dot_is_rejected_before_either_engine_sees_it(self):
        """The rejection is in the operator, so both paths agree by construction."""
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="named_dot")
        left = model.constant("left")
        left.setup_named_vector({"p": 1.0, "q": 2.0})
        right = model.constant("right")
        right.setup_named_vector({"p": 3.0, "q": 4.0})

        with pytest.raises(Exception, match="not supported for named arrayed"):
            left.dot(right)

    def test_mixing_shapes_is_rejected_before_either_engine_sees_it(self):
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="mixed_shapes")
        vector = model.constant("vector")
        vector.setup_vector(3, [1.0, 2.0, 3.0])
        shorter = model.constant("shorter")
        shorter.setup_vector(2, [1.0, 2.0])

        with pytest.raises(Exception, match="different sizes"):
            vector + shorter


# ---------------------------------------------------------------------------
# Stochastic functions: parity of shape, not of value
# ---------------------------------------------------------------------------

STOCHASTIC = {
    "random": lambda model, v: sd.random(v, v * 2.0),
    "normal": lambda model, v: sd.normal(v, 1.0),
    "poisson": lambda model, v: sd.poisson(v),
    "exprnd": lambda model, v: sd.exprnd(v),
    "lognormal": lambda model, v: sd.lognormal(v / 10.0, 0.5),
    "triangular": lambda model, v: sd.triangular(v, v * 2.0, v * 3.0),
    "weibull": lambda model, v: sd.weibull(v, 1.0),
    "geometric": lambda model, v: sd.geometric(1.0 / v),
}


# Whether the parameter that differs between the two indices is a location or a scale,
# so that the index built on 1000 has to land far above the one built on 10. Measured
# per distribution rather than assumed: `weibull` is the exception, because there the
# array is the *shape* parameter and with scale 1.0 both indices concentrate just below
# one - a "larger parameter, larger draw" assertion would be wrong there, and flaky.
SCALES_WITH_ITS_PARAMETER = sorted(set(STOCHASTIC) - {"weibull"})


class TestStochasticOverArrays:
    """What parity can mean for a draw.

    The two engines use different generators, so equal values are not on offer and
    asserting them would be a lie. What must hold is that the *structure* survived:
    every index draws its own number, from its own parameters, on both engines. A
    silent collapse - all indices identical, or all zero - is what this catches.
    """

    HORIZON = 20.0

    def _draws(self, function, backend):
        model = Model(starttime=0.0, stoptime=self.HORIZON, dt=1.0,
                      name=f"stochastic_{function}_{backend}")
        v = model.constant("v")
        v.setup_named_vector({"small": 10.0, "large": 1000.0})
        target = model.converter("target")
        target.equation = STOCHASTIC[function](model, v)

        assert target.arrayed, f"{function} collapsed to a scalar"
        names = leaf_names(target)
        frame = model.simulate(names, backend=backend)
        return {name: [frame[name][t] for t in frame.index] for name in names}

    @pytest.mark.parametrize("function", sorted(STOCHASTIC))
    @pytest.mark.parametrize("backend", ["python", "rust"])
    def test_every_index_draws_its_own_number(self, function, backend):
        draws = self._draws(function, backend)

        for name, values in draws.items():
            assert all(value == value for value in values), f"{name} produced NaN"
            assert any(value != 0.0 for value in values), f"{name} is constantly zero"

        # Independent draws: a shared one would make the two indices equal at every
        # timestep, which is what a collapsed arrayed expression looks like.
        assert draws["target[small]"] != draws["target[large]"]

    @pytest.mark.parametrize("function", SCALES_WITH_ITS_PARAMETER)
    @pytest.mark.parametrize("backend", ["python", "rust"])
    def test_each_index_draws_from_its_own_parameter(self, function, backend):
        """The index built on 1000 lands far above the one built on 10.

        The measured ratio is around a hundred for all of these, so a factor of five
        is a wide margin - this is about the parameter reaching the right index, not
        about the precision of a sample mean.
        """
        draws = self._draws(function, backend)
        small = sum(draws["target[small]"]) / len(draws["target[small]"])
        large = sum(draws["target[large]"]) / len(draws["target[large]"])

        assert large > 5.0 * small, f"{function}: small={small}, large={large}"

    @pytest.mark.parametrize("backend", ["python", "rust"])
    def test_weibull_takes_the_array_as_its_shape(self, backend):
        """The exception to the test above, and the reason it is parametrized.

        `weibull(shape, scale)` takes the array as the shape, so both indices sit just
        below the scale of 1.0 - a large shape does not mean a large draw. Pinned so
        that the previous test's exclusion is a statement rather than an omission.
        """
        draws = self._draws("weibull", backend)

        for name, values in draws.items():
            assert all(0.0 < value < 3.0 for value in values), name
        mean = sum(draws["target[large]"]) / len(draws["target[large]"])
        assert 0.8 < mean < 1.2

    @pytest.mark.parametrize("backend", ["python", "rust"])
    def test_exprnd_treats_its_parameter_as_the_mean_on_both_engines(self, backend):
        """Measured, because the two readings differ by a factor of a hundred.

        `exprnd(10)` averages about 10 on both engines, so the parameter is the mean
        and not the rate - a rate of 10 would average 0.1. The engines agreeing on
        that reading is exactly the kind of thing a silent divergence would break.
        """
        model = Model(starttime=0.0, stoptime=200.0, dt=1.0, name=f"exprnd_{backend}")
        v = model.constant("v")
        v.setup_named_vector({"ten": 10.0})
        target = model.converter("target")
        target.equation = sd.exprnd(v)

        frame = model.simulate(["target[ten]"], backend=backend)
        mean = frame["target[ten]"].mean()
        assert 5.0 < mean < 20.0, mean

    @pytest.mark.parametrize("backend", ["python", "rust"])
    def test_bounded_draws_stay_inside_their_own_bounds(self, backend):
        """`random(v, 2v)` has bounds per index, which is checkable on both engines."""
        model = Model(starttime=0.0, stoptime=6.0, dt=1.0, name=f"bounds_{backend}")
        v = model.constant("v")
        v.setup_named_vector({"low": 4.0, "high": 100.0})
        target = model.converter("target")
        target.equation = sd.random(v, v * 2.0)

        frame = model.simulate(leaf_names(target), backend=backend)
        for name, lower in (("target[low]", 4.0), ("target[high]", 100.0)):
            for t in frame.index:
                assert lower <= frame[name][t] <= lower * 2.0, (
                    f"{name} at t={t} left [{lower}, {lower * 2.0}]")
