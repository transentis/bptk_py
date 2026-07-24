import os
import tempfile
import unittest
from unittest import mock

from BPTK_Py.sdcompiler.compile import compile_xmile


def _minimal_xmile(equations):
    """Build a minimal (view-less) XMILE document from a {name: eqn} mapping.

    Only the header, sim_specs and a <variables> block are needed for the
    compiler; the graphical <views> section is irrelevant to transpilation.
    """
    vars_xml = "".join(
        '<aux name="{}"><eqn>{}</eqn></aux>'.format(name, eqn)
        for name, eqn in equations.items()
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<xmile version="1.0" xmlns="http://docs.oasis-open.org/xmile/ns/XMILE/v1.0"'
        ' xmlns:isee="http://iseesystems.com/XMILE">\n'
        '<header><smile version="1.0" namespace="std, isee"/><name>m</name>'
        '<uuid>x</uuid><vendor>v</vendor><product version="1.0" lang="en">p</product></header>\n'
        '<sim_specs method="Euler" time_units="Months"><start>1</start><stop>5</stop><dt>1</dt></sim_specs>\n'
        '<model><variables>{}</variables></model>\n'
        '</xmile>'.format(vars_xml)
    )


def _compile_source(xml):
    """Compile a full XMILE document string to Python; return the generated source."""
    tmpdir = tempfile.mkdtemp()
    src = os.path.join(tmpdir, "m.stmx")
    dest = os.path.join(tmpdir, "m.py")
    with open(src, "w", encoding="utf-8") as f:
        f.write(xml)
    compile_xmile(src, dest, "py")
    with open(dest, "r", encoding="utf-8") as f:
        return f.read()


_ARRAY_MODEL = '''<?xml version="1.0" encoding="utf-8"?>
<xmile version="1.0" xmlns="http://docs.oasis-open.org/xmile/ns/XMILE/v1.0" xmlns:isee="http://iseesystems.com/XMILE">
<header><smile version="1.0" namespace="std, isee"/><name>m</name><uuid>x</uuid><vendor>v</vendor><product version="1.0" lang="en">p</product></header>
<sim_specs method="Euler" time_units="Months"><start>1</start><stop>3</stop><dt>1</dt></sim_specs>
<dimensions><dim name="Dim" size="3"/></dimensions>
<model><variables>
<aux name="vec"><dimensions><dim name="Dim"/></dimensions>
<element subscript="1"><eqn>1</eqn></element>
<element subscript="2"><eqn>2</eqn></element>
<element subscript="3"><eqn>3</eqn></element>
</aux>
<aux name="total"><eqn>SUM(vec[*])</eqn></aux>
<aux name="avg"><eqn>MEAN(vec[*])</eqn></aux>
<aux name="product"><eqn>PROD(vec[*])</eqn></aux>
<aux name="cnt"><eqn>SIZE(vec[*])</eqn></aux>
</variables></model>
</xmile>'''


def _compile_equations(equations):
    """Compile a minimal model with the given equations to Python; return the source."""
    tmpdir = tempfile.mkdtemp()
    src = os.path.join(tmpdir, "m.stmx")
    dest = os.path.join(tmpdir, "m.py")
    with open(src, "w", encoding="utf-8") as f:
        f.write(_minimal_xmile(equations))
    compile_xmile(src, dest, "py")
    with open(dest, "r", encoding="utf-8") as f:
        return f.read()


