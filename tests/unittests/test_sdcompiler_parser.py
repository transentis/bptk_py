import os
import tempfile
import unittest

from BPTK_Py.sdcompiler.compile import compile_xmile


def _compile_model(sim_specs, variables):
    """Compile a minimal XMILE document (custom sim_specs + variables) to SD DSL code."""
    xml = (
        '<?xml version="1.0"?><xmile version="1.0"'
        ' xmlns="http://docs.oasis-open.org/xmile/ns/XMILE/v1.0"'
        ' xmlns:isee="http://iseesystems.com/XMILE">'
        '<header><smile version="1.0" namespace="std, isee"/><name>m</name>'
        '<uuid>x</uuid><vendor>v</vendor><product version="1.0" lang="en">p</product></header>'
        '{}<model><variables>{}</variables></model></xmile>'.format(sim_specs, variables)
    )
    tmpdir = tempfile.mkdtemp()
    src = os.path.join(tmpdir, "m.stmx")
    dest = os.path.join(tmpdir, "m.py")
    with open(src, "w", encoding="utf-8") as f:
        f.write(xml)
    compile_xmile(src, dest, "py-sddsl")
    with open(dest, "r", encoding="utf-8") as f:
        return f.read()


def _shape(node):
    """A tree as brackets, for reading: `(a - b)`, `(neg a)`, `(not a)`, `f[a, b]`."""
    if isinstance(node, dict):
        if node.get("type") == "operator":
            args = node["args"]
            if len(args) == 1:
                return "({} {})".format(node["name"], _shape(args[0]))
            if args[0] == "" and node["name"] == "-":
                return "(neg {})".format(_shape(args[1]))
            return "({} {} {})".format(_shape(args[0]), node["name"], _shape(args[1]))
        if "args" in node:
            args = node["args"] if isinstance(node["args"], list) else [node["args"]]
            return "{}[{}]".format(node["name"], ", ".join(_shape(arg) for arg in args))
        return node["name"]
    return repr(node)


class TestSmileParser(unittest.TestCase):
    """The Pratt parser: precedence as the XMILE standard gives it, the node shapes the
    compiler reads, and what Stella writes that the grammar of old refused."""

    def _check(self, cases):
        from BPTK_Py.sdcompiler.parsers.smile.parser import parse
        for equation, shape in cases:
            with self.subTest(equation=equation):
                self.assertEqual(_shape(parse(equation)), shape)

    def test_precedence_and_associativity(self):
        self._check([
            ("a - b - c", "((a - b) - c)"),
            ("a / b * c", "((a / b) * c)"),
            ("a ^ b ^ c", "(a ^ (b ^ c))"),
            ("a ^ b * c", "((a ^ b) * c)"),
            ("a MOD b * c", "((a MOD b) * c)"),
            ("a + b * c > d", "((a + (b * c)) > d)"),
            ("a > 1 OR b > 2 AND c > 3", "((a > 1.0) OR ((b > 2.0) AND (c > 3.0)))"),
            ("a and b or c", "((a AND b) OR c)"),
            ("(a + b) * c", "((() (a + b)) * c)"),
        ])

    def test_unary_minus_binds_below_the_power_and_above_the_product(self):
        self._check([
            ("-a * b", "((neg a) * b)"),
            ("-a ^ 2", "(neg (a ^ 2.0))"),
            ("-2 ^ 2", "(neg (2.0 ^ 2.0))"),
            ("- 7", "-7.0"),
            ("a * -b", "(a * (neg b))"),
            ("2 ^ -1", "(2.0 ^ -1.0)"),
            ("--a", "(neg (neg a))"),
        ])

    def test_not_is_a_unary_operator_above_the_comparisons(self):
        self._check([
            ("NOT a > 1", "((not a) > 1.0)"),
            ("NOT NOT a", "(not (not a))"),
            ("NOT (a > 1)", "(not (() (a > 1.0)))"),
            ("NOT 0", "(not 0.0)"),
            ("NOT a + b > c", "(((not a) + b) > c)"),
        ])

    def test_numbers(self):
        self._check([("1.5e2", "150.0"), ("2E-3", "0.002"), ("2e+3", "2000.0"),
                     (".5", "0.5"), ("-.5", "-0.5"), ("7.", "7.0")])

    def test_names(self):
        self._check([
            ("Größe", "größe"),
            ("x_1", "x1"),
            ("module.rate", "module.rate"),
            (".rate", "rate"),
            ('"rate (per month)"', "rate(perMonth)"),
            ('"rate_(per_month)"', "rate(perMonth)"),
            ('"a \\"b\\""', "aB"),
            ("NOTE + iffy", "(note + iffy)"),
            ("time * DT", "(time[] * dt[])"),
            ("time2", "time2"),
        ])

    def test_calls_and_conditions(self):
        self._check([
            ("MAX(a, b + 1)", "max[a, (b + 1.0)]"),
            ("IF_THEN(a, b)", "ifthen[a, b]"),
            ("TIME()", "time['']"),
            ("f()", "f['']"),
            ("IF a THEN b ELSE c + 1", "if[a, b, (c + 1.0)]"),
            ("IF(a>1)THEN(b)", "if[(() (a > 1.0)), (() b)]"),
            ("1 + IF a THEN b ELSE c", "(1.0 + if[a, b, c])"),
        ])

    def test_a_single_number_as_the_argument_is_a_string(self):
        from BPTK_Py.sdcompiler.parsers.smile.parser import parse
        self.assertEqual(parse("ABS(-1)")["args"], "-1.0")
        self.assertEqual(parse("ABS(1, 2)")["args"], [1.0, 2.0])

    def test_arrays(self):
        self._check([
            ("arr[1]", "arr[1]"),
            ("arr[*]", "arr['*']"),
            ("arr[dim, *]", "arr[dim, '*']"),
            ("arr[a:b]", "arr[:[a, b]]"),
            ("arr[TIME]", "arr[time]"),
            ("arr[f(1)]", "arr[f['1.0']]"),
            ("arr[m.x]", "arr[m.x]"),
            ("base[D - 1]", "base[(d - 1.0)]"),
            ("arr[*] * 2", "(arr['*'] * 2.0)"),
            ("SUM(a[1] + b)", "sum[(a[1] + b)]"),
            ("MEAN(a[1,2] * b)", "mean[(a[1, 2] * b)]"),
        ])
        from BPTK_Py.sdcompiler.parsers.smile.parser import parse
        self.assertEqual(parse("arr[*]")["args"], "*")
        self.assertEqual(parse("arr[m.x]")["args"], [{"name": "m.x", "type": "identifier"}])
        self.assertEqual(parse("arr[1]")["args"], [{"name": "1", "type": "label"}])

    def test_empty_operands_comments_and_whitespace(self):
        self._check([
            ("", "''"),
            ("   ", "''"),
            ("{a comment}", "'0.0'"),
            ("x {sum of the three}", "x"),
            ("a + * b", "(a + ('' * b))"),
            ("a\n+\u00a0b\u2028", "(a + b)"),
        ])

    def test_what_cannot_be_read_names_the_position(self):
        from BPTK_Py.sdcompiler.parsers.smile.parser import SmileSyntaxError, parse
        for equation, message in [
            ("(a + b", "expected ')', found the end at position 6"),
            ("5, 10, 15", "expected the end of the equation, found ',' at position 1"),
            ("a ? b", "unexpected '?' at position 2"),
            ("IF a b", "expected 'then', found 'b' at position 5"),
            ("arr[a:*]", "expected a label after ':', found '*' at position 6"),
        ]:
            with self.subTest(equation=equation):
                with self.assertRaises(SmileSyntaxError) as raised:
                    parse(equation)
                self.assertIn(message, str(raised.exception))


