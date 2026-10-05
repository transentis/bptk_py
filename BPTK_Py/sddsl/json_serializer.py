"""
Serialize an SD DSL Model to the JSON model format used by the Rust engine.

Usage:
    from BPTK_Py import Model
    model = Model(starttime=0, stoptime=10, dt=1, name="my_model")
    # ... define model ...
    json_str = model.to_json()

Arrayed elements are supported: sub-elements flatten to bracket-named scalar entities
(`name[label]`, nested `name[row][col]` for a matrix), the parent element is skipped, and
the aggregations become variadic `arr_*` calls. The engine therefore needs to know
nothing about dimensions. `dot` is expanded into a sum of products here rather than
becoming a call.
"""

import inspect
import json
import threading
from . import operators as ops
from .element import Element


# ── Inline lookup table tracking ────────────────────────────────────────────

_inline_tables = {}
_inline_counter = 0

# The model being serialized. A custom function is emitted by name, and that name has to be
# checked against the callable the model holds for it - which `_expr_to_json` cannot reach,
# taking an expression and recursing through dozens of call sites.
_current_model = None


# The state above is per serialization, but module-wide. One serialization at a time, so
# that two threads - two server sessions, say - cannot interleave and mix their tables
# and models.
_serialization_lock = threading.Lock()


def _next_inline_id():
    global _inline_counter
    _inline_counter += 1
    return _inline_counter


def _reset_inline_tables():
    global _inline_tables, _inline_counter
    _inline_tables = {}
    _inline_counter = 0


