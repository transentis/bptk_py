"""Building blocks of the engine's JSON model format, for tests that write it by hand."""


def lit(value):
    """A literal expression node."""
    return {"type": "literal", "value": value}


def ref(name):
    """A reference expression node."""
    return {"type": "ref", "name": name}


def binop(op, left, right):
    """A binary-op expression node."""
    return {"type": "binary_op", "op": op, "left": left, "right": right}


def add(left, right):
    return binop("add", left, right)


def mul(left, right):
    return binop("mul", left, right)


def unop(op, operand):
    """A unary-op expression node."""
    return {"type": "unary_op", "op": op, "operand": operand}


def call(function, args):
    """A builtin call node."""
    return {"type": "call", "function": function, "args": args}


def if_expr(condition, then, else_):
    """An if node."""
    return {"type": "if", "condition": condition, "then": then, "else": else_}