class TestXmileParser(unittest.TestCase):
    def test_reciprocal_dt_nonnegative_stock_and_graphical_xpts(self):
        """A reciprocal dt, a non-negative stock (max(0, equation)) and a graphical
        function with explicit xpts all parse."""
        code = _compile_model(
            '<sim_specs method="Euler" time_units="Months"><start>1</start><stop>10</stop>'
            '<dt reciprocal="true">4</dt></sim_specs>',
            '<stock name="s"><eqn>rate</eqn><inflow>rate</inflow><non_negative/></stock>'
            '<flow name="rate"><eqn>1</eqn></flow>'
            '<aux name="lk"><gf><xpts>0,1,2</xpts><ypts>0,10,20</ypts></gf><eqn>rate</eqn></aux>',
        )
        self.assertIn("dt=0.25", code)
        self.assertIn("[[0.0, 0.0], [1.0, 10.0], [2.0, 20.0]]", code)

    def test_dt_with_text_node(self):
        """A dt given as an element with attributes (dict with #text, non-reciprocal)."""
        code = _compile_model(
            '<sim_specs method="Euler" time_units="Months"><start>1</start><stop>5</stop>'
            '<dt units="months">2</dt></sim_specs>',
            '<aux name="a"><eqn>1</eqn></aux>',
        )
        self.assertIn("dt=2.0", code)

    def test_connects_single_and_multiple(self):
        """Element <connect> data is extracted for both a single connect (dict) and
        multiple connects (list)."""
        specs = ('<sim_specs method="Euler" time_units="Months"><start>1</start>'
                 '<stop>5</stop><dt>1</dt></sim_specs>')
        single = _compile_model(specs,
            '<aux name="a"><eqn>1</eqn></aux>'
            '<aux name="b"><eqn>a</eqn><connect to="b" from="a"/></aux>')
        self.assertIn("b.equation = a", single)

        multiple = _compile_model(specs,
            '<aux name="a"><eqn>1</eqn></aux><aux name="b"><eqn>2</eqn></aux>'
            '<aux name="c"><eqn>a+b</eqn><connect to="c" from="a"/><connect to="c" from="b"/></aux>')
        self.assertIn("c.equation = (a + b)", multiple)


