"""The SMILE parser against every equation it has been seen to parse.

`tests/test_models/smile_corpus.json` records, for each equation a model of this repository
hands the parser, what the parser makes of it: the tree, or the error it raises. A change to
the parser shows up here as a changed entry - read it entry by entry, then record the corpus
again:

    uv run python -m tests.test_smile_corpus

The equations are taken where the parser receives them, so the corpus holds the text after
the compiler's own preparation and the equations array expansion writes, not only what the
model files spell. A model the compiler gives up on stops at the equation it fails on;
every `<eqn>` of every model is therefore taken from the file as well. Only models of this
repository: the corpus is synced to the public repository, and every source it names has to
be there.
"""

import json
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests" / "test_models" / "smile_corpus.json"
# The equations of the models the `py` target was tested with, which went with it in 3.5.0,
# and of the step models of Make Your PSF Grow's XMILE series, removed with the series in
# 3.5.0, stay in the corpus: no other model writes them. Their source reads "retired: <model>", and
# recording the corpus again carries them over from the file as it is.
RETIRED = "retired: "

# Equations for each construct of the language and for each edge the parser has been seen to
# stumble on, so that the corpus holds more than what the models happen to write. The key
# names the construct; the source of the entry in the corpus is the key.
GRAMMAR_CASES = {
    "Sentence: nothing": "",
    "Sentence: whitespace around": "  x  ",
    "Comment": "{a comment}",
    "Comment: after an expression": "x {note}",
    "ConditionalExpression: with ELSE": "IF a THEN b ELSE c",
    "ConditionalExpression: without ELSE": "IF a THEN b",
    "ConditionalExpression: nested": "IF a THEN IF b THEN 1 ELSE 2 ELSE 3",
    "ConditionalExpression: brackets as separators": "IF(a>1)THEN(b)ELSE(c)",
    "ConditionalStatement: AND": "a > 1 AND b < 2",
    "ConditionalStatement: OR then AND": "a > 1 OR b < 2 AND c = 3",
    "ConditionalStatement: lower case": "a > 1 and b < 2 or c = 3",
    "BooleanTerm: NOT": "NOT a > 1",
    "BooleanTerm: NOT bracketed": "NOT (a > 1)",
    "BooleanTerm: NOT NOT": "NOT NOT a > 1",
    "BooleanTerm: NOT NOT without a comparison": "NOT NOT a",
    "BooleanTerm: bracketed statements": "(a > 1) AND (b > 2)",
    "Not: a name that starts with NOT": "NOTE + 1",
    "ComparisonOperator: >=": "a >= 1",
    "ComparisonOperator: =": "a = 1",
    "ComparisonOperator: <=": "a <= 1",
    "ComparisonOperator: <>": "a <> 1",
    "ComparisonOperator: <": "a < 1",
    "ComparisonOperator: >": "a > 1",
    "ComparisonExpression: expressions on both sides": "a + 1 > b * 2",
    "Expression: +": "a + b",
    "Expression: - then +": "a - b + c",
    "Expression: - then -": "a - b - c",
    "Expression: unary minus on a name": "-a + b",
    "Term: *": "a * b",
    "Term: / then /": "a / b / c",
    "Term: ^ then ^": "a ^ b ^ c",
    "Term: ^ then *": "a ^ b * c",
    "Term: * then ^": "a * b ^ c",
    "Term: MOD": "a MOD b",
    "Term: mod then *": "a mod b * c",
    "Term: minus to a power": "-2 ^ 2",
    "Term: minus after *": "a * -b",
    "Term: minus after ^": "a ^ -b",
    "Term: minus after / with a power": "a / -b ^ 2",
    "Atom: bracketed sentence": "(a + b) * c",
    "Atom: brackets around a condition": "(a > b) * 2",
    "NumericLiteral: significant fraction exponent": "1.5e2",
    "NumericLiteral: significant fraction": "1.5",
    "NumericLiteral: minus fraction exponent": "-.5e2",
    "NumericLiteral: minus fraction": "-.5",
    "NumericLiteral: fraction": ".5",
    "NumericLiteral: significant exponent": "2e3",
    "NumericLiteral: negative exponent": "2e-3",
    "NumericLiteral: capital E": "2E3",
    "NumericLiteral: significant": "7",
    "NumericLiteral: minus and space": "- 7",
    "FunctionExpression: two arguments": "SMTH1(x, 2)",
    "FunctionExpression: one argument": "ABS(a)",
    "FunctionExpression: no argument": "f()",
    "FunctionExpression: expressions as arguments": "MAX(a + b, c * d)",
    "FunctionExpression: nested": "MAX(MIN(a, b), ABS(c))",
    "FunctionArgument: array then operator": "MAX(arr[1] + 2, 3)",
    "FunctionArgument: array alone": "SUM(arr[*])",
    "FunctionArgument: condition": "IF_THEN(a > 1, 2)",
    "SpecialFunction: STARTTIME": "STARTTIME",
    "SpecialFunction: STOPTIME": "STOPTIME",
    "SpecialFunction: TIME": "TIME",
    "SpecialFunction: DT": "DT",
    "SpecialFunction: PI": "PI",
    "SpecialFunction: CLOCKTIME": "CLOCKTIME",
    "SpecialFunction: NAN": "NAN",
    "SpecialFunction: INF": "INF",
    "SpecialFunction: lower case": "time * dt",
    "SpecialFunction: a name that starts with one": "time2 + dtx",
    "Identifier: enclosed with spaces and brackets": '"rate (per month)" * 2',
    "Identifier: enclosed with an escaped quote": '"a \\"b\\"" + 1',
    "Identifier: namespaced": "module.rate + 1",
    "Identifier: namespaced without a module": ".rate + 1",
    "Identifier: underscores and digits": "x_1 + y_2",
    "Identifier: currency and percent": "cost€ + share% + price$",
    "Identifier: apostrophe": "a'b + 1",
    "Identifier: umlauts": "Größe * 2",
    "ArrayExpression: one index": "arr[1]",
    "ArrayExpression: two indices": "arr[1, 2]",
    "ArrayExpression: asterisk": "arr[*]",
    "ArrayExpression: range": "arr[a:b]",
    "ArrayExpression: label and asterisk": "arr[dim1, *]",
    "ArrayExpression: function as index": "arr[f(1)]",
    "ArrayExpression: name as index": "arr[d] * 2",
    "Keyword: names that start with keywords": "iffy + thenx + elsewhere + andy + oregon",
    "whitespace: tabs and line breaks": "a\n+\tb",
    "whitespace: non-breaking space": "a\u00a0+ b",
    "BooleanTerm: NOT before arithmetic": "NOT a + b > c",
    "ConditionalStatement: arithmetic after AND": "a = b AND c + d > e",
    "FunctionArgument: an array and two operators": "MAX(arr[1] - c - d, b)",
    "edge: two operators": "a + * b",
    "edge: unclosed bracket": "(a + b",
    "edge: a comma outside a call": "5, 10, 15",
}


