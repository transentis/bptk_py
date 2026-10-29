"""The `py-sddsl` target against Stella's runs and on the engine.

Every XMILE model of the repository is compiled to SD DSL code. Where Stella's run of it is
committed beside it, the SD DSL model is compared with that at every DT. What the SD DSL
cannot express is refused with a message, and each such model is listed with the message it
gets.

Each exception names its reason: a case where the SD DSL departs from Stella on purpose - a
row of "XMILE, Stella and the SD DSL" on the website - or something about an export.
"""

import importlib.util
import pathlib
import re
import xml.etree.ElementTree as ElementTree

import numpy as np
import pytest

from BPTK_Py.sdcompiler.compile import compile_xmile
from BPTK_Py.sdcompiler.generator.sddsl.sddsl import GeneratorError
from BPTK_Py.sdcompiler.plugins.sanitizeNames import sanitizeName
from BPTK_Py.util import timerange
from tests.helpers.stella import PARKED, matches_stella, stella_precision, stella_results

ROOT = pathlib.Path(__file__).resolve().parents[1]
# The website's models, and those with a Stella run beside them
WEBSITE_MODELS = sorted(path for path in (ROOT / "website-tutorial").rglob("*.stmx") if "_output" not in path.parts)
STELLA_MODELS = sorted((ROOT / "tests" / "test_models").glob("*.stmx")) + sorted(PARKED.glob("*.stmx"))


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.simulation_model()


def _compiled(source, directory):
    target = directory / (source.stem + "_sddsl.py")
    compile_xmile(str(source), str(target), "py-sddsl")
    return _load(target, source.stem + "_sddsl")


def _elements(model):
    return {**model.stocks, **model.flows, **model.biflows, **model.converters, **model.constants}


# ── Refused ─────────────────────────────────────────────────────────────────────────

# Each model the SD DSL cannot express, and the start of what it is told
REFUSED = {
    "test_array_3dimensional": "'inventory' in model 'test_array_3dimensional' has 3 dimensions",
    "test_endval": "ENDVAL in 'end' reads earlier runs",
    "arrays_stateful": "'cube' in model 'arrays_stateful' has 3 dimensions",
    "conveyor_options": "The conveyor 'cArrest' uses arrest",
    "modules_external": "The module 'inner' of model 'modules_external' is kept in a file of its own",
    "rk4_builtins": "Model 'rk4_builtins' integrates with RK4",
    "rk4_conveyor": "Model 'rk4_conveyor' integrates with RK4",
    "rk4_feedback": "Model 'rk4_feedback' integrates with RK4",
    "run_builtins": "ENDVAL in 'endOfLastRun' reads earlier runs",
    "run_specs_rk2_instantaneous_false": "Model 'run_specs_rk2_instantaneous_false' integrates with RK2",
    "run_specs_rk2_instantaneous_true": "Model 'run_specs_rk2_instantaneous_true' integrates with RK2",
}


@pytest.mark.parametrize("target", ["py-sddsl", "json-rust-engine"])
@pytest.mark.parametrize("source", [path for path in STELLA_MODELS if path.stem in REFUSED],
                         ids=lambda path: path.stem)
def test_what_the_sd_dsl_cannot_express_is_refused_with_its_reason(tmp_path, source, target):
    """Both targets refuse alike: the engine's JSON is written from the SD DSL model."""
    with pytest.raises(GeneratorError) as refusal:
        compile_xmile(str(source), str(tmp_path / "out"), target)
    assert str(refusal.value).startswith(REFUSED[source.stem])
    assert not (tmp_path / "out").exists()


def test_every_refused_model_is_a_model():
    stems = {path.stem for path in STELLA_MODELS}
    assert set(REFUSED) <= stems


def test_the_parked_models_are_the_refused_ones():
    """A Stella model waits in `stella_parked/` exactly when the SD DSL cannot express it."""
    parked = {path.stem for path in PARKED.glob("*.stmx")}
    assert parked == set(REFUSED) | set(STELLA_UNREADABLE)


def _constructs(source):
    """What a Stella model uses, coarsely: its builtins, and each kind of element with what
    it carries - a graphical function and its type, dimensions, non-negativity, a conveyor."""
    text = source.read_text(encoding="utf-8", errors="replace")
    found = set()
    for tag in ("stock", "flow", "aux"):
        for body in re.findall(r"<{0}\b[^>]*>(.*?)</{0}>".format(tag), text, re.S):
            kind = tag if tag != "flow" else ("flow" if "<non_negative" in body else "biflow")
            arrayed = " arrayed" if "<dimensions" in body else ""
            for attributes in re.findall(r"<gf([^>]*)>", body):
                gf_type = re.search(r'type="([^"]+)"', attributes)
                per_element = " per element" if "<element" in body else ""
                found.add("graphical function {} in {}{}{}".format(
                    gf_type.group(1) if gf_type else "continuous", kind, arrayed, per_element))
            found.add(kind + arrayed)
            if "<conveyor" in body:
                found.add("conveyor" + arrayed)
            for equation in re.findall(r"<eqn>(.*?)</eqn>", body, re.S):
                found |= {"builtin " + name for name in re.findall(r"\b([A-Z][A-Z0-9_]+)\s*\(", equation.upper())}
    return found