class TestModuleConnections(unittest.TestCase):
    """A variable a module connect feeds is another name for its source."""

    MODEL = (
        '<?xml version="1.0"?><xmile version="1.0" xmlns="http://docs.oasis-open.org/xmile/ns/XMILE/v1.0">'
        '<header><smile version="1.0" uses_submodels="true"/><name>m</name></header>'
        '<sim_specs method="Euler"><start>0</start><stop>3</stop><dt>1</dt></sim_specs>'
        '<model><variables>'
        '<aux name="a"><eqn>3</eqn></aux>'
        '<module name="outer"><connect to="outer.factor" from=".a"/><connect to=".x" from="outer.x"/></module>'
        '<aux name="x" access="input"><eqn>0</eqn></aux>'
        '</variables></model>'
        '<model name="outer"><variables>'
        '<aux name="factor" access="input"><eqn>1</eqn></aux>'
        '<module name="inner"><connect to="inner.factor" from="factor"/><connect to="x" from="inner.y"/></module>'
        '<aux name="x" access="output"><eqn>0</eqn></aux>'
        '</variables></model>'
        '<model name="inner"><variables>'
        '<aux name="factor" access="input"><eqn>1</eqn></aux>'
        '<aux name="y" access="output"><eqn>5 * factor</eqn></aux>'
        '</variables></model></xmile>')

    def _model(self):
        import importlib.util
        tmpdir = tempfile.mkdtemp()
        src, dest = os.path.join(tmpdir, "m.stmx"), os.path.join(tmpdir, "m.py")
        with open(src, "w", encoding="utf-8") as f:
            f.write(self.MODEL)
        compile_xmile(src, dest, "py-sddsl")
        spec = importlib.util.spec_from_file_location("module_connections", dest)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.simulation_model()

    def test_an_input_and_an_output_take_their_sources_values(self):
        model = self._model()
        # The input of the module is the main model's a, not its placeholder 1; the output
        # outside is the module's value, not its placeholder 0
        self.assertEqual(model.converters["outer.factor"](1), 3.0)
        self.assertEqual(model.converters["x"](1), 15.0)


def _load_sdcompiler_standalone(relpath, modname):
    """Load a sdcompiler module as a stand-alone top-level script (as if the
    compiler were run outside the BPTK_Py package): the module's relative
    imports fail and its absolute-import fallback runs. The caller is
    responsible for restoring sys.path / sys.modules. Returns the module."""
    import sys
    import importlib.util
    import BPTK_Py

    sdcompiler_dir = os.path.join(os.path.dirname(BPTK_Py.__file__), "sdcompiler")
    sys.path.insert(0, sdcompiler_dir)
    spec = importlib.util.spec_from_file_location(
        modname, os.path.join(sdcompiler_dir, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestStandaloneImports(unittest.TestCase):
    """The sdcompiler modules carry an absolute-import fallback so they can also
    run as stand-alone scripts outside the BPTK_Py package. Loading each module
    as a top-level script (no package parent) makes its relative imports fail,
    exercising the fallback branch. sys.path / sys.modules are restored after."""

    def _run(self, relpath, modname):
        import sys
        saved_path = list(sys.path)
        saved_modules = set(sys.modules)
        try:
            return _load_sdcompiler_standalone(relpath, modname)
        finally:
            sys.path[:] = saved_path
            for name in set(sys.modules) - saved_modules:
                del sys.modules[name]

    def test_parser_standalone_import(self):
        mod = self._run("parsers/smile/parser.py", "standalone_parser")
        self.assertTrue(hasattr(mod, "parse"))
        self.assertTrue(hasattr(mod, "sanitizeName"))

    def test_xmile_standalone_import(self):
        mod = self._run("parsers/xmile/xmile.py", "standalone_xmile")
        self.assertTrue(hasattr(mod, "parse_xmile"))
        self.assertTrue(hasattr(mod, "sanitizeName"))

    def test_make_name_absolute(self):
        """A name without a dot is qualified with its model; one with a dot is already
        absolute and comes back untouched."""
        from BPTK_Py.sdcompiler.parsers.xmile.xmile import make_name_absolute

        self.assertEqual(make_name_absolute("model", "stock"), "model.stock")
        self.assertEqual(make_name_absolute("model", "other.stock"), "other.stock")

    def test_connects_are_qualified_with_their_model(self):
        """A connection between two elements of a named model carries that name."""
        from BPTK_Py.sdcompiler.parsers.xmile.xmile import extract_connects

        self.assertEqual(extract_connects("sub", [{"@to": "b", "@from": "a"}]),
                         {"sub.b": "sub.a"})
        # A name that is already qualified keeps its own model, and a leading dot names a
        # variable of the main model, as Stella reads it - from any module
        self.assertEqual(extract_connects("sub", [{"@to": ".b", "@from": "other.a"}]),
                         {"b": "other.a"})
