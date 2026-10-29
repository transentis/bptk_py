#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2019-2026 transentis labs GmbH
# MIT License

"""The SMILE equation parser: a tokenizer and a Pratt parser.

`parse` turns the text of an equation into the tree the rest of the compiler reads:

- a number is a float, an empty operand is `""`
- an operator is `{"name", "type": "operator", "args"}`; a unary minus has `""` as its left
  operand, NOT has one operand, brackets are an operator `()` of their own
- a name is `{"name", "type": "identifier"}`, TIME, DT and the other special names are calls
  without arguments
- a call is `{"name", "type": "call", "args"}`, IF ... THEN ... ELSE a call `if`
- an array is `{"name", "type": "array", "args"}`, its indices labels, ranges, `"*"` or
  expressions

Precedence follows the XMILE standard, from loose to tight: OR, AND, the comparisons, `+ -`,
`* / MOD`, the unary `-` and NOT, and `^`, the only operator that associates to the right -
`-2 ^ 2` is -4, `NOT a > 1` is `(NOT a) > 1`.
"""

import re

try:
    from ...plugins import sanitizeName
except:  # Standalone Mode
    from plugins import sanitizeName


class SmileSyntaxError(ValueError):
    """An equation the parser cannot read; the message names the position."""


_WHITESPACE = "\t\v\f\r\n \u00a0\u2028\ufeff"
_NAME_CHARS = r"[\w%$€£¥&§#']"

_TOKEN = re.compile(r"""
    (?P<space>[%s]+|\{[^}]*\})
  | (?P<number>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?(?!%s))
  | (?P<quoted>"(?:[^"\\]|\\.)*")
  | (?P<name>\.?%s+(?:\.%s+)*)
  | (?P<operator><>|<=|>=|[-+*/^=<>()\[\],:])
""" % (_WHITESPACE, _NAME_CHARS, _NAME_CHARS, _NAME_CHARS), re.VERBOSE)

_KEYWORDS = {"if", "then", "else", "and", "or", "not", "mod"}
_SPECIAL_NAMES = {"starttime", "stoptime", "time", "dt", "pi", "clocktime", "nan", "inf"}

_COMPARISONS = {"=", "<>", "<", ">", "<=", ">="}

# Binding power of each infix operator: higher binds tighter
_POWER = {"or": 1, "and": 2, "+": 10, "-": 10, "*": 20, "/": 20, "mod": 20, "^": 30}
_POWER.update({comparison: 5 for comparison in _COMPARISONS})
_UNARY = 25
_RIGHT_ASSOCIATIVE = {"^"}

# The names the compiler reads; the comparisons and the symbols stand for themselves
_NAME = {"and": "AND", "or": "OR", "mod": "MOD"}


class _Token:
    __slots__ = ("kind", "text", "position")

    def __init__(self, kind, text, position):
        self.kind, self.text, self.position = kind, text, position

    @property
    def key(self):
        """What the parser dispatches on: the keyword or symbol, or the kind of token."""
        if self.kind == "name" and self.text.lower() in _KEYWORDS:
            return self.text.lower()
        return self.text if self.kind == "operator" else self.kind


def _tokenize(equation):
    tokens, position = [], 0
    while position < len(equation):
        match = _TOKEN.match(equation, position)
        if not match:
            raise SmileSyntaxError("unexpected {!r} at position {} of {!r}".format(
                equation[position], position, equation))
        if match.lastgroup != "space":
            tokens.append(_Token(match.lastgroup, match.group(), position))
        position = match.end()
    tokens.append(_Token("end", "", position))
    return tokens


def _name(text):
    return sanitizeName(text.lower())


