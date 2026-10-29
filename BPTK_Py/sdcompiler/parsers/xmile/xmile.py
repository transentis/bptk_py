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

import xml.etree.ElementTree as ElementTree
from copy import deepcopy

try: # Relative imports in case you are using me inside BPTK or any other library
    from ...parsers.smile.parser import parse
    from ...plugins import sanitizeName
    from ...plugins import makeExpressionAbsolute
except: # Absolute imports, in case you are using me standalone
    from parsers.smile.parser import parse
    from plugins import sanitizeName, makeExpressionAbsolute


class _Document:
    """An XMILE file read with ElementTree. Tags are named as the file spells them: an
    element of the default namespace by its name, one of another namespace with the prefix
    the file gives it - `isee:dependencies`."""

    def __init__(self, filename):
        self.prefixes = {}
        for _, (prefix, uri) in ElementTree.iterparse(filename, events=["start-ns"]):
            self.prefixes.setdefault(uri, prefix)
        self.root = ElementTree.parse(filename).getroot()

    def tag(self, element):
        if not element.tag.startswith("{"):
            return element.tag
        uri, name = element.tag[1:].split("}", 1)
        prefix = self.prefixes.get(uri, "")
        return prefix + ":" + name if prefix else name

    def children(self, element, tag):
        return [child for child in element if self.tag(child) == tag]

    def child(self, element, tag):
        children = self.children(element, tag)
        return children[0] if children else None

    def text(self, element, tag):
        """The text of the first child called `tag`, without surrounding whitespace; None
        when there is no such child or it is empty."""
        child = self.child(element, tag)
        if child is None or child.text is None or not child.text.strip():
            return None
        return child.text.strip()


def extract_connects(model_name, connects):
    """
    Extract Connects between elements
    :param model_name:
    :param connects: the `@to` and `@from` of each connect element
    :return:
    """
    def handle_connect(connect):
        to_ = make_qualified_name(model_name,connect["@to"])
        from_ = make_qualified_name(model_name, connect["@from"])
        return {sanitizeName(to_.lower()): sanitizeName(from_.lower())}

    def make_qualified_name(model_name,element_name):
        # A leading dot names a variable of the main model, from whichever module; a name
        # without one is a variable of the model the connect is written in
        if element_name[0] == ".":
            return element_name[1:]
        if "." in element_name or model_name == "":
            return element_name
        return model_name + "." + element_name

    result = {}
    for connect in connects:
        result.update(handle_connect(connect))
    return result


def make_name_absolute(model_name, name):
    """
    Make an element's name absolute to make it unique. Eg "stock1" in model "model" --> "model.stock1"
    :param model_name: Name of model
    :param name: Element name
    :return:
    """
    seperator = "."
    if "." not in name:
        return model_name + seperator + name
    else:
        return name

def read_gf(document, gf_):
    """The points of a graphical function and its type; no points where there is none."""
    if gf_ is None:
        return [], "continuous"
    ypoints = [float(x) for x in document.text(gf_, "ypts").split(",")]
    xpts = document.text(gf_, "xpts")
    if xpts is None:
        xscale = document.child(gf_, "xscale")
        minX = float(xscale.get("min"))
        maxX = float(xscale.get("max"))
        xpoints = [minX + k * (maxX - minX) / (len(ypoints) - 1) for k in range(0, len(ypoints))]
    else:
        xpoints = [float(x) for x in xpts.split(",")]
    # XMILE's type of graphical function: continuous unless it says otherwise
    return list(zip(xpoints, ypoints)), gf_.get("type", "continuous")