def parse(equation):
    """The tree the parser builds for `equation`, or the name of the error it raises."""
    from BPTK_Py.sdcompiler.parsers.smile.parser import SmileSyntaxError, parse as parse_smile
    try:
        return {"ir": parse_smile(equation)}
    except SmileSyntaxError as error:
        return {"error": type(error).__name__}


def _equations_of(model, seen):
    """Compile `model` and collect every equation the parser receives on the way."""
    import importlib
    from BPTK_Py.sdcompiler import compile_xmile

    # The XMILE reader holds the parser under its own name, the array expansion imports it
    # when it runs - both are replaced while the model compiles
    modules = [importlib.import_module("BPTK_Py.sdcompiler.parsers.smile.parser"),
               importlib.import_module("BPTK_Py.sdcompiler.parsers.xmile.xmile")]
    original = modules[0].parse

    def recording(text):
        seen.setdefault(text, str(model))
        return original(text)

    for module in modules:
        module.parse = recording
    try:
        with tempfile.TemporaryDirectory() as directory:
            compile_xmile(str(model), str(Path(directory) / "model.py"), "py-sddsl")
        return None
    except Exception as error:  # a model the compiler refuses still gave its equations
        return type(error).__name__
    finally:
        for module in modules:
            module.parse = original


def _written_equations(model, seen):
    """Every equation as the model's file spells it."""
    import xml.etree.ElementTree as ElementTree
    try:
        tree = ElementTree.parse(model)
    except ElementTree.ParseError:
        return
    for element in tree.iter():
        if element.tag.rsplit("}", 1)[-1] == "eqn" and element.text and element.text.strip():
            seen.setdefault(element.text.strip(), str(model))


