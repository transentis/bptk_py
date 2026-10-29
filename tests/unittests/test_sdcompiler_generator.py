import importlib
import os
import pathlib
import sys
import tempfile
import unittest

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
    """Compile a full XMILE document string with py-sddsl; return the generated source."""
    tmpdir = tempfile.mkdtemp()
    src = os.path.join(tmpdir, "m.stmx")
    dest = os.path.join(tmpdir, "m.py")
    with open(src, "w", encoding="utf-8") as f:
        f.write(xml)
    compile_xmile(src, dest, "py-sddsl")
    with open(dest, "r", encoding="utf-8") as f:
        return f.read()


def _model_of(source):
    """The model a generated source defines."""
    namespace = {}
    exec(compile(source, "<generated>", "exec"), namespace)
    return namespace["simulation_model"]()


class TestSdCompilerCompile(unittest.TestCase):
    def test_unsupported_target_raises(self):
        """compile_xmile rejects an unknown target language before parsing, and names the
        targets it has."""
        with self.assertRaises(Exception) as ctx:
            compile_xmile("irrelevant.stmx", "out.py", "no_such_target")
        self.assertEqual(str(ctx.exception), "Target Language no_such_target not supported: "
                                             "use 'py-sddsl' or 'json-rust-engine'")

    def test_the_py_target_is_gone(self):
        with self.assertRaisesRegex(Exception, "the target 'py' was removed in 3.5.0: use 'py-sddsl'"):
            compile_xmile("irrelevant.stmx", "out.py", "py")

    def test_the_json_target_is_gone(self):
        """The unused `json` target, which dumped the IR, is removed: beside `py-sddsl` and
        the engine's JSON it would only mislead."""
        tmpdir = tempfile.mkdtemp()
        with self.assertRaisesRegex(Exception, "Target Language json not"):
            compile_xmile(os.path.join(tmpdir, "m.stmx"), os.path.join(tmpdir, "m.json"), "json")

    def test_standalone_module_import(self):
        """compile.py can be loaded as a stand-alone script (outside the BPTK_Py package):
        the relative imports fail, the absolute-import fallback runs (standalone=True), and
        compilation still works. sys.path / sys.modules are restored afterwards."""
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
            standalone.compile_xmile(src, dest, "py-sddsl")
            self.assertTrue(os.path.isfile(dest))
        finally:
            sys.path[:] = saved_path
            for name in set(sys.modules) - saved_modules:
                del sys.modules[name]

    def test_comment_only_aux_is_zero(self):
        model = _model_of(_compile_source(_minimal_xmile({"c": "{just a comment}"})))
        self.assertEqual(model.evaluate_equation("c", 1.0), 0.0)

    def test_a_document_without_a_namespace_compiles_alike(self):
        """Tags are read by name with or without the XMILE namespace."""
        model = _minimal_xmile({"a": "1", "b": "a * 2"})
        plain = model.replace(' xmlns="http://docs.oasis-open.org/xmile/ns/XMILE/v1.0"', "")
        self.assertNotEqual(plain, model)
        self.assertEqual(_compile_source(plain), _compile_source(model))

    def test_stock_with_only_outflow(self):
        """A stock that has an outflow but no inflow drains."""
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
        model = _model_of(_compile_source(xml))
        self.assertEqual(model.evaluate_equation("s", 3.0), 90.0)

    def test_mean_over_several_arguments(self):
        """MEAN takes a list of arguments, not only one array."""
        model = _model_of(_compile_source(_minimal_xmile({"a": "2", "b": "3", "meanOfTwo": "MEAN(a, b)"})))
        self.assertEqual(model.evaluate_equation("meanoftwo", 2.0), 2.5)


# ── The py-sddsl target ────────────────────────────────────────────────────────────────