class _Parser:

    def __init__(self, equation):
        self.equation = equation
        self.tokens = _tokenize(equation)
        self.index = 0

    @property
    def next(self):
        return self.tokens[self.index]

    def advance(self):
        token = self.tokens[self.index]
        self.index += 1
        return token

    def expect(self, key):
        if self.next.key != key:
            self.fail("expected {!r}".format(key))
        return self.advance()

    def fail(self, reason):
        token = self.next
        found = repr(token.text) if token.kind != "end" else "the end"
        raise SmileSyntaxError("{}, found {} at position {} of {!r}".format(
            reason, found, token.position, self.equation))

    def equation_tree(self):
        if self.next.kind == "end":
            # Nothing but a comment, or nothing at all
            return "0.0" if "{" in self.equation else ""
        tree = self.expression(0)
        if self.next.kind != "end":
            self.fail("expected the end of the equation")
        return tree

    def expression(self, binding):
        left = self.operand()
        while _POWER.get(self.next.key, 0) > binding:
            key = self.advance().key
            power = _POWER[key] - 1 if key in _RIGHT_ASSOCIATIVE else _POWER[key]
            left = {"name": _NAME.get(key, key), "type": "operator", "args": [left, self.expression(power)]}
        return left

    def operand(self):
        token = self.next
        key = token.key
        if key == "number":
            self.advance()
            return float(token.text)
        if key in ("name", "quoted"):
            return self.reference()
        if key == "(":
            self.advance()
            inner = self.expression(0)
            self.expect(")")
            return {"name": "()", "type": "operator", "args": [inner]}
        if key == "-":
            self.advance()
            operand = self.expression(_UNARY)
            if isinstance(operand, float):
                return -operand
            return {"name": "-", "type": "operator", "args": ["", operand]}
        if key == "not":
            self.advance()
            return {"name": "not", "type": "operator", "args": [self.expression(_UNARY)]}
        if key == "if":
            return self.conditional()
        # An operand left out, as in `a + * b`: the empty operand the compiler has always read
        return ""

    def conditional(self):
        self.expect("if")
        condition = self.expression(0)
        self.expect("then")
        args = [condition, self.expression(0)]
        if self.next.key == "else":
            self.advance()
            args.append(self.expression(0))
        return {"name": "if", "type": "call", "args": args}

    def reference(self):
        token = self.advance()
        # A quoted name is the name the model gives the variable, escaped quotes and all
        name = _name(token.text[1:-1].replace('\\"', '"') if token.kind == "quoted" else token.text)
        if self.next.key == "(" and token.kind == "name":
            return {"name": _name(name), "type": "call", "args": self.arguments()}
        if self.next.key == "[":
            return {"name": name, "type": "array", "args": self.indices()}
        if token.kind == "name" and token.text.lower() in _SPECIAL_NAMES:
            return {"name": token.text.lower(), "type": "call", "args": []}
        return {"name": name, "type": "identifier"}

    def arguments(self):
        self.expect("(")
        args = [self.expression(0)]
        while self.next.key == ",":
            self.advance()
            args.append(self.expression(0))
        self.expect(")")
        # A single number stands for itself rather than in a list - the compiler reads it so
        if len(args) == 1 and isinstance(args[0], float):
            return str(args[0])
        return args

    def indices(self):
        self.expect("[")
        indices = [self.index_()]
        while self.next.key == ",":
            self.advance()
            indices.append(self.index_())
        self.expect("]")
        return "*" if indices == ["*"] else indices

    def index_(self):
        """One index of an array: `*`, a label, a range of labels, or an expression -
        `base[D - 1]` computes with the dimension's position."""
        if self.next.key == "*" and self.tokens[self.index + 1].key in (",", "]"):
            self.advance()
            return "*"
        label = self.label()
        if label is None:
            return self.expression(0)
        if self.next.key == ":":
            self.advance()
            end = self.label()
            if end is None:
                self.fail("expected a label after ':'")
            return {"name": ":", "type": "range", "args": [label, end]}
        return label

    def label(self):
        """A name or a number standing alone in an index is a label of the dimension."""
        token, following = self.next, self.tokens[self.index + 1]
        plain = token.kind == "number" or (token.kind == "name" and "." not in token.text.lstrip(".")
                                           and token.key == "name")
        if plain and following.key in (",", "]", ":"):
            self.advance()
            return {"name": _name(token.text), "type": "label"}
        return None


def parse(equation):
    """The tree of one SMILE equation; raises `SmileSyntaxError` if it cannot be read."""
    return _Parser(equation).equation_tree()