# What a parked model may hold that no model compared with Stella holds: the construct it is
# refused for
PARKED_ONLY = {"run_builtins": {"builtin ENDVAL"}, "test_endval": {"builtin ENDVAL"}}


def test_a_parked_model_hides_nothing_else():
    """A parked model is only checked for its refusal. Anything else in it that no compared model
    holds goes unchecked - a flow's own graphical function did, until its model was unparked."""
    compared = [path for path in STELLA_MODELS if path.parent != PARKED
                and path.stem not in set(NO_EXPORT) | STELLA_DRAWS]
    covered = set().union(*(_constructs(path) for path in compared))
    hidden = {path.stem: _constructs(path) - covered - PARKED_ONLY.get(path.stem, set())
              for path in sorted(PARKED.glob("*.stmx"))}
    assert {stem: constructs for stem, constructs in hidden.items() if constructs} == {}


# ── Against Stella ──────────────────────────────────────────────────────────────────

_ROW = "the SD DSL departs from Stella on purpose: the row {} of \"XMILE, Stella and the SD DSL\""

# Where the SD DSL departs from Stella's run, by model and column
STELLA_DIFFERS = {
    "agecount_transit_change": {column: _ROW.format("AGECOUNT on a conveyor whose transit time changes") for column in (
        "leaking older", "leaking young", "longer older", "longer young", "shorter older", "shorter young")},
    "modules_all_elements": {column: _ROW.format("AGECOUNT on a conveyor whose transit time changes")
                             for column in ("supply.young", "overview")},
    "delay_variable": {column: _ROW.format("DELAY(input, T) with T changing") for column in ("delayed", "delayed init")},
    "delays": {"delay var": _ROW.format("DELAY(input, T) with T changing")},
    "domain_combinatorics": {**{column: _ROW.format("FACTORIAL(2.5)") for column in (
        "comb frac", "comb frac 2", "fact frac", "perm frac", "perm frac 2", "comb neg r", "perm neg r")},
        **{column: _ROW.format("FACTORIAL(168) to FACTORIAL(171)") for column in ("fact 171", "fact 172")}},
    "domain_delay": {column: _ROW.format("DELAY(input, 0)") for column in ("d 0 3", "minus 3", "minus 1", "d 0")},
    "domain_delay_short_dt_quarter": {column: _ROW.format("DELAY(input, 0)") for column in ("d 0 1", "minus 0 1")},
    "finance": {"irr 1": "Stella's IRR stops its iteration within 1e-7 of the rate, -0.699999926 for -0.7"},
    "math_rounding": {column: _ROW.format("-7 MOD 3") for column in ("mod negative left", "mod negative right")},
    "operators": {"mod times": _ROW.format("7 MOD 3 * 2")},
    "pulse_start_0_dt_quarter": {column: _ROW.format("PULSE(20)") for column in (
        "s volume only", "p volume only", "s first only", "p first only", "a volume only")},
    "pulse_start_1_dt_1": {column: _ROW.format("PULSE(20)") for column in (
        "s volume only", "p volume only", "s first only", "p first only", "a volume only")},
    "stella_extras": {**{column: _ROW.format("LOOKUPMEAN(table, 3, 5)") for column in (
        "lookupmean const 3 5", "lookupmean const 5 3", "lookupmean range 3 5", "lookupmean shape 5 3",
        "lookupmean shape from 0 1 3")},
        **{column: _ROW.format("PERCENTILE(values, 0, 0, weights)") for column in (
            "percentile orig w last 6", "percentile w equal", "percentile w first 2", "percentile w last 2",
            "percentile w last half", "percentile w middle 3")}},
}

# Models without an export of a Stella run, each with the reason
NO_EXPORT = {
    "beta_5_a2_b5": "BETA(2, 5) stops Stella's run at its third draw",
    "domain_normalpink_zero": "a correlation time of 0 stops Stella's run",
    "domain_sinwave_period_0": "SINWAVE with a period of 0 stops Stella's run",
    "domain_sqrt_negative": "SQRT(-4) stops Stella's run",
    # Two models of the tests of the target `py`, kept for their refusal
    "test_array_3dimensional": "kept from the tests of `py` for its refusal, never run in Stella",
    "test_endval": "kept from the tests of `py` for its refusal, never run in Stella",
}


