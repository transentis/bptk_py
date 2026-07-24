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


if __name__ == "__main__":
    unittest.main()
