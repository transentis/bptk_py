import os
import tempfile
import unittest

from BPTK_Py.sdcompiler.compile import compile_xmile
from BPTK_Py.sdcompiler.parsers.smile.grammar import SMILEVisitor, grammar


def _parse(eqn):
    """Parse a SMILE equation string into its IR node via the grammar + visitor."""
    return SMILEVisitor().visit(grammar.parse(eqn))


def _compile_model(sim_specs, variables):
    """Compile a minimal XMILE document (custom sim_specs + variables) to Python."""
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
    compile_xmile(src, dest, "py")
    with open(dest, "r", encoding="utf-8") as f:
        return f.read()


class TestSmileGrammar(unittest.TestCase):
    def test_if_without_else(self):
        """IF ... THEN ... (no ELSE) produces a two-argument if-call."""
        result = _parse("IF x THEN y")
        self.assertEqual(result["name"], "if")
        self.assertEqual(result["type"], "call")
        self.assertEqual(len(result["args"]), 2)  # condition + then, no else

    def test_namespaced_identifier(self):
        """A dotted (namespaced) identifier is parsed as a single identifier node."""
        result = _parse("model.var")
        self.assertEqual(result["type"], "identifier")
        self.assertEqual(result["name"], "model.var")

    def test_boolean_operators(self):
        """AND / OR boolean operators build operator nodes."""
        self.assertEqual(_parse("a=1 OR b=2")["name"], "OR")
        self.assertEqual(_parse("a=1 AND b=2")["name"], "AND")

    def test_scientific_notation(self):
        """Regression guard for the visit_exponent fix: exponent notation parses to a
        float (previously crashed with 'list has no attribute text')."""
        self.assertEqual(_parse("2e3"), 2000.0)
        self.assertEqual(_parse("1.5e-3"), 0.0015)
        self.assertEqual(_parse("1.0e5"), 100000.0)

    def test_enclosed_identifier(self):
        """A quoted identifier is parsed as an identifier node."""
        result = _parse('"quoted_id"')
        self.assertEqual(result["type"], "identifier")


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
        self.assertIn("import numpy as np", code)

    def test_dt_with_text_node(self):
        """A dt given as an element with attributes (dict with #text, non-reciprocal)."""
        code = _compile_model(
            '<sim_specs method="Euler" time_units="Months"><start>1</start><stop>5</stop>'
            '<dt units="months">2</dt></sim_specs>',
            '<aux name="a"><eqn>1</eqn></aux>',
        )
        self.assertIn("import numpy as np", code)

    def test_connects_single_and_multiple(self):
        """Element <connect> data is extracted for both a single connect (dict) and
        multiple connects (list)."""
        specs = ('<sim_specs method="Euler" time_units="Months"><start>1</start>'
                 '<stop>5</stop><dt>1</dt></sim_specs>')
        single = _compile_model(specs,
            '<aux name="a"><eqn>1</eqn></aux>'
            '<aux name="b"><eqn>a</eqn><connect to="b" from="a"/></aux>')
        self.assertIn("import numpy as np", single)

        multiple = _compile_model(specs,
            '<aux name="a"><eqn>1</eqn></aux><aux name="b"><eqn>2</eqn></aux>'
            '<aux name="c"><eqn>a+b</eqn><connect to="c" from="a"/><connect to="c" from="b"/></aux>')
        self.assertIn("import numpy as np", multiple)


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

    def test_grammar_standalone_import(self):
        mod = self._run("parsers/smile/grammar.py", "standalone_grammar")
        # sanitizeName came in through the absolute-import fallback.
        self.assertTrue(hasattr(mod, "SMILEVisitor"))
        self.assertTrue(hasattr(mod, "sanitizeName"))

    def test_xmile_standalone_import(self):
        mod = self._run("parsers/xmile/xmile.py", "standalone_xmile")
        self.assertTrue(hasattr(mod, "parse_xmile"))
        self.assertTrue(hasattr(mod, "sanitizeName"))


if __name__ == '__main__':
    unittest.main()
