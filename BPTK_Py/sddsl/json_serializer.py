"""
Serialize an SD DSL Model to the JSON model format used by the Rust engine.

Usage:
    from BPTK_Py import Model
    model = Model(starttime=0, stoptime=10, dt=1, name="my_model")
    # ... define model ...
    json_str = model.to_json()

The JSON format matches the schema in engine/schema/sd_model_v1.json.

Arrayed elements are supported: sub-elements flatten to bracket-named scalar entities
(`name[label]`, nested `name[row][col]` for a matrix), the parent element is skipped, and
the aggregations become variadic `arr_*` calls. The engine therefore needs to know
nothing about dimensions. `dot` is expanded into a sum of products here rather than
becoming a call.
"""

import json
from . import operators as ops
from .element import Element
from .stock import Stock
from .flow import Flow
from .biflow import Biflow
from .converter import Converter
from .constant import Constant


# ── Inline lookup table tracking ────────────────────────────────────────────

_inline_tables = {}
_inline_counter = 0


def _next_inline_id():
    global _inline_counter
    _inline_counter += 1
    return _inline_counter


def _reset_inline_tables():
    global _inline_tables, _inline_counter
    _inline_tables = {}
    _inline_counter = 0


# ── Comparison sign → JSON op mapping ────────────────────────────────────────

_COMPARISON_SIGN_MAP = {
    ">": "gt",
    "<": "lt",
    ">=": "gte",
    "<=": "lte",
    "==": "eq",
    "!=": "neq",
}


# ── Arrayed elements ─────────────────────────────────────────────────────────

def _leaf_refs(element):
    """
    JSON for every leaf of an arrayed element, in the parent's key order.

    The order is part of the contract: `arr_rank` and `arr_median` sort, and the two
    engines have to sort the same list. A matrix is walked depth-first, which is the
    order `_matrix_element_to_string` uses on the Python side.
    """
    if element._elements.vector_size() == 0:
        return [_expr_to_json(element)]

    refs = []
    for key in element._elements.equations:
        refs.extend(_leaf_refs(element[key]))
    return refs


def _aggregation_to_json(function, element, extra_args=(), scalar_input="zero"):
    """
    An aggregation as a variadic call over the leaves of its arrayed operand.

    An operand with no sub-elements follows the Python operators exactly: `arr_sum` and
    `arr_prod` pass the scalar through, every other aggregation answers 0.0.
    """
    if element._elements.vector_size() == 0 and scalar_input == "zero":
        return {"type": "literal", "value": 0.0}

    return {"type": "call", "function": function,
            "args": _leaf_refs(element) + list(extra_args)}


def _product(left, right):
    return {"type": "binary_op", "op": "mul", "left": left, "right": right}


def _sum_of_products(pairs):
    """`a1*b1 + a2*b2 + ...`, left-associative like the Python term."""
    if not pairs:
        raise ValueError("Cannot serialize an empty dot product.")

    result = _product(*pairs[0])
    for pair in pairs[1:]:
        result = {"type": "binary_op", "op": "add",
                  "left": result, "right": _product(*pair)}
    return result


def _dot_operand_at(operand, position):
    """One leaf of a `dot` operand, addressed by a list of indices."""
    if isinstance(operand, Element):
        current = operand
        for key in position:
            current = current[key]
        return _expr_to_json(current)
    return _expr_to_json(operand.clone_with_index(position))