def parse_entity(document, entity, model_name):
    """
    Parse one entity
    :param document: The XMILE document
    :param entity: Entity (XML element)
    :param model_name: Name of model the entity belongs to
    :return:
    """
    event_poster = []
    gf, gf_type = read_gf(document, document.child(entity, "gf"))

    non_negative = document.child(entity, "non_negative") is not None

    # A conveyor: its transit time, its kind of leak and the options it uses besides
    conveyor = None
    conveyor_ = document.child(entity, "conveyor")
    if conveyor_ is not None:
        conveyor = {"len": document.text(conveyor_, "len"),
                    "exponential_leak": conveyor_.get("exponential_leak", "false").lower() == "true",
                    "options": [document.tag(child) for child in conveyor_ if document.tag(child) != "len"]}
    # A leakage flow of a conveyor, and the part of the belt it leaks from
    leak = document.child(entity, "leak") is not None
    leak_zone = entity.get("leak_start") is not None or entity.get("leak_end") is not None
    doc = document.text(entity, "doc")
    # A loop or pathway score Stella computes for loop dominance analysis
    score = next((kind for kind in ("loopscore", "pathscore")
                  if document.child(entity, "isee:" + kind) is not None), None)

    inflows = [sanitizeName(make_name_absolute(model_name, flow.text.strip()))
               for flow in document.children(entity, "inflow")]
    outflows = [sanitizeName(make_name_absolute(model_name, flow.text.strip()))
                for flow in document.children(entity, "outflow")]

    name = entity.get("name")
    if name is not None and not "." in name:
        name = model_name + "." + name.lower()

    connects = extract_connects(model_name, [{"@to": connect.get("to"), "@from": connect.get("from")}
                                             for connect in document.children(entity, "connect")])
    name = "" if name is None else sanitizeName(name)

    access = entity.get("access", "")
    # A module kept in a file of its own names the file
    url = entity.get("url")
    equation = [] if document.child(entity, "eqn") is None else [document.text(entity, "eqn")]

    dimensions = []
    labels = []

    dimensions_ = document.child(entity, "dimensions")
    elements = document.children(entity, "element")
    if dimensions_ is not None: # If entity is arrayed

        dims = document.children(dimensions_, "dim")
        if dims:
            for elem in elements:
                label = tuple([sanitizeName(x) for x in elem.get("subscript").split(",")])
                labels += [label]

        for dim in dims:
            dimensions+= [sanitizeName(dim.get("name"))]

    ## Parse Equations again if we find out there are arrayed Equations!
    element_gfs = []
    if len(labels) > 0: # If the entity has dimension labels
        equation = [document.text(elem, "eqn") for elem in elements]
        # A graphical function per element
        element_gfs = [read_gf(document, document.child(elem, "gf")) for elem in elements]
        if not any(points for points, _ in element_gfs):
            element_gfs = []

    return {"name": name,
        "access": access,
        "equation": equation,
        "connects": connects,
        "non_negative": non_negative,
        "inflow": inflows,
        "outflow": outflows,
        "doc": doc,
        "gf": gf,
        "gf_type": gf_type,
        "element_gfs": element_gfs,
        "conveyor": conveyor,
        "leak": leak,
        "leak_zone": leak_zone,
        "event_poster": event_poster,
        "dimensions": dimensions,
        "labels":labels,
        "url": url,
        "score": score,
            }


def _source(assignments, name):
    """The variable a chain of module connects ends at."""
    seen = {name}
    while name in assignments and assignments[name] not in seen:
        name = assignments[name]
        seen.add(name)
    return name


def _control_name(name):
    """A control's variable, spelt as the entities are: `Module.Variable_Name`, or the name
    alone for one of the main model."""
    module, _, variable = name.rpartition(".")
    return sanitizeName(module + "." + variable.lower())


def _top_level_parts(equation):
    """An equation cut at the commas outside parentheses and brackets: a conveyor's initial
    fill, `5, 10, 15`, is a list of what is on its belt, the first to leave first."""
    parts, depth, current = [], 0, ""
    for character in equation:
        if character in "([":
            depth += 1
        elif character in ")]":
            depth -= 1
        if character == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += character
    return parts + [current]