def _xmile(variables, dimensions="", method="Euler", extra=""):
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<xmile version="1.0" xmlns="http://docs.oasis-open.org/xmile/ns/XMILE/v1.0"'
        ' xmlns:isee="http://iseesystems.com/XMILE">\n'
        '<header><smile version="1.0" namespace="std, isee"/><name>m</name>'
        '<vendor>v</vendor><product version="1.0" lang="en">p</product></header>\n'
        '<sim_specs method="{}" time_units="Months"><start>1</start><stop>4</stop><dt>1</dt></sim_specs>\n'
        '{}<model><variables>{}</variables></model>{}\n'
        '</xmile>'.format(method, "<dimensions>{}</dimensions>".format(dimensions) if dimensions else "",
                          variables, extra))


def _aux(name, equation, dims=""):
    dimensions = "<dimensions>{}</dimensions>".format("".join('<dim name="{}"/>'.format(d) for d in dims.split())) if dims else ""
    return '<aux name="{}">{}<eqn>{}</eqn></aux>'.format(name, dimensions, equation)


def _sddsl(xml):
    """Compile with py-sddsl; the generated model."""
    tmpdir = pathlib.Path(tempfile.mkdtemp())
    (tmpdir / "m.stmx").write_text(xml, encoding="utf-8")
    compile_xmile(str(tmpdir / "m.stmx"), str(tmpdir / "m_sddsl.py"), "py-sddsl")
    spec = importlib.util.spec_from_file_location("m_sddsl_{}".format(id(tmpdir)), tmpdir / "m_sddsl.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.simulation_model()


_VECTOR = '<dim name="D" size="3"/>'
_LETTERS = '<dim name="L"><elem name="a"/><elem name="b"/></dim>'


class TestPySddsl(unittest.TestCase):

    def _refused(self, xml, message):
        from BPTK_Py.sdcompiler.generator.sddsl.sddsl import GeneratorError
        with self.assertRaises(GeneratorError) as refusal:
            _sddsl(xml)
        self.assertIn(message, str(refusal.exception))

    def test_the_module_is_laid_out_by_kind(self):
        """Two headings, a subheading per kind the model has, in a fixed order, and the
        elements of each kind by name; a kind the model lacks has no subheading."""
        xml = _xmile('<stock name="s"><eqn>10</eqn><inflow>grow</inflow></stock>'
                     '<flow name="grow"><eqn>rate * s</eqn><non_negative/></flow>'
                     + _aux("rate", "0.1") + _aux("double", "s * 2")
                     + '<aux name="effect"><eqn>s</eqn><gf><xscale min="0" max="10"/>'
                       '<ypts>0,1</ypts></gf></aux>')
        tmpdir = pathlib.Path(tempfile.mkdtemp())
        (tmpdir / "m.stmx").write_text(xml, encoding="utf-8")
        compile_xmile(str(tmpdir / "m.stmx"), str(tmpdir / "m.py"), "py-sddsl")
        lines = [line.strip() for line in (tmpdir / "m.py").read_text(encoding="utf-8").splitlines()]
        comments = [line for line in lines if line.startswith("#")]
        self.assertEqual(
            [comment.rstrip("─ ") for comment in comments],
            ["# ── Defining the elements", "# Stocks", "# Flows", "# Converters", "# Constants",
             "# ── Setting the initial values and equations", "# Graphical functions",
             "# Stocks", "# Flows", "# Converters", "# Constants"])
        converters = lines.index("# Converters")
        self.assertEqual(lines[converters + 1:converters + 3],
                         ["double = self.converter('double')", "effect = self.converter('effect')"])
        self.assertNotIn("s.outflows = []", lines)

    def test_a_kind_lists_the_models_own_elements_before_its_modules(self):
        """Sorted by name alone, the model's own elements fell between the modules."""
        from BPTK_Py.sdcompiler.generator.sddsl.sddsl import _layout_key
        names = ["supply.check", "overview", "market.signal", "customers", "market.attractiveness"]
        self.assertEqual(sorted(names, key=_layout_key),
                         ["customers", "overview", "market.attractiveness", "market.signal", "supply.check"])

    def test_where_stella_computes_differently_the_transpiler_warns(self):
        """MOD bound differently, PULSE without an interval and DELAY with a changing time
        compute differently from Stella once transpiled; each says so once at [WARN]."""
        from tests.helpers.log_helpers import clear_log, read_log
        clear_log()
        model = _sddsl(_xmile(
            _aux("t", "1 + TIME")
            + _aux("first", "7 MOD 3 * 2") + _aux("second", "3 + 5 MOD 4")
            + _aux("unambiguous", "(7 MOD 3) * 2 + (7 * 3 MOD 2) + (5 MOD 4 + 3)")
            + _aux("pulsed", "PULSE(5, 2) + PULSE(5, 2, 0)")
            + _aux("delayed", "DELAY(TIME, t) + DELAY(TIME, 2)")
            + '<aux name="fixed_delay"><eqn>DELAY(TIME, 2) + DELAY(TIME, c)</eqn></aux>' + _aux("c", "2")
            + _aux("arrayed", "TIME MOD 2 * 3", "L"), dimensions=_LETTERS))
        log = read_log()
        self.assertEqual(model.evaluate_equation("first", 1.0), 2.0)
        for name in ("first", "second"):
            self.assertIn("'{}' uses MOD next to".format(name), log)
        self.assertNotIn("'unambiguous' uses MOD", log)
        self.assertEqual(log.count("'pulsed' calls PULSE without an interval"), 1)
        self.assertEqual(log.count("'delayed' calls DELAY"), 1)
        self.assertNotIn("'fixed_delay' calls DELAY", log)
        self.assertEqual(log.count("'arrayed' uses MOD"), 1)

    def test_a_flow_reads_its_own_graphical_function(self):
        """Stella writes a graphical function into a flow as into an aux; the flow is the lookup."""
        model = _sddsl(_xmile(
            '<stock name="s"><eqn>0</eqn><inflow>f</inflow></stock>'
            '<flow name="f"><eqn>TIME</eqn><non_negative/><gf><xscale min="0" max="10"/>'
            '<ypts>0,20</ypts></gf></flow>'))
        self.assertEqual(model.evaluate_equation("f", 2.0), 4.0)

    def test_a_builtin_the_sd_dsl_does_not_know_is_refused(self):
        self._refused(_xmile(_aux("unknown", "NOSUCHBUILTIN(1)")), "The builtin NOSUCHBUILTIN in 'unknown'")

    def test_a_graphical_function_per_element_of_a_flow_is_refused(self):
        self._refused(_xmile(
            '<stock name="s"><dimensions><dim name="L"/></dimensions><eqn>0</eqn><inflow>f</inflow></stock>'
            '<flow name="f"><dimensions><dim name="L"/></dimensions>'
            '<element subscript="a"><eqn>TIME</eqn><gf><xscale min="0" max="10"/><ypts>0,10</ypts></gf></element>'
            '<element subscript="b"><eqn>TIME</eqn><gf><xscale min="0" max="10"/><ypts>0,5</ypts></gf></element>'
            '</flow>', dimensions=_LETTERS), "A graphical function per element of a flow in 'f'")

    def test_a_loop_score_is_left_out_with_a_warning(self):
        """A loop or pathway score is analysis, not simulation: the model compiles without it."""
        from tests.helpers.log_helpers import clear_log, read_log
        clear_log()
        model = _sddsl(_xmile(
            '<stock name="level"><eqn>10</eqn><inflow>growth</inflow></stock>'
            '<flow name="growth"><eqn>level * 0.1</eqn></flow>'
            '<aux name="loop"><eqn>LOOPSCORE(level, growth)</eqn><isee:loopscore/></aux>'
            '<aux name="path"><eqn>PATHSCORE(level, growth, level)</eqn><isee:pathscore/></aux>'
            + _aux("typed", "PATHSCORE(level, growth)")))
        self.assertEqual(model.evaluate_equation("level", 2.0), 11.0)
        self.assertNotIn("loop", model.converters)
        log = read_log()
        self.assertIn("'loop' is a loop score", log)
        self.assertIn("'path' is a pathway score", log)
        self.assertIn("'typed' is a pathway score", log)

    def test_a_function_python_computes_is_refused_for_the_engines_json_only(self):
        """CLOCKTIME is a function of the model's own, which Python answers while the model
        runs: the SD DSL model has it, the JSON can only name it - and the engine on its own
        cannot load a node it has no function for."""
        from BPTK_Py.sdcompiler.generator.sddsl.sddsl import GeneratorError
        xml = _xmile(_aux("clock", "CLOCKTIME"))
        self.assertIn("clock", _sddsl(xml).converters)
        tmpdir = pathlib.Path(tempfile.mkdtemp())
        (tmpdir / "m.stmx").write_text(xml, encoding="utf-8")
        with self.assertRaises(GeneratorError) as refusal:
            compile_xmile(str(tmpdir / "m.stmx"), str(tmpdir / "m.json"), "json-rust-engine")
        self.assertEqual(str(refusal.exception), "Model 'm' calls CLOCKTIME, which Python computes while the "
                         "model runs: the engine's JSON has to run without Python - compile it with py-sddsl")
        self.assertFalse((tmpdir / "m.json").exists())

    def test_forms_the_old_test_models_covered(self):
        """An unnamed matrix, an order held by a constant, LOOKUPAREA over the whole table
        and up to a bound, and RAMP without a start time."""
        dims = '<dim name="A" size="2"/><dim name="B" size="2"/>'
        table = ('<aux name="table"><eqn>TIME</eqn><gf><xscale min="0" max="4"/><yscale min="0" max="4"/>'
                 '<ypts>2,2,2,2,2</ypts></gf></aux>')
        model = _sddsl(_xmile(
            '<aux name="m"><dimensions><dim name="A"/><dim name="B"/></dimensions><eqn>7</eqn></aux>'
            + _aux("order", "3") + _aux("smoothed", "SMTHN(TIME, 2, order)") + table
            + _aux("area", "LOOKUPAREA(table)") + _aux("partArea", "LOOKUPAREA(table, 3)")
            + _aux("rising", "RAMP(2)"), dims))
        self.assertEqual(model.evaluate_equation("m[1][1]", 1.0), 7.0)
        self.assertEqual(model.evaluate_equation("area", 1.0), 8.0)
        self.assertEqual(model.evaluate_equation("partarea", 1.0), 6.0)
        self.assertEqual(model.evaluate_equation("rising", 3.0), 4.0)
        self.assertIn("smoothed", model.equations)

    def test_an_aggregation_takes_its_arguments_as_stella_does(self):
        """SUM, PROD and SIZE take one array; MEAN, MAX and MIN take numbers, or one array -
        Stella allows `*` and ranges only in an aggregation of one argument. In an arrayed
        equation an array's name is its cell, and stays allowed."""
        vec = ('<aux name="vec"><dimensions><dim name="D"/></dimensions>' + "".join(
            '<element subscript="{0}"><eqn>{0}</eqn></element>'.format(i) for i in (1, 2, 3)) + '</aux>')
        for equation, message in (("SUM(a, b)", "SUM of more than one argument"),
                                  ("PROD(a, b)", "PROD of more than one argument"),
                                  ("SIZE(a, b)", "SIZE of more than one argument"),
                                  ("MEAN(vec[*], a)", "MEAN of an array beside other arguments"),
                                  ("MAX(vec[1:2], a)", "MAX of an array beside other arguments")):
            with self.subTest(equation):
                self._refused(_xmile(vec + _aux("a", "2") + _aux("b", "3") + _aux("x", equation), _VECTOR), message)
        cellwise = '<aux name="y"><dimensions><dim name="D"/></dimensions><eqn>MAX(vec, 2)</eqn></aux>'
        model = _sddsl(_xmile(vec + _aux("a", "2") + _aux("b", "3") + _aux("m", "MEAN(a, b)") + cellwise, _VECTOR))
        self.assertEqual(model.evaluate_equation("m", 1.0), 2.5)
        self.assertEqual([model.evaluate_equation("y[{}]".format(i), 1.0) for i in range(3)], [2.0, 2.0, 3.0])

    def test_a_python_name_for_every_xmile_name(self):
        from BPTK_Py.sdcompiler.generator.sddsl.sddsl import python_name
        self.assertEqual(python_name("brewery.inventory"), "brewery__inventory")
        self.assertEqual(python_name("2nd"), "_2nd")
        self.assertEqual(python_name("lambda"), "lambda_")
        self.assertEqual(python_name("sd"), "sd_")

    def test_numbers_aggregations_and_indices(self):
        vec = '<aux name="vec"><dimensions><dim name="D"/></dimensions>' + "".join(
            '<element subscript="{}"><eqn>{}</eqn></element>'.format(i, v) for i, v in ((1, 2), (2, 4), (3, 6))) + "</aux>"
        model = _sddsl(_xmile(vec + _aux("meanof", "MEAN(2, 4)")
                              + _aux("sizerange", "SIZE(vec[1:2])") + _aux("product", "PROD(vec[*] * 2)")
                              + _aux("pick", "vec[(2)]") + _aux("index", "2") + _aux("chosen", "vec[index]")
                              + _aux("beyond", "vec[4]") + _aux("fromtext", "INIT(vec[1])")
                              + _aux("shifted", "vec[index + 1]") + _aux("meanone", "MEAN(5)"), _VECTOR))
        elements = {**model.converters, **model.constants}
        values = {name: elements[name](1) for name in ("meanof", "sizerange", "product", "pick", "chosen",
                                                       "beyond", "shifted", "meanone")}
        self.assertEqual(values, {"meanof": 3.0, "sizerange": 2.0, "product": 384.0,
                                  "pick": 4.0, "chosen": 4.0, "beyond": 0.0, "shifted": 6.0, "meanone": 5.0})

    def test_a_matrix_sliced_and_counted(self):
        matrix = '<aux name="m"><dimensions><dim name="D"/><dim name="L"/></dimensions><eqn>D * 10</eqn></aux>'
        model = _sddsl(_xmile(matrix + _aux("column", "SUM(m[*, b])") + _aux("rowofd", "SUM(m[D, *])", "D")
                              + _aux("whole", "SUM(m[D, b])")
                              + _aux("cells", "SIZE(m)"), _VECTOR + _LETTERS))
        self.assertEqual(model.converters["column"](1), 60.0)
        # A dimension the variable is not arrayed over stands for all of it
        self.assertEqual(model.converters["whole"](1), 60.0)
        self.assertEqual(model.converters["rowofd[0]"](1), 20.0)
        self.assertEqual({**model.converters, **model.constants}["cells"](1), 6.0)

    def test_what_is_refused(self):
        vec = _aux("vec", "1", "D")
        for variables, message in (
                (vec + _aux("whole", "vec"), "The array 'vec' where one value is needed"),
                (_aux("missing", "nowhere[1]"), "The array 'nowhere', which the model does not have"),
                (vec + _aux("toomany", "vec[1, 2]"), "'vec' with 2 indices for 1 dimensions"),
                (_aux("notarray", "PROD(5)"), "PROD of something other than an array"),
                (_aux("nosize", "SIZE(2)"), "SIZE of something other than an array"),
                (_aux("table", "LOOKUP(2 * TIME, 3)"), "A lookup of something other than a graphical function"),
                (_aux("order", "SMTHN(TIME, 2, 2.5)"), "nor a constant that is one"),
                (_aux("counted", "RUNCOUNT"), "RUNCOUNT in 'counted' reads earlier runs"),
                (_aux("sensitive", "SENSIRUNCOUNT"), "SENSIRUNCOUNT in 'sensitive' reads earlier runs"),
                (_aux("ended", "ENDVAL(TIME, 0)"), "ENDVAL in 'ended' reads earlier runs"),
                (_aux("named", "nothing_here"), "'nothingHere' in 'named' is neither a variable")):
            with self.subTest(message):
                self._refused(_xmile(variables, _VECTOR), message)

    def test_a_model_refused_as_a_whole(self):
        self._refused(_xmile(_aux("x", "1"), method="RK4"), "integrates with RK4")
        self._refused(_xmile(_aux("x", "1"), extra='<data><import resource="r../data/series.csv"/></data>'),
                      "imports data from 'r../data/series.csv'")
        exported = _sddsl(_xmile(_aux("x", "1"), extra='<data><export resource="results.xlsx" type="Excel"><all/>'
                                                       '</export></data>'))
        self.assertIn("x", exported.constants)
        leak_zone = ('<stock name="belt"><eqn>0</eqn><inflow>filling</inflow><outflow>leaking</outflow>'
                     '<conveyor><len>2</len></conveyor></stock><flow name="filling"><eqn>1</eqn></flow>'
                     '<flow name="leaking" leak_start="0.5" leak_end="1"><eqn>0.1</eqn><leak/></flow>')
        self._refused(_xmile(leak_zone), "leaks from a zone of its conveyor")
        fill = ('<aux name="source"><dimensions><dim name="D"/></dimensions><eqn>TIME</eqn></aux>'
                '<stock name="belt"><eqn>source[1:2]</eqn><outflow>leaving</outflow>'
                '<conveyor><len>2</len></conveyor></stock><flow name="leaving"/>')
        self._refused(_xmile(fill, _VECTOR), "A fill from 'source', whose elements are not all numbers")

    def test_a_fill_from_a_whole_array_or_a_fixed_cell(self):
        source = '<aux name="source"><dimensions><dim name="D"/><dim name="L"/></dimensions><eqn>3</eqn></aux>'
        belt = ('<stock name="belt"><eqn>source[*, a]</eqn><outflow>leaving</outflow>'
                '<conveyor><len>3</len></conveyor></stock><flow name="leaving"/>')
        model = _sddsl(_xmile(source + belt, _VECTOR + _LETTERS))
        self.assertEqual(model.stocks["belt"](1), 9.0)

    def test_lookuprandom_with_its_options(self):
        table = '<aux name="table"><eqn>TIME</eqn><gf><xscale min="0" max="4"/><yscale min="0" max="2"/><ypts>0,1,2,1,0</ypts></gf></aux>'
        model = _sddsl(_xmile(table + _aux("drawn", "LOOKUPRANDOM(table, 3, 1, 3, 2)")))
        drawn = [model.converters["drawn"](t) for t in (1.0, 2.0, 3.0)]
        self.assertTrue(all(1.0 <= value <= 3.0 for value in drawn))
        # A sample of 2 holds the draw for the next step
        self.assertEqual(drawn[0], drawn[1])

    def test_what_the_parser_never_hands_over_is_refused(self):
        from BPTK_Py.sdcompiler.generator.sddsl.sddsl import GeneratorError, _Generator
        IR = {"name": "m", "specs": {"start": "1", "stop": "2", "dt": 1}, "dimensions": {},
              "models": {"": {"entities": {}}}}
        generator = _Generator(IR)
        generator.entity = {"name": "x"}
        for expression, message in (({"name": "xor", "type": "operator", "args": [1.0, 2.0]}, "The operator 'xor'"),
                                    ({"name": "a", "type": "range", "args": [1.0, 2.0]}, "type 'range'"),
                                    ("text", "'text'"), ([1.0, 2.0], "A list of expressions")):
            with self.subTest(message), self.assertRaisesRegex(GeneratorError, message):
                generator.render(expression)
        self.assertEqual(generator.render([[" 3 "]]), "3.0")
        self.assertEqual(generator.render({"name": "max", "type": "call", "args": [[1.0, [2.0, ","]]]}), "sd.max(1.0, 2.0)")
        self.assertIsNone(generator._static({"name": "f", "type": "call", "args": []}))
        self.assertIsNone(generator._static("text"))
        self.assertIsNone(generator._static([1.0, 2.0]))