class TestSdCompilerCompile(unittest.TestCase):
    def test_unsupported_target_raises(self):
        """compile_xmile rejects an unknown target language before parsing."""
        with self.assertRaises(Exception) as ctx:
            compile_xmile("irrelevant.stmx", "out.py", "no_such_target")
        self.assertIn("not (yet) supported", str(ctx.exception))

    def test_standalone_module_import(self):
        """compile.py can be loaded as a stand-alone script (outside the BPTK_Py package):
        the relative imports fail, the absolute-import fallback runs (standalone=True), and
        compilation still works. sys.path / sys.modules are restored afterwards."""
        import sys
        import importlib.util
        import BPTK_Py

        sdcompiler_dir = os.path.join(os.path.dirname(BPTK_Py.__file__), "sdcompiler")
        saved_path = list(sys.path)
        saved_modules = set(sys.modules)
        sys.path.insert(0, sdcompiler_dir)
        try:
            spec = importlib.util.spec_from_file_location(
                "standalone_compile", os.path.join(sdcompiler_dir, "compile.py"))
            standalone = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(standalone)

            self.assertTrue(standalone.standalone)  # took the absolute-import fallback

            # And it actually compiles in standalone mode.
            tmpdir = tempfile.mkdtemp()
            src = os.path.join(tmpdir, "m.stmx")
            dest = os.path.join(tmpdir, "m.py")
            with open(src, "w", encoding="utf-8") as f:
                f.write(_minimal_xmile({"a": "1"}))
            standalone.compile_xmile(src, dest, "py")
            self.assertTrue(os.path.isfile(dest))
        finally:
            sys.path[:] = saved_path
            for name in set(sys.modules) - saved_modules:
                del sys.modules[name]

    def test_unknown_function_is_skipped(self):
        """An unimplemented SMILE function falls into the KeyError branch of
        parseExpression: it logs a warning and generates "0" rather than crashing."""
        code = _compile_equations({"a": "1", "u": "FOOBAR(a)"})
        self.assertIn("import numpy as np", code)

    def test_parse_expression_defensive_branches(self):
        """parseExpression's malformed-IR safety nets: an empty '()' node yields 0, while
        an unknown operator and an unknown node type both raise."""
        from BPTK_Py.sdcompiler.generator.py import py
        self.assertEqual(py.parseExpression({"type": "()", "args": []}), 0)
        with self.assertRaises(Exception):
            py.parseExpression({"type": "operator", "name": "NOTANOP", "args": [1, 2]})
        with self.assertRaises(Exception):
            py.parseExpression({"type": "totally_unknown_node"})

    def test_handler_keyerror_skipped_but_typeerror_propagates(self):
        """parseExpression treats a handler KeyError as "not implemented" (returns "0"),
        but must let a TypeError propagate — otherwise real handler bugs get hidden
        (this is what once masked the NORMAL defect)."""
        from BPTK_Py.sdcompiler.generator.py import py
        call_expr = {"type": "call", "name": "boom", "args": []}

        with mock.patch.dict(py.builtins, {"boom": mock.Mock(side_effect=KeyError("x"))}):
            self.assertEqual(py.parseExpression(call_expr), "0")

        with mock.patch.dict(py.builtins, {"boom": mock.Mock(side_effect=TypeError("x"))}):
            with self.assertRaises(TypeError):
                py.parseExpression(call_expr)

    def test_comment_only_aux_becomes_constant(self):
        """An aux whose equation is a comment resolves to 0.0, so the context builder
        classifies it as a constant (contextBuilder numeric-expression branch)."""
        code = _compile_source(
            '<?xml version="1.0"?><xmile version="1.0"'
            ' xmlns="http://docs.oasis-open.org/xmile/ns/XMILE/v1.0"'
            ' xmlns:isee="http://iseesystems.com/XMILE">'
            '<header><smile version="1.0" namespace="std, isee"/><name>m</name>'
            '<uuid>x</uuid><vendor>v</vendor><product version="1.0" lang="en">p</product></header>'
            '<sim_specs method="Euler" time_units="Months"><start>1</start><stop>3</stop><dt>1</dt></sim_specs>'
            '<model><variables><aux name="c"><eqn>{just a comment}</eqn></aux></variables></model></xmile>'
        )
        self.assertIn("import numpy as np", code)