def record():
    seen = {}
    refused = {}
    # Stella writes .stmx, iThink - and Stella for an external module - .itmx; both are XMILE
    models = sorted(path.resolve() for directory in (ROOT / "tests" / "test_models", ROOT / "website-tutorial")
                    for pattern in ("*.stmx", "*.itmx")
                    for path in directory.rglob(pattern) if "_output" not in path.parts)
    for model in models:
        error = _equations_of(model, seen)
        if error is not None:
            refused[str(model)] = error
        _written_equations(model, seen)
    corpus = {equation: dict(parse(equation), source=_relative(source)) for equation, source in sorted(seen.items())}
    for case, equation in GRAMMAR_CASES.items():
        corpus.setdefault(equation, dict(parse(equation), source="grammar: " + case))
    previous = json.loads(CORPUS.read_text(encoding="utf-8")) if CORPUS.exists() else {}
    for equation, entry in previous.items():
        if entry["source"].startswith(RETIRED):
            corpus.setdefault(equation, dict(parse(equation), source=entry["source"]))
    return dict(sorted(corpus.items())), refused, len(models)


def _relative(path):
    return str(Path(path).relative_to(ROOT))


if __name__ == "__main__":
    corpus, refused, count = record()
    CORPUS.write_text(json.dumps(corpus, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    failed = sum("error" in entry for entry in corpus.values())
    print("{} models, {} equations, {} the parser refuses; {} models the compiler refuses".format(
        count, len(corpus), failed, len(refused)))


ENTRIES = json.loads(CORPUS.read_text(encoding="utf-8"))


@pytest.mark.parametrize("equation", sorted(ENTRIES), ids=lambda equation: equation[:60])
def test_the_parser_reads_every_equation_of_the_corpus_as_recorded(equation):
    expected = {key: value for key, value in ENTRIES[equation].items() if key != "source"}
    assert parse(equation) == expected, ENTRIES[equation]["source"]


def test_the_corpus_holds_the_equations_the_models_hand_the_parser():
    """A corpus recorded from too few models would hold too little to change a parser by -
    and every source it names is a model of this repository, which is public."""
    assert len(ENTRIES) > 600
    assert all("ir" in entry or "error" in entry for entry in ENTRIES.values())
    assert all(entry["source"].startswith(("grammar: ", RETIRED)) or (ROOT / entry["source"]).is_file()
               for entry in ENTRIES.values())


def test_every_case_of_the_grammar_is_in_the_corpus():
    assert set(GRAMMAR_CASES.values()) <= set(ENTRIES)


def test_the_retired_equations_stay_in_the_corpus():
    """144 equations came only from the models of `py`'s tests and 19 from the step models of
    Make Your PSF Grow; recording again drops none."""
    assert sum(entry["source"].startswith(RETIRED) for entry in ENTRIES.values()) == 163


def test_the_parser_refuses_only_what_is_wrong():
    refused = {equation for equation, entry in ENTRIES.items() if "error" in entry}
    assert refused == {"(a + b", "5, 10, 15"}