def test_every_stella_check_has_its_run_beside_it():
    """An export left out of a commit would leave its model compiled but never compared."""
    without = {path.stem for path in STELLA_MODELS if not (path.parent / (path.stem + "_results.csv")).exists()}
    assert without == set(NO_EXPORT)


# Columns of an export the transpiler leaves out of the model, by model: the scores of loop
# dominance analysis, which compute nothing the simulation reads
LEFT_OUT = {"converter_kinds": {"growth link score", "growth path score", "loop r1", "pathway r1"}}


def _compared(source, stella):
    """The columns of Stella's export to compare. A column twice in an export comes back as
    "name.1": the way through Excel doubled it."""
    return [column for column in stella.columns if not re.search(r"\.\d+$", column)
            and column not in LEFT_OUT.get(source.stem, set())]


# Models whose export is compared in its moments elsewhere, not value by value: they draw
STELLA_DRAWS = {"random_dt_1", "random_dt_quarter", "beta_1_a0_5_b0_5", "beta_5_a2_b5", "domain_normalpink_short"}
# The file keeps no link to the data it imports - Stella saved it without - so it cannot be
# refused, and computes without its data
STELLA_UNREADABLE = {"imported_data": "the link to its imported data is not in the file"}


def _column_element(model, column):
    """The element of a column of Stella's export: its name as the compiler spells it, a
    cell of an unnamed array shifted to count from 0."""
    match = re.fullmatch(r"(.*)\[(.*)\]", column)
    elements = _elements(model)
    if not match:
        name = sanitizeName(column)
        return name if name in elements else None
    base, labels = sanitizeName(match.group(1)), [label.strip() for label in match.group(2).split(",")]
    for candidate in (base + "".join("[{}]".format(int(label) - 1) for label in labels)
                      if all(label.isdigit() for label in labels) else None,
                      base + "".join("[{}]".format(sanitizeName(label)) for label in labels)):
        if candidate in elements:
            return candidate
    return None


@pytest.mark.parametrize("source", [path for path in STELLA_MODELS
                                    if path.stem not in REFUSED and path.stem not in STELLA_UNREADABLE
                                    and (path.parent / (path.stem + "_results.csv")).exists()],
                         ids=lambda path: path.stem)
def test_every_stella_check_computes_as_stella_does(tmp_path, source):
    model = _compiled(source, tmp_path)
    stella = stella_results(source.stem)
    columns = _compared(source, stella)
    found = {column: _column_element(model, column) for column in columns}
    if source.stem in STELLA_DRAWS:
        model.simulate(sorted({name for name in found.values() if name}))
        return
    assert all(found.values()), [column for column, name in found.items() if not name]
    results = model.simulate(sorted(set(found.values())))
    precision = stella_precision(source.stem)
    differing = [column for column, name in found.items()
                 if not matches_stella([results[name].get(t, np.nan) for t in stella.index],
                                       stella[column].values, precision[column].values).all()]
    assert sorted(differing) == sorted(STELLA_DIFFERS.get(source.stem, {})), source.stem


# ── Inside a module ─────────────────────────────────────────────────────────────────

_XMILE = "http://docs.oasis-open.org/xmile/ns/XMILE/v1.0"


def _in_a_module(source, directory, module="m"):
    """The model moved into a module of its own, with nothing connected to it: a model that
    computes what the model itself does, every element under `m.` - a module of a module
    where the model has modules of its own."""
    ElementTree.register_namespace("", _XMILE)
    ElementTree.register_namespace("isee", "http://iseesystems.com/XMILE")
    tree = ElementTree.parse(source)
    root = tree.getroot()
    root.find("{{{0}}}header/{{{0}}}smile".format(_XMILE)).set("uses_submodels", "true")
    main = next(model for model in root.findall("{{{}}}model".format(_XMILE)) if model.get("name") is None)
    inner = ElementTree.SubElement(root, "{{{}}}model".format(_XMILE), {"name": module})
    for child in list(main):
        main.remove(child)
        inner.append(child)
    variables = ElementTree.SubElement(main, "{{{}}}variables".format(_XMILE))
    ElementTree.SubElement(variables, "{{{}}}module".format(_XMILE), {"name": module})
    # A leading dot names the main model; what was the main model is the module now, and
    # a connect of a module inside it names that one without the dot
    for connect in inner.iter("{{{}}}connect".format(_XMILE)):
        for end in ("to", "from"):
            if connect.get(end, "").startswith("."):
                connect.set(end, connect.get(end)[1:])
    target = directory / (source.stem + "_in_a_module.stmx")
    tree.write(target, xml_declaration=True, encoding="utf-8")
    return target