def _set_current_model(model):
    global _current_model
    _current_model = model


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

    The engine gets no `dot` builtin: the operator itself decides the shape and the keys
    to sum over, and this function renders the same expansion as JSON, so that what
    reaches Rust is ordinary scalar arithmetic over flattened entities. Named arrays take
    exactly this path - a label addresses a bracket-named entity the way a position does.
    """
    try:
        kind, contracted, free = expr._shape()
    except Exception as error:
        # Everything this function raises has to be a ValueError, because that is what
        # the runner turns into a RustBackendError naming the cause. The operator itself
        # raises plain exceptions, and an invalid product reaches this point only when
        # an operator is serialized without ever having been assigned as an equation.
        raise ValueError("Cannot serialize this dot product: {}".format(error))

    if expr.index is None:
        index = []
    elif isinstance(expr.index, (list, tuple)):
        index = list(expr.index)
    else:
        index = [expr.index]

    def operands(keys_1, keys_2):
        return (_dot_operand_at(expr.element_1, keys_1),
                _dot_operand_at(expr.element_2, keys_2))

    if kind == "vector_vector":
        # A scalar result, so this one carries no index.
        return _sum_of_products([operands([key], [key]) for key in contracted])

    if not index:
        # Every remaining shape yields an array, so each sub-element holds a clone that
        # knows its index. Without one there is nothing to serialize.
        if kind in ("value_array", "array_value"):
            raise ValueError(
                "Cannot serialize a dot product of a value and an array without an index.")
        raise ValueError(
            "Cannot serialize a dot product that yields an array without an index.")

    if kind == "value_array":
        return _product(_expr_to_json(expr.element_1),
                        _dot_operand_at(expr.element_2, index))
    if kind == "array_value":
        return _product(_dot_operand_at(expr.element_1, index),
                        _expr_to_json(expr.element_2))

    if kind == "vector_matrix":
        # vector . matrix -> one column of the matrix per index.
        return _sum_of_products(
            [operands([key], [key, index[0]]) for key in contracted])

    if kind == "matrix_vector":
        # matrix . vector -> one row of the matrix per index.
        return _sum_of_products(
            [operands([index[0], key], [key]) for key in contracted])

    # matrix . matrix -> a row of the left and a column of the right.
    if len(index) != 2:
        raise ValueError(
            "Cannot serialize a matrix dot product with the index {}; "
            "a two-element index is required.".format(expr.index))
    return _sum_of_products(
        [operands([index[0], key], [key, index[1]]) for key in contracted])


# ── Custom functions ─────────────────────────────────────────────────────────

def _check_call_site_arity(fn, name, argument_count):
    """
    Check that `fn` accepts what the call site passes: the model, the time, and the
    arguments of the expression.

    The signature itself is not the criterion. `lambda model, t, *args: ...` is a
    perfectly well defined custom function and three test fixtures use one, so what
    matters is whether a call of this shape binds, not whether the parameters are
    counted out.
    """
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        # A built-in or a C callable has no signature to inspect. Nothing to check,
        # and refusing it here would be a rule the Python engine does not have.
        return

    try:
        signature.bind(*((None,) * (argument_count + 2)))
    except TypeError as error:
        raise ValueError(
            "Custom function '{}' does not accept the arguments of its call site: it is "
            "called with the model, the time and {} argument(s), which gives {} in total, "
            "and binding them failed with: {}".format(
                name, argument_count, argument_count + 2, error))


def _py_callback_to_json(expr):
    """
    A custom function as a node the engine answers by calling back into Python.

    Only the name is serialized, never the callable: the engine resolves it to a slot at
    load time and the caller registers what to run. Everything this function raises is a
    ValueError, because that is what the runner turns into a RustBackendError naming
    the cause.
    """
    if not expr.elementwise:
        raise ValueError(
            "Custom function '{}' takes whole arrays (elementwise=False), which has no "
            "node in the engine format: a callback answers with one number, and an "
            "array-taking function is handed a sequence and answers once.".format(
                expr.name))

    if _current_model is None:
        raise ValueError(
            "Custom function '{}' cannot be serialized outside model_to_json(), which is "
            "what makes the model's callables reachable.".format(expr.name))

    fn = _current_model.fn.get(expr.name)
    if fn is None:
        raise ValueError(
            "Custom function '{}' has no callable registered on the model.".format(
                expr.name))

    if _current_model.agent_factories or _current_model.agents:
        # A hybrid model advances its two halves in lockstep: the agents compute step t
        # and write what the SD side reads at step t. The engine runs every step at once,
        # so at step 50 the agents have not moved and there is nothing to read. The
        # criterion is the model's shape, never what the function's body does - a look
        # inside the callable would be a guess.
        raise ValueError(
            "Custom function '{}' belongs to a model that also has agents. A hybrid "
            "model advances its agents and its System Dynamics side one step at a time, "
            "and the engine computes every step at once, so a function that reads what "
            "the agents produced would read a step that has not happened. Hybrid models "
            "run on the Python engine.".format(expr.name))

    _check_call_site_arity(fn, expr.name, len(expr.args))

    return {
        "type": "py_callback",
        "name": expr.name,
        "args": [_expr_to_json(arg) for arg in expr.args],
    }


# ── Expression serializer ────────────────────────────────────────────────────

# The operators that render the same way, as tables. Each is checked with isinstance, in
# order; no class in them derives from another, so the order changes nothing today. An
# operator that is in none of them is rendered by code of its own in `_expr_to_json`;
# tests/unittests/test_json_serializer.py fails for one that is in neither.

# (operator, builtin, whether a scalar operand passes through) - the others answer 0.0
# for an operand without sub-elements, as the Python operators do.
_AGGREGATIONS = (
    (ops.ArraySumOperator, "arr_sum", True),
    (ops.ArrayProductOperator, "arr_prod", True),
    (ops.ArrayMeanOperator, "arr_mean", False),
    (ops.ArrayMedianOperator, "arr_median", False),
    (ops.ArrayStandardDeviationOperator, "arr_stddev", False),
    (ops.ArrayMaxOperator, "arr_max", False),
    (ops.ArrayMinOperator, "arr_min", False),
)

# (operator, op, attribute of the left operand, attribute of the right one)
_BINARY_OPERATORS = (
    (ops.AdditionOperator, "add", "element_1", "element_2"),
    (ops.SubtractionOperator, "sub", "element_1", "element_2"),
    (ops.NumericalMultiplicationOperator, "mul", "element_1", "element_2"),
    (ops.MultiplicationOperator, "mul", "element_1", "element_2"),
    (ops.DivisionOperator, "div", "element_1", "element_2"),
    (ops.PowerOperator, "pow", "element", "power"),
    (ops.ModOperator, "mod", "element_1", "element_2"),
    (ops.And, "and", "lhs", "rhs"),
    (ops.Or, "or", "lhs", "rhs"),
)

# (operator, builtin, attributes holding its arguments, in the engine's order)
_CALLS = (
    (ops.Time, "time", ()),
    (ops.DT, "dt", ()),
    (ops.Starttime, "starttime", ()),
    (ops.Stoptime, "stoptime", ()),
    (ops.AbsOperator, "abs", ("element",)),
    (ops.Sqrt, "sqrt", ("x",)),
    (ops.Exp, "exp", ("element",)),
    (ops.Sin, "sin", ("x",)),
    (ops.Cos, "cos", ("x",)),
    (ops.Tan, "tan", ("x",)),
    (ops.Arcsin, "arcsin", ("x",)),
    (ops.Arccos, "arccos", ("x",)),
    (ops.Arctan, "arctan", ("x",)),
    (ops.Pi, "pi", ()),
    (ops.Ln, "ln", ("x",)),
    (ops.Log10, "log10", ("x",)),
    (ops.Floor, "floor", ("x",)),
    (ops.Ceil, "ceil", ("x",)),
    (ops.Round, "round", ("operator", "digits")),
    (ops.MaxOperator, "max", ("element_1", "element_2")),
    (ops.MinOperator, "min", ("element_1", "element_2")),
    (ops.Sinwave, "sinwave", ("amplitude", "period")),
    (ops.Coswave, "coswave", ("amplitude", "period")),
    (ops.Step, "step", ("height", "timestep")),
    (ops.Pulse, "pulse", ("volume", "first_pulse", "interval")),
    (ops.Combinations, "combinations", ("n", "r")),
    (ops.Permutations, "permutations", ("n", "r")),
    (ops.Factorial, "factorial", ("n",)),
    (ops.GammaLN, "gammaln", ("n",)),
    (ops.Inf, "inf", ()),
    (ops.Nan, "nan", ()),
    (ops.Random, "random", ("min_value", "max_value")),
    (ops.Normal, "normal", ("mean", "stddev")),
    (ops.Beta, "beta", ("a", "b")),
    (ops.Binomial, "binomial", ("n", "p")),
    (ops.NegBinomial, "negbinomial", ("n", "p")),
    (ops.Exprnd, "exprnd", ("l",)),
    (ops.Gamma, "gamma_dist", ("shape", "scale")),
    (ops.Geometric, "geometric", ("p",)),
    (ops.Lognormal, "lognormal", ("mean", "stddev")),
    (ops.Logistic, "logistic", ("mean", "scale")),
    (ops.Montecarlo, "montecarlo", ("p",)),
    (ops.Poisson, "poisson", ("mu",)),
    (ops.Triangular, "triangular", ("lower_bound", "mode", "upper_bound")),
    (ops.Weibull, "weibull", ("shape", "scale")),
    (ops.Pareto, "pareto", ("shape", "scale")),
    (ops.NormalCDF, "normalcdf", ("left", "right", "mean", "stddev")),
)

def _expr_to_json(expr):
    """
    Recursively convert an SD DSL expression tree to a JSON-compatible dict.

    Handles: literals, element references, the array aggregations, `dot`, all
    operators and built-in functions that the Rust engine supports, and a custom
    function, which becomes a node the engine answers by calling back into Python.
    Raises ValueError for nodes the engine cannot express - a function that takes whole
    arrays, or a reference to the parent of an arrayed element - which the runner reports
    as a RustBackendError.
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
            # is a guard: raising makes the runner refuse the model instead of loading it
            # with an unresolvable reference.
            raise ValueError(
                f"Cannot serialize a reference to the arrayed element '{expr.name}'. "
                f"Only its sub-elements are entities in the JSON model."
            )
        return {"type": "ref", "name": expr.name}

    # ── Array aggregations: array in, one number out ─────────────────────
    for operator, function, pass_through in _AGGREGATIONS:
        if isinstance(expr, operator):
            if pass_through:
                ops._check_aggregation_dimensions(function, expr.element, expr.dimensions)
            return _aggregation_to_json(function, expr.element,
                                        scalar_input="pass_through" if pass_through else "zero")

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

    # ── x * -1.0 is a negation ───────────────────────────────────────────
    if isinstance(expr, ops.NumericalMultiplicationOperator):
        for factor, other in ((expr.element_2, expr.element_1), (expr.element_1, expr.element_2)):
            if (isinstance(factor, ops.UnaryOperator) and isinstance(factor.element, (int, float))
                    and factor.element == -1.0):
                return {"type": "unary_op", "op": "neg", "operand": _expr_to_json(other)}

    # ── Binary operators ─────────────────────────────────────────────────
    for operator, op, left, right in _BINARY_OPERATORS:
        if isinstance(expr, operator):
            return {"type": "binary_op", "op": op,
                    "left": _expr_to_json(getattr(expr, left)),
                    "right": _expr_to_json(getattr(expr, right))}

    if isinstance(expr, ops.ComparisonOperator):
        op = _COMPARISON_SIGN_MAP.get(expr.sign)
        if op is None:
            raise ValueError(f"Unknown comparison sign: {expr.sign}")
        return {"type": "binary_op", "op": op,
                "left": _expr_to_json(expr.element_1),
                "right": _expr_to_json(expr.element_2)}

    # ── Conditional / logical ────────────────────────────────────────────
    if isinstance(expr, ops.If):
        return {"type": "if",
                "condition": _expr_to_json(expr.if_),
                "then": _expr_to_json(expr.then_),
                "else": _expr_to_json(expr.else_) if expr.else_ is not None
                else {"type": "literal", "value": 0.0}}

    if isinstance(expr, ops.Not):
        return {"type": "unary_op", "op": "not",
                "operand": _expr_to_json(expr.condition)}

    # ── Builtins whose arguments are attributes of the operator ──────────
    for operator, function, arguments in _CALLS:
        if isinstance(expr, operator):
            return {"type": "call", "function": function,
                    "args": [_expr_to_json(getattr(expr, argument)) for argument in arguments]}

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

    if isinstance(expr, ops.Invnorm):
        # Always all three: with a positional list, a stddev given without a mean would
        # arrive where the engine reads the mean.
        mean = 0.0 if expr.mean is None else expr.mean
        stddev = 1.0 if expr.stddev is None else expr.stddev
        return {"type": "call", "function": "invnorm",
                "args": [_expr_to_json(expr.p), _expr_to_json(mean), _expr_to_json(stddev)]}

    # ── Custom functions: a call back into Python, by name ─────────────────
    if isinstance(expr, ops.NaryOperator):
        return _py_callback_to_json(expr)

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

    A custom function becomes a `py_callback` node carrying its name; the callable
    itself is never serialized.

    Returns a JSON string. Raises ValueError if the model uses features the Rust engine
    cannot express, such as a custom function that takes whole arrays.
    """
    with _serialization_lock:
        _reset_inline_tables()
        _set_current_model(model)
        try:
            return _model_to_json(model)
        finally:
            _set_current_model(None)


def _model_to_json(model) -> str:
    """The body of `model_to_json`, run with the serialization context in place."""
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