def _dot_to_json(expr):
    """
    `dot` as the sum of products that `DotOperator.term()` writes as a string.

    The engine gets no `dot` builtin: the expansion is decided here, by the same
    dimension rules the Python operator applies, and what reaches Rust is ordinary
    scalar arithmetic over flattened entities. Named arrays never arrive - `DotOperator`
    rejects them in its constructor - so a shape this function cannot map raises, and
    the runner falls back.
    """
    dimensions_1 = ops._get_element_dimensions(expr.element_1)
    dimensions_2 = ops._get_element_dimensions(expr.element_2)
    index = expr.index

    def is_vector(dimensions):
        return len(dimensions) == 1 or dimensions[1] == 0

    if dimensions_1 == -1 or dimensions_2 == -1:
        # A value on one side: one product with the leaf at this index.
        if dimensions_1 == -1 and dimensions_2 == -1 or index is None:
            raise ValueError(
                "Cannot serialize a dot product of two values - use * instead."
                if dimensions_1 == -1 and dimensions_2 == -1 else
                "Cannot serialize a dot product of a value and an array without an index."
            )
        if dimensions_1 == -1:
            return _product(_expr_to_json(expr.element_1),
                            _dot_operand_at(expr.element_2, index))
        return _product(_dot_operand_at(expr.element_1, index),
                        _expr_to_json(expr.element_2))

    if is_vector(dimensions_1) and is_vector(dimensions_2):
        # vector . vector -> a scalar, so this one carries no index.
        if dimensions_1[0] != dimensions_2[0]:
            raise ValueError(
                "Cannot serialize a dot product of vectors of sizes {} and {}.".format(
                    dimensions_1[0], dimensions_2[0]))
        return _sum_of_products([
            (_dot_operand_at(expr.element_1, [i]),
             _dot_operand_at(expr.element_2, [i]))
            for i in range(dimensions_1[0])])

    if index is None:
        # Every remaining shape yields an array, so each sub-element holds a clone that
        # knows its index. Without one there is nothing to serialize.
        raise ValueError(
            "Cannot serialize a dot product that yields an array without an index.")

    if is_vector(dimensions_1):
        # vector . matrix -> one column of the matrix per index.
        position = index if isinstance(index, int) else index[0]
        return _sum_of_products([
            (_dot_operand_at(expr.element_1, [k]),
             _dot_operand_at(expr.element_2, [k, position]))
            for k in range(dimensions_2[0])])

    if is_vector(dimensions_2):
        # matrix . vector -> one row of the matrix per index.
        position = index if isinstance(index, int) else index[0]
        return _sum_of_products([
            (_dot_operand_at(expr.element_1, [position, k]),
             _dot_operand_at(expr.element_2, [k]))
            for k in range(dimensions_1[1])])

    # matrix . matrix -> a row of the left and a column of the right.
    if isinstance(index, int) or len(index) != 2:
        raise ValueError(
            "Cannot serialize a matrix dot product with the index {}; "
            "a two-element index is required.".format(index))
    return _sum_of_products([
        (_dot_operand_at(expr.element_1, [index[0], k]),
         _dot_operand_at(expr.element_2, [k, index[1]]))
        for k in range(dimensions_1[1])])


# ── Expression serializer ────────────────────────────────────────────────────