@pytest.mark.parametrize("source", [path for path in STELLA_MODELS
                                    if path.stem not in set(REFUSED) | STELLA_DRAWS | set(STELLA_UNREADABLE)
                                    and (path.parent / (path.stem + "_results.csv")).exists()],
                         ids=lambda path: path.stem)
def test_every_stella_check_computes_as_stella_does_inside_a_module(tmp_path, source):
    """Every element of a model works inside a module: the model, moved into one, computes
    Stella's run under the module's name. A variable of a module of the model keeps its own
    name, the module's. On the Python engine only: a module changes names before the model
    reaches the engine, and every compiled model is compared on both engines above."""
    model = _compiled(_in_a_module(source, tmp_path), tmp_path)
    stella = stella_results(source.stem)
    columns = _compared(source, stella)
    found = {column: _column_element(model, "m." + column) or _column_element(model, column) for column in columns}
    assert all(found.values()), [column for column, name in found.items() if not name]
    results = model.simulate(sorted(set(found.values())))
    precision = stella_precision(source.stem)
    differing = [column for column, name in found.items()
                 if not matches_stella([results[name].get(t, np.nan) for t in stella.index],
                                       stella[column].values, precision[column].values).all()]
    assert sorted(differing) == sorted(STELLA_DIFFERS.get(source.stem, {})), source.stem


# ── On the engine ───────────────────────────────────────────────────────────────────

@pytest.mark.requires_rust
@pytest.mark.parametrize("source", [path for path in WEBSITE_MODELS + STELLA_MODELS
                                    if path.stem not in set(REFUSED) | STELLA_DRAWS],
                         ids=lambda path: path.stem)
def test_every_compiled_model_computes_the_same_on_the_engine(tmp_path, source):
    model = _compiled(source, tmp_path)
    names = sorted(name for name, element in _elements(model).items()
                   if element._elements.vector_size() == 0 and not name.startswith("bptk_"))
    python, rust = model.simulate(names), model.simulate(names, backend="rust")
    assert np.allclose(python[names].values, rust[names].values, rtol=1e-9, atol=1e-9, equal_nan=True)


# ── The engine's JSON, derived from the SD DSL ──────────────────────────────────────

def _engine_run(source, directory, names):
    """The model compiled to the engine's JSON, run on the engine: {name: [value per step]}."""
    from BPTK_Py._rust_engine import RustSdEngine
    target = directory / (source.stem + ".json")
    compile_xmile(str(source), str(target), "json-rust-engine")
    raw = RustSdEngine().load_model(target.read_text()).simulate(names)
    return {name: [value for _, value in sorted(raw[name].items(), key=lambda item: float(item[0]))]
            for name in names}


@pytest.mark.requires_rust
@pytest.mark.parametrize("source", [path for path in WEBSITE_MODELS + STELLA_MODELS
                                    if path.stem not in set(REFUSED) | STELLA_DRAWS | set(STELLA_UNREADABLE)],
                         ids=lambda path: path.stem)
def test_the_engines_json_computes_as_the_sd_dsl_model(tmp_path, source):
    model = _compiled(source, tmp_path)
    names = sorted(name for name, element in _elements(model).items() if element._elements.vector_size() == 0)
    python = model.simulate(names)
    engine = _engine_run(source, tmp_path, names)
    for name in names:
        assert np.allclose(python[name].values, engine[name], rtol=1e-9, atol=1e-9, equal_nan=True), name


@pytest.mark.requires_rust
@pytest.mark.parametrize("source", [path for path in STELLA_MODELS
                                    if path.stem not in set(REFUSED) | STELLA_DRAWS | set(STELLA_UNREADABLE)
                                    and (path.parent / (path.stem + "_results.csv")).exists()],
                         ids=lambda path: path.stem)
def test_every_stella_check_computes_as_stella_does_from_the_engines_json(tmp_path, source):
    model = _compiled(source, tmp_path)
    stella = stella_results(source.stem)
    columns = _compared(source, stella)
    found = {column: _column_element(model, column) for column in columns}
    engine = _engine_run(source, tmp_path, sorted(set(found.values())))
    times = list(np.round(np.array(timerange(model.starttime, model.stoptime, model.dt, exclusive=False)), 10))
    precision = stella_precision(source.stem)
    differing = []
    for column, name in found.items():
        by_time = dict(zip(times, engine[name]))
        computed = [by_time.get(round(float(t), 10), np.nan) for t in stella.index]
        if not matches_stella(computed, stella[column].values, precision[column].values).all():
            differing.append(column)
    assert sorted(differing) == sorted(STELLA_DIFFERS.get(source.stem, {})), source.stem
