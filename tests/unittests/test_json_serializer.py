"""Unit tests for BPTK_Py.sddsl.json_serializer.

Targets edge-case branches that the broader Rust-backend integration tests
do not exercise: UnaryOperator delegating to an inner element, left-handed
``-1.0 * x`` negation detection, unknown comparison sign error, ``If`` with
no else branch, and ``delay()`` without an initial value.
"""

import json
import unittest

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
from BPTK_Py.sddsl import operators as ops
from BPTK_Py.sddsl.json_serializer import _expr_to_json, model_to_json


class TestJsonSerializerEdgeCases(unittest.TestCase):
    def setUp(self):
        self.model = Model(starttime=0, stoptime=5, dt=1, name="json_edge")
        self.stock = self.model.stock("stock")
        self.stock.initial_value = 0.0
        self.constant = self.model.constant("c")
        self.constant.equation = 2.0

    def test_unary_operator_wrapping_element_delegates(self):
        """UnaryOperator wrapping a non-numeric Element must delegate to that element's serialization (json_serializer.py:76)."""
        wrapped = ops.UnaryOperator(self.constant)

        result = _expr_to_json(wrapped)

        self.assertEqual(result, {"type": "ref", "name": "c"})

    def test_left_handed_negation_via_numerical_multiplication(self):
        """NumericalMultiplicationOperator(-1.0, x) must be detected as a negation (json_serializer.py:103)."""
        expr = ops.NumericalMultiplicationOperator(-1.0, self.constant)

        result = _expr_to_json(expr)

        self.assertEqual(
            result,
            {"type": "unary_op", "op": "neg", "operand": {"type": "ref", "name": "c"}},
        )

    def test_unknown_comparison_sign_raises(self):
        """ComparisonOperator with an unknown sign must raise ValueError (json_serializer.py:133)."""
        bad = ops.ComparisonOperator(self.constant, 1.0, "??")

        with self.assertRaises(ValueError) as cm:
            _expr_to_json(bad)

        self.assertIn("Unknown comparison sign", str(cm.exception))
        self.assertIn("??", str(cm.exception))

    def test_if_without_else_defaults_to_zero_literal(self):
        """If with else_=None must serialize an implicit 0.0 literal as the else branch (json_serializer.py:146)."""
        condition = ops.ComparisonOperator(self.constant, 1.0, ">")
        if_expr = ops.If(condition, self.constant)  # else_ defaults to None

        result = _expr_to_json(if_expr)

        self.assertEqual(result["type"], "if")
        self.assertEqual(result["then"], {"type": "ref", "name": "c"})
        self.assertEqual(result["else"], {"type": "literal", "value": 0.0})

    def test_delay_without_initial_value_falls_back_to_input(self):
        """sd.delay(..., initial_value=None) must serialize the input ref as the initial value (json_serializer.py:300)."""
        flow = self.model.flow("flow")
        flow.equation = self.constant
        delayed = sd.delay(self.model, flow, 2.0)  # initial_value omitted

        result = _expr_to_json(delayed)

        self.assertEqual(result["type"], "call")
        self.assertEqual(result["function"], "delay")
        input_ref = {"type": "ref", "name": "flow"}
        # args = [input_ref, delay_duration, initial_value]
        self.assertEqual(result["args"][0], input_ref)
        self.assertEqual(result["args"][2], input_ref)

    def test_model_to_json_round_trips_through_delay_without_initial(self):
        """End-to-end: a model whose flow uses delay() without initial_value serializes cleanly."""
        flow = self.model.flow("flow")
        flow.equation = sd.delay(self.model, self.constant, 1.0)
        self.stock.equation = flow

        payload = json.loads(model_to_json(self.model))

        flow_entry = next(f for f in payload["entities"]["flows"] if f["name"] == "flow")
        delay_call = flow_entry["equation"]
        self.assertEqual(delay_call["function"], "delay")
        self.assertEqual(delay_call["args"][0], delay_call["args"][2])




def ref(name):
    return {"type": "ref", "name": name}


def lit(value):
    return {"type": "literal", "value": value}


def mul(left, right):
    return {"type": "binary_op", "op": "mul", "left": left, "right": right}


def add(left, right):
    return {"type": "binary_op", "op": "add", "left": left, "right": right}