class TestSdCompilerGeneratorFunctions(unittest.TestCase):
    def test_statistical_function_handlers(self):
        """Statistical/probabilistic SMILE functions (and their seeded variants)
        generate Python code without error."""
        code = _compile_equations({
            "a": "10", "b": "2", "p": "0.5", "seed": "5", "lam": "1.5",
            "e_beta": "BETA(a,b)", "e_beta_s": "BETA(a,b,seed)",
            "e_comb": "COMBINATIONS(a,b)",
            "e_binom": "BINOMIAL(a,p)", "e_binom_s": "BINOMIAL(a,p,seed)",
            "e_exprnd": "EXPRND(lam)", "e_exprnd_s": "EXPRND(lam,seed)",
            "e_gamma1": "GAMMA(a)", "e_gamma": "GAMMA(a,b)", "e_gamma_s": "GAMMA(a,b,seed)",
            "e_geom": "GEOMETRIC(p)", "e_geom_s": "GEOMETRIC(p,seed)",
            "e_normal": "NORMAL(a,b)", "e_normal_s": "NORMAL(a,b,seed)",
            "e_gammaln": "GAMMALN(a)",
            "e_gammaln2": "GAMMALN(a,b)",  # >1 arg -> "only one argument" warning branch
            "e_fact": "FACTORIAL(a)",
        })
        self.assertIn("import numpy as np", code)

    def test_pulse_previous_if_branches(self):
        """PULSE with a first-time but no interval, PREVIOUS (no initial value), and an
        IF/THEN/ELSE statement all take their respective generator branches. Note the
        arguments must be identifiers (not literals) to reach these paths."""
        code = _compile_equations({
            "v": "10", "f": "2", "a": "3", "c": "1", "x": "5",
            "e_pulse1": "PULSE(v)",         # single-argument pulse (volume only)
            "e_pulse": "PULSE(v, f)",       # first set, no interval
            "e_prev": "PREVIOUS(a)",        # previous without an initial value
            "e_prev2": "PREVIOUS(a, x)",    # previous with an initial value
            "e_if": "IF c THEN x ELSE 1",   # if/then/else
            "e_if2": "IF c THEN ELSE 1",    # empty then-branch -> defaults to "0"
        })
        self.assertIn("import numpy as np", code)

    def test_financial_unsupported_terminal_argument(self):
        """PMT/FV/PV with a non-zero terminal (future/present value) argument hit the
        "not yet supported" fallback branch."""
        code = _compile_equations({
            "c": "100", "p": "0.05", "n": "12",
            "e_pmt": "PMT(p, n, c, 50)",
            "e_fv": "FV(p, n, c, 50)",
            "e_pv": "PV(p, n, c, 50)",
        })
        self.assertIn("import numpy as np", code)

    def test_array_reduction_functions(self):
        """SUM/MEAN/PROD/SIZE over an arrayed variable exercise the array-function
        handlers and the array-expansion plugin."""
        code = _compile_source(_ARRAY_MODEL)
        self.assertIn("import numpy as np", code)

    def test_endval_and_pulse_branches(self):
        """ENDVAL with a non-identifier input takes the error fallback; the PULSE
        interval==0 and interval>0 variants take their respective branches."""
        code = _compile_equations({
            "e_endval": "ENDVAL(5)",        # literal (no identifier) -> error fallback
            "e_pulse0": "PULSE(10, 2, 0)",  # interval == 0
            "e_pulse3": "PULSE(10, 2, 3)",  # interval > 0
        })
        self.assertIn("import numpy as np", code)

    def test_json_generator_target(self):
        """The 'json' generator target serialises the intermediate representation."""
        xml = (
            '<?xml version="1.0"?><xmile version="1.0"'
            ' xmlns="http://docs.oasis-open.org/xmile/ns/XMILE/v1.0"'
            ' xmlns:isee="http://iseesystems.com/XMILE">'
            '<header><smile version="1.0" namespace="std, isee"/><name>m</name>'
            '<uuid>x</uuid><vendor>v</vendor><product version="1.0" lang="en">p</product></header>'
            '<sim_specs method="Euler" time_units="Months"><start>1</start><stop>3</stop><dt>1</dt></sim_specs>'
            '<model><variables><aux name="a"><eqn>1</eqn></aux></variables></model></xmile>'
        )
        tmpdir = tempfile.mkdtemp()
        src = os.path.join(tmpdir, "m.stmx")
        dest = os.path.join(tmpdir, "m.json")
        with open(src, "w", encoding="utf-8") as f:
            f.write(xml)
        compile_xmile(src, dest, "json")
        with open(dest, "r", encoding="utf-8") as f:
            import json as _json
            data = _json.loads(f.read())
        self.assertIn("models", data)

    def test_stock_with_only_outflow(self):
        """A stock that has an outflow but no inflow compiles (net-flow = -outflow)."""
        xml = (
            '<?xml version="1.0"?><xmile version="1.0"'
            ' xmlns="http://docs.oasis-open.org/xmile/ns/XMILE/v1.0"'
            ' xmlns:isee="http://iseesystems.com/XMILE">'
            '<header><smile version="1.0" namespace="std, isee"/><name>m</name>'
            '<uuid>x</uuid><vendor>v</vendor><product version="1.0" lang="en">p</product></header>'
            '<sim_specs method="Euler" time_units="Months"><start>1</start><stop>3</stop><dt>1</dt></sim_specs>'
            '<model><variables>'
            '<stock name="s"><eqn>100</eqn><outflow>drain</outflow></stock>'
            '<flow name="drain"><eqn>5</eqn></flow>'
            '</variables></model></xmile>'
        )
        code = _compile_source(xml)
        self.assertIn("import numpy as np", code)

    def test_history_rank_triangular_branches(self):
        """HISTORY with a variable time arg, RANK with >2 args, and TRIANGULAR with
        more than 4 args exercise their respective branches."""
        code = _compile_equations({
            "a": "10", "b": "2", "c": "3", "d": "4", "e": "5",
            "e_hist": "HISTORY(a, b)",
            "e_rank": "RANK(a, b, c)",
            "e_tri": "TRIANGULAR(a, b, c, d, e)",
        })
        self.assertIn("import numpy as np", code)


if __name__ == '__main__':
    unittest.main()