def _expr_to_json(expr):
    """
    Recursively convert an SD DSL expression tree to a JSON-compatible dict.

    Handles: literals, element references, the array aggregations, `dot`, and all
    operators and built-in functions that the Rust engine supports. Raises ValueError
    for nodes the engine cannot express - a custom function, or a reference to the
    parent of an arrayed element - which makes the runner fall back to the Python
    engine.
    """

    # ── Scalar literals ──────────────────────────────────────────────────
    if isinstance(expr, (int, float)):
        return {"type": "literal", "value": float(expr)}

    # ── None (default stock equation = 0 net flow) ───────────────────────
    if expr is None:
        return {"type": "literal", "value": 0.0}

    # ── UnaryOperator: wraps a scalar or delegates to inner element ──────
    if type(expr) is ops.UnaryOperator:
        if isinstance(expr.element, (int, float)):
            return {"type": "literal", "value": float(expr.element)}
        return _expr_to_json(expr.element)

    # ── Element references (Stock, Flow, Converter, Constant) ────────────
    if isinstance(expr, Element):
        if expr.arrayed:
            # The parent of an arrayed element is not an entity in the JSON - only its
            # sub-elements are - so a reference to it would dangle. Nothing in the DSL
            # produces one today (aggregations are expanded leaf by leaf below), so this
            # is a guard: raising makes the runner fall back instead of loading a model
            # with an unresolvable reference.
            raise ValueError(
                f"Cannot serialize a reference to the arrayed element '{expr.name}'. "
                f"Only its sub-elements are entities in the JSON model."
            )
        return {"type": "ref", "name": expr.name}

    # ── Array aggregations: array in, one number out ─────────────────────
    if isinstance(expr, ops.ArraySumOperator):
        ops._check_aggregation_dimensions("arr_sum", expr.element, expr.dimensions)
        return _aggregation_to_json("arr_sum", expr.element, scalar_input="pass_through")

    if isinstance(expr, ops.ArrayProductOperator):
        ops._check_aggregation_dimensions("arr_prod", expr.element, expr.dimensions)
        return _aggregation_to_json("arr_prod", expr.element, scalar_input="pass_through")

    if isinstance(expr, ops.ArrayMeanOperator):
        return _aggregation_to_json("arr_mean", expr.element)

    if isinstance(expr, ops.ArrayMedianOperator):
        return _aggregation_to_json("arr_median", expr.element)

    if isinstance(expr, ops.ArrayStandardDeviationOperator):
        return _aggregation_to_json("arr_stddev", expr.element)

    if isinstance(expr, ops.ArrayMaxOperator):
        return _aggregation_to_json("arr_max", expr.element)

    if isinstance(expr, ops.ArrayMinOperator):
        return _aggregation_to_json("arr_min", expr.element)

    if isinstance(expr, ops.ArrayRankOperator):
        # The rank is the last argument, after the leaves.
        return _aggregation_to_json("arr_rank", expr.element,
                                    extra_args=[_expr_to_json(expr.rank)])

    if isinstance(expr, ops.ArraySizeOperator):
        # Folded here: the size is known at serialization time, and it is the vector
        # size rather than the leaf count - 2 for a 2x2 matrix, as in Python.
        return {"type": "literal",
                "value": float(expr.element._elements.vector_size())}

    # ── dot: expanded into a sum of products ─────────────────────────────
    if isinstance(expr, ops.DotOperator):
        return _dot_to_json(expr)

    # ── Binary arithmetic operators ──────────────────────────────────────
    if isinstance(expr, ops.AdditionOperator):
        return {"type": "binary_op", "op": "add",
                "left": _expr_to_json(expr.element_1),
                "right": _expr_to_json(expr.element_2)}

    if isinstance(expr, ops.SubtractionOperator):
        return {"type": "binary_op", "op": "sub",
                "left": _expr_to_json(expr.element_1),
                "right": _expr_to_json(expr.element_2)}

    # NumericalMultiplicationOperator must be checked BEFORE MultiplicationOperator
    # (it's a subclass). Detect negation pattern: element * -1.0 → neg(element).
    if isinstance(expr, ops.NumericalMultiplicationOperator):
        e1 = expr.element_1
        e2 = expr.element_2
        # Check for negation pattern: x * (-1.0)
        if isinstance(e2, ops.UnaryOperator) and isinstance(e2.element, (int, float)) and e2.element == -1.0:
            return {"type": "unary_op", "op": "neg",
                    "operand": _expr_to_json(e1)}
        if isinstance(e1, ops.UnaryOperator) and isinstance(e1.element, (int, float)) and e1.element == -1.0:
            return {"type": "unary_op", "op": "neg",
                    "operand": _expr_to_json(e2)}
        return {"type": "binary_op", "op": "mul",
                "left": _expr_to_json(e1),
                "right": _expr_to_json(e2)}

    if isinstance(expr, ops.MultiplicationOperator):
        return {"type": "binary_op", "op": "mul",
                "left": _expr_to_json(expr.element_1),
                "right": _expr_to_json(expr.element_2)}

    if isinstance(expr, ops.DivisionOperator):
        return {"type": "binary_op", "op": "div",
                "left": _expr_to_json(expr.element_1),
                "right": _expr_to_json(expr.element_2)}

    if isinstance(expr, ops.PowerOperator):
        return {"type": "binary_op", "op": "pow",
                "left": _expr_to_json(expr.element),
                "right": _expr_to_json(expr.power)}

    if isinstance(expr, ops.ModOperator):
        return {"type": "binary_op", "op": "mod",
                "left": _expr_to_json(expr.element_1),
                "right": _expr_to_json(expr.element_2)}

    # ── Comparison operators ─────────────────────────────────────────────
    if isinstance(expr, ops.ComparisonOperator):
        op = _COMPARISON_SIGN_MAP.get(expr.sign)
        if op is None:
            raise ValueError(f"Unknown comparison sign: {expr.sign}")
        return {"type": "binary_op", "op": op,
                "left": _expr_to_json(expr.element_1),
                "right": _expr_to_json(expr.element_2)}

    # ── Conditional / logical ────────────────────────────────────────────
    if isinstance(expr, ops.If):
        result = {"type": "if",
                  "condition": _expr_to_json(expr.if_),
                  "then": _expr_to_json(expr.then_)}
        if expr.else_ is not None:
            result["else"] = _expr_to_json(expr.else_)
        else:
            result["else"] = {"type": "literal", "value": 0.0}
        return result

    if isinstance(expr, ops.And):
        return {"type": "binary_op", "op": "and",
                "left": _expr_to_json(expr.lhs),
                "right": _expr_to_json(expr.rhs)}

    if isinstance(expr, ops.Or):
        return {"type": "binary_op", "op": "or",
                "left": _expr_to_json(expr.lhs),
                "right": _expr_to_json(expr.rhs)}

    if isinstance(expr, ops.Not):
        return {"type": "unary_op", "op": "not",
                "operand": _expr_to_json(expr.condition)}

    # ── Temporal functions ───────────────────────────────────────────────
    if isinstance(expr, ops.Time):
        return {"type": "call", "function": "time", "args": []}

    if isinstance(expr, ops.DT):
        return {"type": "call", "function": "dt", "args": []}

    if isinstance(expr, ops.Starttime):
        return {"type": "call", "function": "starttime", "args": []}

    if isinstance(expr, ops.Stoptime):
        return {"type": "call", "function": "stoptime", "args": []}

    # ── Math functions (single argument) ─────────────────────────────────
    if isinstance(expr, ops.AbsOperator):
        return {"type": "call", "function": "abs",
                "args": [_expr_to_json(expr.element)]}

    if isinstance(expr, ops.Sqrt):
        return {"type": "call", "function": "sqrt",
                "args": [_expr_to_json(expr.x)]}

    if isinstance(expr, ops.Exp):
        return {"type": "call", "function": "exp",
                "args": [_expr_to_json(expr.element)]}

    if isinstance(expr, ops.Sin):
        return {"type": "call", "function": "sin",
                "args": [_expr_to_json(expr.x)]}

    if isinstance(expr, ops.Cos):
        return {"type": "call", "function": "cos",
                "args": [_expr_to_json(expr.x)]}

    if isinstance(expr, ops.Tan):
        return {"type": "call", "function": "tan",
                "args": [_expr_to_json(expr.x)]}

    if isinstance(expr, ops.Arcsin):
        return {"type": "call", "function": "arcsin",
                "args": [_expr_to_json(expr.x)]}

    if isinstance(expr, ops.Arccos):
        return {"type": "call", "function": "arccos",
                "args": [_expr_to_json(expr.x)]}

    if isinstance(expr, ops.Arctan):
        return {"type": "call", "function": "arctan",
                "args": [_expr_to_json(expr.x)]}

    if isinstance(expr, ops.Pi):
        return {"type": "call", "function": "pi", "args": []}

    if isinstance(expr, ops.Ln):
        return {"type": "call", "function": "ln",
                "args": [_expr_to_json(expr.x)]}

    if isinstance(expr, ops.Log10):
        return {"type": "call", "function": "log10",
                "args": [_expr_to_json(expr.x)]}

    if isinstance(expr, ops.Floor):
        return {"type": "call", "function": "floor",
                "args": [_expr_to_json(expr.x)]}

    if isinstance(expr, ops.Ceil):
        return {"type": "call", "function": "ceil",
                "args": [_expr_to_json(expr.x)]}

    if isinstance(expr, ops.Round):
        return {"type": "call", "function": "round",
                "args": [_expr_to_json(expr.operator), _expr_to_json(expr.digits)]}

    # ── Math functions (two arguments) ───────────────────────────────────
    if isinstance(expr, ops.MaxOperator):
        return {"type": "call", "function": "max",
                "args": [_expr_to_json(expr.element_1),
                         _expr_to_json(expr.element_2)]}

    if isinstance(expr, ops.MinOperator):
        return {"type": "call", "function": "min",
                "args": [_expr_to_json(expr.element_1),
                         _expr_to_json(expr.element_2)]}

    # ── Wave functions ───────────────────────────────────────────────────
    if isinstance(expr, ops.Sinwave):
        return {"type": "call", "function": "sinwave",
                "args": [_expr_to_json(expr.amplitude),
                         _expr_to_json(expr.period)]}

    if isinstance(expr, ops.Coswave):
        return {"type": "call", "function": "coswave",
                "args": [_expr_to_json(expr.amplitude),
                         _expr_to_json(expr.period)]}

    # ── Control functions ────────────────────────────────────────────────
    if isinstance(expr, ops.Step):
        return {"type": "call", "function": "step",
                "args": [_expr_to_json(expr.height),
                         _expr_to_json(expr.timestep)]}

    if isinstance(expr, ops.Pulse):
        return {"type": "call", "function": "pulse",
                "args": [_expr_to_json(expr.volume),
                         _expr_to_json(expr.first_pulse),
                         _expr_to_json(expr.interval)]}

    # ── Lookup function ──────────────────────────────────────────────────
    if isinstance(expr, ops.Lookup):
        points = expr.points
        # points is either a string (table name reference) or a list
        if isinstance(points, str):
            # Strip surrounding quotes if present (Lookup.__init__ adds them)
            table_name = points.strip('"')
        else:
            # Inline points — auto-generate a unique table name and register
            table_name = f"_inline_lookup_{_next_inline_id()}"
            _inline_tables[table_name] = points
        return {"type": "call", "function": "lookup",
                "args": [_expr_to_json(expr.element),
                         {"type": "literal", "value": table_name}]}

    # ── Smooth: output is the internal stock ─────────────────────────────
    if isinstance(expr, ops.Smooth):
        return {"type": "ref", "name": expr.smooth.name}

    # ── Trend: output is the internal converter ────────────────────────
    if isinstance(expr, ops.Trend):
        return {"type": "ref", "name": expr.trend.name}

    # ── Delay: memo-table lookback ───────────────────────────────────
    if isinstance(expr, ops.Delay):
        input_ref = {"type": "ref", "name": expr.input_function.name}
        delay_duration = _expr_to_json(expr.delay_duration)
        if expr.initial_value is not None:
            initial_value = _expr_to_json(expr.initial_value)
        else:
            initial_value = input_ref
        return {"type": "call", "function": "delay",
                "args": [input_ref, delay_duration, initial_value]}

    # ── Combinatorial & special functions ────────────────────────────────
    if isinstance(expr, ops.Combinations):
        return {"type": "call", "function": "combinations",
                "args": [_expr_to_json(expr.n), _expr_to_json(expr.r)]}

    if isinstance(expr, ops.Permutations):
        return {"type": "call", "function": "permutations",
                "args": [_expr_to_json(expr.n), _expr_to_json(expr.r)]}

    if isinstance(expr, ops.Factorial):
        return {"type": "call", "function": "factorial",
                "args": [_expr_to_json(expr.n)]}

    if isinstance(expr, ops.GammaLN):
        return {"type": "call", "function": "gammaln",
                "args": [_expr_to_json(expr.n)]}

    if isinstance(expr, ops.Inf):
        return {"type": "call", "function": "inf", "args": []}

    if isinstance(expr, ops.Nan):
        return {"type": "call", "function": "nan", "args": []}

    # ── Statistical functions ────────────────────────────────────────────
    if isinstance(expr, ops.Random):
        return {"type": "call", "function": "random",
                "args": [_expr_to_json(expr.min_value), _expr_to_json(expr.max_value)]}

    if isinstance(expr, ops.Normal):
        return {"type": "call", "function": "normal",
                "args": [_expr_to_json(expr.mean), _expr_to_json(expr.stddev)]}

    if isinstance(expr, ops.Beta):
        return {"type": "call", "function": "beta",
                "args": [_expr_to_json(expr.a), _expr_to_json(expr.b)]}

    if isinstance(expr, ops.Binomial):
        return {"type": "call", "function": "binomial",
                "args": [_expr_to_json(expr.n), _expr_to_json(expr.p)]}

    if isinstance(expr, ops.NegBinomial):
        return {"type": "call", "function": "negbinomial",
                "args": [_expr_to_json(expr.n), _expr_to_json(expr.p)]}

    if isinstance(expr, ops.Exprnd):
        return {"type": "call", "function": "exprnd",
                "args": [_expr_to_json(expr.l)]}

    if isinstance(expr, ops.Gamma):
        return {"type": "call", "function": "gamma_dist",
                "args": [_expr_to_json(expr.shape), _expr_to_json(expr.scale)]}

    if isinstance(expr, ops.Geometric):
        return {"type": "call", "function": "geometric",
                "args": [_expr_to_json(expr.p)]}

    if isinstance(expr, ops.Lognormal):
        return {"type": "call", "function": "lognormal",
                "args": [_expr_to_json(expr.mean), _expr_to_json(expr.stddev)]}

    if isinstance(expr, ops.Logistic):
        return {"type": "call", "function": "logistic",
                "args": [_expr_to_json(expr.mean), _expr_to_json(expr.scale)]}

    if isinstance(expr, ops.Montecarlo):
        return {"type": "call", "function": "montecarlo",
                "args": [_expr_to_json(expr.p)]}

    if isinstance(expr, ops.Poisson):
        return {"type": "call", "function": "poisson",
                "args": [_expr_to_json(expr.mu)]}

    if isinstance(expr, ops.Triangular):
        return {"type": "call", "function": "triangular",
                "args": [_expr_to_json(expr.lower_bound),
                         _expr_to_json(expr.mode),
                         _expr_to_json(expr.upper_bound)]}

    if isinstance(expr, ops.Weibull):
        return {"type": "call", "function": "weibull",
                "args": [_expr_to_json(expr.shape), _expr_to_json(expr.scale)]}

    if isinstance(expr, ops.Pareto):
        return {"type": "call", "function": "pareto",
                "args": [_expr_to_json(expr.shape), _expr_to_json(expr.scale)]}

    if isinstance(expr, ops.Invnorm):
        args = [_expr_to_json(expr.p)]
        if expr.mean is not None:
            args.append(_expr_to_json(expr.mean))
        if expr.stddev is not None:
            args.append(_expr_to_json(expr.stddev))
        return {"type": "call", "function": "invnorm", "args": args}

    if isinstance(expr, ops.NormalCDF):
        return {"type": "call", "function": "normalcdf",
                "args": [_expr_to_json(expr.left), _expr_to_json(expr.right),
                         _expr_to_json(expr.mean), _expr_to_json(expr.stddev)]}

    # ── Unsupported: custom functions ────────────────────────────────────
    if isinstance(expr, ops.NaryOperator):
        raise ValueError(
            f"Custom function '{expr.name}' is not supported by to_json(). "
            f"The Rust engine does not support user-defined functions."
        )

    # ── Fallback ─────────────────────────────────────────────────────────
    raise ValueError(
        f"Cannot serialize expression of type {type(expr).__name__} to JSON. "
        f"This operator/function is not yet supported."
    )