class TestArrayedSerialization(unittest.TestCase):
    """Arrayed models reach the Rust engine.

    Two things used to stop them. Every array operator hit the catch-all and raised, and
    a parent arrayed element was emitted beside its sub-elements with a bogus
    `{"literal": 0.0}` equation. The engine itself stays array-agnostic: sub-elements
    flatten to bracket-named scalar entities and the aggregations become variadic calls.
    """

    def setUp(self):
        self.model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="arrayed_json")
        self.vector = self.model.constant("v")
        self.vector.setup_named_vector({"a": 4.0, "b": 9.0, "c": 2.0})
        self.matrix = self.model.constant("m")
        self.matrix.setup_matrix([2, 2], [[1.0, 2.0], [3.0, 4.0]])
        self.scalar = self.model.constant("s")
        self.scalar.equation = 5.0

    def _entities(self, model=None):
        payload = json.loads(model_to_json(model or self.model))
        return {kind: [entity["name"] for entity in entities]
                for kind, entities in payload["entities"].items()}

    # --- flattening -----------------------------------------------------------

    def test_only_the_leaves_become_entities(self):
        names = self._entities()["constants"]

        self.assertEqual(names, ["v[a]", "v[b]", "v[c]",
                                 "m[0][0]", "m[0][1]", "m[1][0]", "m[1][1]", "s"])
        self.assertNotIn("v", names)
        self.assertNotIn("m", names)
        self.assertNotIn("m[0]", names)   # a matrix row is a parent too

    def test_every_element_kind_skips_its_parents(self):
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="every_kind")
        for builder in (model.stock, model.flow, model.biflow,
                        model.converter, model.constant):
            element = builder(builder.__name__ + "_element")
            element.setup_named_vector({"x": 1.0, "y": 2.0})

        for kind, names in self._entities(model).items():
            self.assertTrue(names, kind)
            for name in names:
                self.assertTrue(name.endswith("[x]") or name.endswith("[y]"),
                                f"{kind}: {name} is a parent")

    def test_a_reference_to_a_parent_raises(self):
        with self.assertRaises(ValueError) as context:
            _expr_to_json(self.vector)

        self.assertIn("arrayed element 'v'", str(context.exception))

    # --- aggregations ---------------------------------------------------------

    def test_each_aggregation_becomes_a_variadic_call_over_the_leaves(self):
        leaves = [ref("v[a]"), ref("v[b]"), ref("v[c]")]
        for method, function in (("arr_sum", "arr_sum"), ("arr_prod", "arr_prod"),
                                 ("arr_mean", "arr_mean"), ("arr_median", "arr_median"),
                                 ("arr_stddev", "arr_stddev"), ("arr_max", "arr_max"),
                                 ("arr_min", "arr_min")):
            with self.subTest(method):
                self.assertEqual(
                    _expr_to_json(getattr(self.vector, method)()),
                    {"type": "call", "function": function, "args": leaves})

    def test_the_leaves_of_a_matrix_are_walked_depth_first(self):
        self.assertEqual(
            _expr_to_json(self.matrix.arr_sum()),
            {"type": "call", "function": "arr_sum",
             "args": [ref("m[0][0]"), ref("m[0][1]"), ref("m[1][0]"), ref("m[1][1]")]})

    def test_the_leaf_order_is_the_order_python_aggregates_in(self):
        """`arr_rank` and `arr_median` sort, so both engines must see one order.

        Checked against the Python term rather than restated: the names in the term
        string are the order the Python operator builds, and they have to match the
        order of the call's arguments.
        """
        import re

        for element in (self.vector, self.matrix):
            with self.subTest(element.name):
                json_order = [argument["name"] for argument
                              in _expr_to_json(element.arr_sum())["args"]]
                python_order = re.findall(r"memoize\('([^']+)'",
                                          element.arr_median().term())
                self.assertEqual(json_order, python_order)

    def test_arr_rank_carries_the_rank_as_its_last_argument(self):
        self.assertEqual(
            _expr_to_json(self.vector.arr_rank(2)),
            {"type": "call", "function": "arr_rank",
             "args": [ref("v[a]"), ref("v[b]"), ref("v[c]"), lit(2.0)]})

    def test_arr_size_folds_to_a_literal(self):
        # The vector size, not the leaf count: 2 for a 2x2 matrix, as in Python.
        self.assertEqual(_expr_to_json(self.vector.arr_size()), lit(3.0))
        self.assertEqual(_expr_to_json(self.matrix.arr_size()), lit(2.0))

    def test_a_scalar_operand_follows_the_python_operators(self):
        # arr_sum and arr_prod pass the value through; the others answer 0.0.
        self.assertEqual(
            _expr_to_json(self.scalar.arr_sum()),
            {"type": "call", "function": "arr_sum", "args": [ref("s")]})
        self.assertEqual(
            _expr_to_json(self.scalar.arr_prod()),
            {"type": "call", "function": "arr_prod", "args": [ref("s")]})
        for method in ("arr_mean", "arr_median", "arr_stddev", "arr_max", "arr_min"):
            with self.subTest(method):
                self.assertEqual(_expr_to_json(getattr(self.scalar, method)()), lit(0.0))
        self.assertEqual(_expr_to_json(self.scalar.arr_size()), lit(0.0))

    def test_a_partial_dimension_still_raises(self):
        from BPTK_Py.sddsl.operators import OperatorError

        with self.assertRaises(OperatorError):
            _expr_to_json(self.matrix.arr_sum(1))

    # --- dot ------------------------------------------------------------------

    def test_vector_dot_vector_expands_to_a_sum_of_products(self):
        other = self.model.constant("w")
        other.setup_vector(3, [1.0, 2.0, 3.0])
        left = self.model.constant("u")
        left.setup_vector(3, [4.0, 5.0, 6.0])

        self.assertEqual(
            _expr_to_json(left.dot(other)),
            add(add(mul(ref("u[0]"), ref("w[0]")),
                    mul(ref("u[1]"), ref("w[1]"))),
                mul(ref("u[2]"), ref("w[2]"))))

    def test_vector_dot_matrix_takes_one_column_per_index(self):
        weights = self.model.constant("weights")
        weights.setup_vector(2, [0.5, 1.5])
        target = self.model.converter("weighted")
        target.equation = weights.dot(self.matrix)

        self.assertEqual(
            _expr_to_json(target[1].equation),
            add(mul(ref("weights[0]"), ref("m[0][1]")),
                mul(ref("weights[1]"), ref("m[1][1]"))))

    def test_matrix_dot_vector_takes_one_row_per_index(self):
        weights = self.model.constant("weights")
        weights.setup_vector(2, [0.5, 1.5])
        target = self.model.converter("rows")
        target.equation = self.matrix.dot(weights)

        self.assertEqual(
            _expr_to_json(target[1].equation),
            add(mul(ref("m[1][0]"), ref("weights[0]")),
                mul(ref("m[1][1]"), ref("weights[1]"))))

    def test_matrix_dot_matrix_pairs_a_row_with_a_column(self):
        other = self.model.constant("n")
        other.setup_matrix([2, 2], [[5.0, 6.0], [7.0, 8.0]])
        target = self.model.converter("product")
        target.equation = self.matrix.dot(other)

        self.assertEqual(
            _expr_to_json(target[1][0].equation),
            add(mul(ref("m[1][0]"), ref("n[0][0]")),
                mul(ref("m[1][1]"), ref("n[1][0]"))))

    def test_a_value_on_either_side_of_a_dot_is_one_product(self):
        # An unnamed vector: `dot` rejects named arrays in its constructor.
        unnamed = self.model.constant("u")
        unnamed.setup_vector(2, [1.0, 2.0])

        self.assertEqual(
            _expr_to_json(ops.DotOperator(self.scalar, unnamed, [1])),
            mul(ref("s"), ref("u[1]")))
        self.assertEqual(
            _expr_to_json(ops.DotOperator(unnamed, self.scalar, [1])),
            mul(ref("u[1]"), ref("s")))

    def test_an_expression_as_a_dot_operand_is_cloned_to_its_leaves(self):
        left = self.model.constant("u")
        left.setup_vector(2, [1.0, 2.0])
        right = self.model.constant("w")
        right.setup_vector(2, [3.0, 4.0])
        target = self.model.converter("combined")
        target.equation = ops.DotOperator(left + right, self.matrix)

        self.assertEqual(
            _expr_to_json(target[0].equation),
            add(mul(add(ref("u[0]"), ref("w[0]")), ref("m[0][0]")),
                mul(add(ref("u[1]"), ref("w[1]")), ref("m[1][0]"))))

    def test_the_dot_shapes_that_cannot_be_serialized_raise(self):
        other = self.model.constant("n")
        other.setup_matrix([2, 2], [[5.0, 6.0], [7.0, 8.0]])
        second_scalar = self.model.constant("s2")
        second_scalar.equation = 1.0
        short = self.model.constant("short")
        short.setup_vector(2, [1.0, 2.0])
        long_vector = self.model.constant("long")
        long_vector.setup_vector(3, [1.0, 2.0, 3.0])

        cases = {
            "two values": ops.DotOperator(self.scalar, second_scalar),
            "value and an array without an index":
                ops.DotOperator(self.scalar, short),
            "array without an index":
                ops.DotOperator(short, self.matrix),
            "two-element index":
                ops.DotOperator(self.matrix, other, 0),
            # `dot` allows different sizes at construction and checks them per shape.
            "vectors of sizes": ops.DotOperator(short, long_vector),
        }
        for expected, expression in cases.items():
            with self.subTest(expected):
                with self.assertRaises(ValueError) as context:
                    _expr_to_json(expression)
                self.assertIn(expected, str(context.exception))

    def test_an_empty_dot_product_raises(self):
        """A guard on the helper: every shape above builds at least one pair."""
        from BPTK_Py.sddsl.json_serializer import _sum_of_products

        with self.assertRaises(ValueError) as context:
            _sum_of_products([])

        self.assertIn("empty dot product", str(context.exception))

    # --- the whole model ------------------------------------------------------

    def test_an_arrayed_model_round_trips(self):
        total = self.model.converter("total")
        total.equation = self.vector.arr_sum()
        scaled = self.model.converter("scaled")
        scaled.equation = self.vector * 2.0

        payload = json.loads(model_to_json(self.model))
        converters = {entity["name"]: entity["equation"]
                      for entity in payload["entities"]["converters"]}

        self.assertEqual(sorted(converters),
                         ["scaled[a]", "scaled[b]", "scaled[c]", "total"])
        self.assertEqual(converters["total"]["function"], "arr_sum")
        # The element stays on the left, the literal on the right.
        self.assertEqual(converters["scaled[b]"],
                         mul(ref("v[b]"), lit(2.0)))


if __name__ == "__main__":
    unittest.main()
