"""Direct tests for the XMILE compiler plugins that were covered only through whole models."""

from BPTK_Py.sdcompiler.plugins import filterGhosts, resolveSelf, sanitizeName, sortEntities


def _ir(entities):
    """An intermediate representation with one model holding the given entities."""
    return {"models": {"m": {"entities": entities}}}


def test_filter_ghosts_gives_an_empty_equation_a_zero():
    ir = _ir({"stock": [{"name": "empty", "equation_parsed": []},
                        {"name": "full", "equation_parsed": ["1.0"]}]})

    stocks = filterGhosts(ir)["models"]["m"]["entities"]["stock"]

    assert stocks[0]["equation_parsed"] == ["0"]
    assert stocks[1]["equation_parsed"] == ["1.0"]


def test_resolve_self_names_the_entity_it_belongs_to():
    self_reference = {"name": "self", "type": "identifier"}
    other = {"name": "other", "type": "identifier"}
    call = {"name": "delay", "type": "call", "args": [dict(self_reference), other, 2.0]}
    ir = _ir({"flow": [{"name": "inflow", "equation_parsed": [call]}]})

    parsed = resolveSelf(ir)["models"]["m"]["entities"]["flow"][0]["equation_parsed"]

    # Inside the arguments of a call too, and nothing else is touched
    assert parsed[0]["args"][0]["name"] == "inflow"
    assert parsed[0]["args"][1] == {"name": "other", "type": "identifier"}
    assert parsed[0]["args"][2] == 2.0


def test_resolve_self_leaves_a_call_named_self_alone():
    ir = _ir({"flow": [{"name": "inflow", "equation_parsed": [{"name": "self", "type": "call"}]}]})

    parsed = resolveSelf(ir)["models"]["m"]["entities"]["flow"][0]["equation_parsed"]

    assert parsed[0]["name"] == "self"


def test_sanitize_name_makes_a_camel_case_identifier():
    assert sanitizeName("my_stock") == "myStock"
    assert sanitizeName("My Stock") == "myStock"
    assert sanitizeName("two  spaces") == "twoSpaces"
    assert sanitizeName("a\\nb") == "aB"


def test_sanitize_name_drops_what_an_identifier_cannot_hold():
    assert sanitizeName('"quoted"') == "quoted"
    assert sanitizeName("x--y") == "xy"
    assert sanitizeName("it's") == "its"
    assert sanitizeName(".hidden") == "hidden"
    assert sanitizeName("") == ""


def test_sort_entities_orders_each_type_by_name():
    ir = _ir({"stock": [{"name": "b"}, {"name": "a"}, {"name": "c"}],
              "flow": [{"name": "z"}, {"name": "y"}]})

    entities = sortEntities(ir)["models"]["m"]["entities"]

    assert [e["name"] for e in entities["stock"]] == ["a", "b", "c"]
    assert [e["name"] for e in entities["flow"]] == ["y", "z"]