# ── Model serializer ─────────────────────────────────────────────────────────

def model_to_json(model) -> str:
    """
    Serialize an SD DSL Model to the JSON format expected by the Rust engine.

    Arrayed elements are flattened: every sub-element is an entity of its own, named
    with brackets, and the parent is skipped - it holds no equation, only its
    sub-elements do.

    Returns a JSON string. Raises ValueError if the model uses features the Rust engine
    cannot express, such as a custom function.
    """
    _reset_inline_tables()

    specs = {
        "starttime": model.starttime,
        "stoptime": model.stoptime,
        "dt": model.dt,
    }

    entities = {}

    # ── Stocks ───────────────────────────────────────────────────────────
    if model.stocks:
        stocks_list = []
        for name, stock in model.stocks.items():
            if stock.arrayed:
                # The parent of an arrayed element carries no equation - its
                # sub-elements are entities of their own, already in this dict. It used
                # to be emitted with a bogus {"literal": 0.0} beside the real ones.
                continue
            initial_value = stock.initial_value
            # initial_value can be a float, Constant, or Converter
            initial_value_json = _expr_to_json(initial_value)
            equation_json = _expr_to_json(stock.equation)
            stocks_list.append({
                "name": name,
                "initial_value": initial_value_json,
                "equation": equation_json,
            })
        entities["stocks"] = stocks_list

    # ── Flows ────────────────────────────────────────────────────────────
    if model.flows:
        flows_list = []
        for name, flow in model.flows.items():
            if flow.arrayed:
                continue  # A parent arrayed element is not an entity - see stocks.
            flows_list.append({
                "name": name,
                "equation": _expr_to_json(flow.equation),
            })
        entities["flows"] = flows_list

    # ── Biflows ──────────────────────────────────────────────────────────
    if model.biflows:
        biflows_list = []
        for name, biflow in model.biflows.items():
            if biflow.arrayed:
                continue  # A parent arrayed element is not an entity - see stocks.
            biflows_list.append({
                "name": name,
                "equation": _expr_to_json(biflow.equation),
            })
        entities["biflows"] = biflows_list

    # ── Converters ───────────────────────────────────────────────────────
    if model.converters:
        converters_list = []
        for name, converter in model.converters.items():
            if converter.arrayed:
                continue  # A parent arrayed element is not an entity - see stocks.
            converters_list.append({
                "name": name,
                "equation": _expr_to_json(converter.equation),
            })
        entities["converters"] = converters_list

    # ── Constants ────────────────────────────────────────────────────────
    if model.constants:
        constants_list = []
        for name, constant in model.constants.items():
            if constant.arrayed:
                continue  # A parent arrayed element is not an entity - see stocks.
            constants_list.append({
                "name": name,
                "equation": _expr_to_json(constant.equation),
            })
        entities["constants"] = constants_list

    # ── Build model dict ─────────────────────────────────────────────────
    model_dict = {
        "name": model.name,
        "specs": specs,
        "entities": entities,
    }

    # ── Graphical functions (lookup tables) ──────────────────────────────
    all_points = dict(model.points) if model.points else {}
    all_points.update(_inline_tables)
    if all_points:
        gf = {}
        for table_name, points in all_points.items():
            gf[table_name] = {"points": points}
        model_dict["graphical_functions"] = gf

    return json.dumps(model_dict)