def parse_xmile(filename):
    """
    Main method, opens the XMILE file and extracts the model structure
    :param filename: Filename of XMILE file (*.stmx, *.itmx)
    :return: Dictionary containing structure in a Python-processable data structure. Including Abstract Syntax trees for all equations (Excluding extensive pre-processing!)
    """
    document = _Document(filename)
    root = document.root

    ## Main Specs
    sim_specs = document.child(root, "sim_specs")
    header = document.child(root, "header")

    ## ensure starttime and stoptime are floats
    specs = {}
    for key in ("start", "stop"):
        value = document.text(sim_specs, key)
        specs[key] = value + ".0" if '.' not in value else value

    ## Delta T (DT)
    dt = document.child(sim_specs, "dt")
    if dt is not None:
        specs["dt"] = dt.text.strip()
        if dt.get("reciprocal", "").lower() == 'true': ## Reciprocal values
            specs["dt"] = 1 / int(specs["dt"])

    specs["method"] = sim_specs.get("method")
    specs["units"] = sim_specs.get("time_units")

    IR = { # Empty Intermediate Representation. This is the main representation that we fill up in the further parsing steps
        "dimensions": {},
        "models": {},
        "specs": specs,
        "name": document.text(header, "name"), "assignments": {},
        # Data imported from a file: the model keeps only the link to it. An export sits
        # beside the imports and reads nothing
        "imports": [element.get("resource") for data in document.children(root, "data")
                    for element in document.children(data, "import")],
        # The value an interface control was left at, by the variable it sets: Stella runs
        # with it in place of the variable's equation
        "controls": {_control_name(control.get("name")): control.get("value")
                     for controls in document.children(root, "isee:controls")
                     for control in document.children(controls, "isee:control")},
    }

    ## DIMENSIONS
    dimensions = document.child(root, "dimensions")
    for dim in [] if dimensions is None else document.children(dimensions, "dim"):
        size = None if dim.get("size") is None else int(dim.get("size"))
        name = sanitizeName(dim.get("name"))
        labels = None

        if not size:
            labels = [sanitizeName(elem.get("name")) for elem in document.children(dim, "elem")]
        else:
            labels = [str((i+1)) for i in range(0,size)]

        IR["dimensions"][name] = {
            "size": size,
            "name": name, "labels": labels, "variables": []}


    ## ENTITIES
    # What the connects of modules feed: another name for each variable's source
    aliases = {}
    for model in document.children(root, "model"):
        name = model.get("name", "")
        variables = document.child(model, "variables")
        entities = {}

        # One list per kind of entity, the kinds in the order they first appear; an empty
        # element, such as Stella's `<isee:dependencies/>`, has a kind but no entity
        for element in [] if variables is None else variables:
            kind = entities.setdefault(document.tag(element), [])
            if element.attrib or len(element) or (element.text or "").strip():
                kind.append(parse_entity(document, element, name))

        # Each dimension knows the arrayed variables that use it
        for entity_type in entities:
            if entity_type.lower() in ["stock","aux","array","flow"]:
                for entity in entities[entity_type]:
                    for dim in entity["dimensions"]:
                        IR["dimensions"][dim]["variables"] += [{"model":name,"name":entity["name"]}]

        IR["models"][name] = {"name": name, "entities": entities}

        for key, value in entities.items():
            for elem in value:
                IR["assignments"].update(elem["connects"])
                if key == "module":
                    aliases.update(elem["connects"])

    ### PARSE EQUATIONS
    for name, model in IR["models"].items():
        for entity_type, entity in model["entities"].items():
            for elem in entity:
                fill = elem.get("conveyor") and len(elem["equation"]) == 1 and \
                    len(_top_level_parts(elem["equation"][0])) > 1
                if fill:
                    elem["conveyor"]["fill_parsed"] = [
                        makeExpressionAbsolute(name, parse(part), connects=IR["assignments"], entity=entity,
                                               dimensions=IR["dimensions"])
                        for part in _top_level_parts(elem["equation"][0])]
                    elem["equation"] = ["0"]
                elem["equation_parsed"] = [makeExpressionAbsolute(name,parse(x),connects=IR["assignments"],entity=entity,dimensions=IR["dimensions"]) for x in elem["equation"]]
                if elem.get("conveyor") and elem["conveyor"]["len"] is not None:
                    elem["conveyor"]["len_parsed"] = makeExpressionAbsolute(
                        name, parse(elem["conveyor"]["len"]), connects=IR["assignments"], entity=entity,
                        dimensions=IR["dimensions"])

                # A variable a module connect feeds is another name for its source: it takes
                # the source's values, not the placeholder equation the file gives it
                if entity_type == "aux" and elem["name"] in aliases and len(elem["equation"]) <= 1:
                    elem["equation_parsed"] = [{"name": _source(aliases, elem["name"]), "type": "identifier"}]

                # Handle Non-Negative stocks. equation_parsed is always a list (built by
                # the comprehension above), so the value is never a bare float here —
                # wrap it in a max(0, equation) call.
                if elem["non_negative"]:
                    elem["equation_parsed"] = {"name": 'max', "type": 'call',
                                               "args": [0, deepcopy(elem["equation_parsed"])]}

    return IR
