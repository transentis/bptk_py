#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2026 transentis labs GmbH
# MIT License

"""The `py-sddsl` target: an XMILE model as SD DSL code.

The generator writes a module with a `Model` subclass that builds the model element by
element, the way a model written by hand in the SD DSL does, and a `simulation_model()`
that returns an instance. The elements carry the names the `py` target gives them, so a
scenario file reads either.

Each builtin is translated as "Builtins Side by Side" on the website shows it; a builtin
BPTK-Py does not have is refused with a message that names it and the variable, never
computed as something else.
"""

import keyword
import re


class GeneratorError(Exception):
    """A model the SD DSL cannot express, with the reason and where."""


def generate(IR):
    return _Generator(IR).module()


# ── Names ────────────────────────────────────────────────────────────────────

_RESERVED = set(keyword.kwlist) | {"self", "sd", "Model", "math", "simulation_model"}


def python_name(name):
    """The Python name of an element: a module's dot becomes a double underscore, anything
    else a Python name cannot hold an underscore, and a name Python or the module itself
    already uses gets an underscore after it."""
    result = re.sub(r"[^0-9a-zA-Z_]", "_", name.replace(".", "__"))
    if result[:1].isdigit():
        result = "_" + result
    return result + "_" if result in _RESERVED else result


# ── Expressions ──────────────────────────────────────────────────────────────

def _flat(args):
    """The arguments of a call as one list: the parser nests some of them in lists of
    their own and keeps the commas between them."""
    if isinstance(args, (list, tuple)):
        result = []
        for arg in args:
            if isinstance(arg, (list, tuple)):
                result += _flat(arg)
            elif not (isinstance(arg, str) and arg.strip() == ","):
                result.append(arg)
        return result
    return [args]


def _one(expression):
    """An expression the parser wrapped in a list of one."""
    while isinstance(expression, (list, tuple)) and len(expression) == 1:
        expression = expression[0]
    return expression


_BINARY = {"+": "+", "-": "-", "*": "*", "/": "/", "^": "**", "mod": "%",
           "=": "==", "<>": "!=", ">": ">", "<": "<", ">=": ">=", "<=": "<="}


# The kinds of element in the order the generated module lists them, each under a heading
_SECTIONS = (("stock", "Stocks"), ("conveyor", "Conveyors"), ("flow", "Flows"), ("biflow", "Biflows"),
             ("converter", "Converters"), ("constant", "Constants"))


def _layout_key(name):
    module, _, element = name.rpartition(".")
    return (module != "", module, python_name(element))


def _heading(title):
    """A heading of the generated module, ruled out to the width of its lines."""
    return ["# ── {} ".format(title).ljust(71, "─"), ""]


def _section(title, lines):
    """A subheading and its lines - nothing at all for a kind the model does not have."""
    return ["# " + title] + lines + [""] if lines else []


class _Generator:

    def __init__(self, IR):
        self.IR = IR
        self.entity = None
        self.cell = {}
        self.whole = False
        self.functions = {}
        self.warnings = set()
        self.by_name = {entity["name"]: entity for model in IR["models"].values()
                        for members in model["entities"].values() for entity in members if entity["name"]}
        # The flows a conveyor computes itself: its outflows and its leaks
        self.belt_flows = {flow for entity in self.by_name.values() if entity.get("conveyor")
                           for flow in entity["outflow"]}

    # ── the module ───────────────────────────────────────────────────────────

    def module(self):
        specs = self.IR["specs"]
        name = self.IR.get("name") or "model"
        entities = [(kind, entity) for model in self.IR["models"].values()
                    for kind, members in model["entities"].items() for entity in members
                    if kind in ("stock", "flow", "aux") and entity["name"]]
        for kind, entity in entities:
            score = _score(entity)
            if score:
                self.warn("'{}' is a {} score Stella computes for loop dominance analysis: it is left "
                          "out, the model runs without it".format(entity["name"], score))
        entities = [(kind, entity) for kind, entity in entities if not _score(entity)]
        self._check(entities)
        # Within a kind: the model's own elements first, then module by module, each by name
        entities = sorted(entities, key=lambda pair: _layout_key(pair[1]["name"]))
        # Each element's lines go under the heading of its kind; the tables an equation
        # reads get a heading of their own, ahead of every equation
        definitions = {element: [] for element, _ in _SECTIONS}
        equations = {element: [] for element, _ in _SECTIONS}
        tables = []
        for kind, entity in entities:
            self.entity = entity
            element = self._element_kind(kind, entity)
            for line in getattr(self, "_" + kind)(entity):
                (tables if line.startswith("self.points[") else equations[element]).append(line)
            definitions[element].append("{} = self.{}({!r})".format(python_name(entity["name"]), element,
                                                                     entity["name"]))
            if entity["dimensions"]:
                definitions[element].append(self._setup(entity))
                if entity["name"] in self.belt_flows:
                    # The conveyor computes these cells; setting the array up gave them 0
                    definitions[element] += ["{}.equation = None".format(self.cell_of(entity["name"], cell))
                                             for cell in self.cells(entity)]
        # The functions the equations call, then every element, so that an equation can
        # name any of them
        functions = [line for function, _ in self.functions.values() for line in function]
        body = _heading("Defining the elements")
        body += _section("Functions", functions)
        for element, title in _SECTIONS:
            body += _section(title, definitions[element])
        body += _heading("Setting the initial values and equations")
        body += _section("Graphical functions", tables)
        for element, title in _SECTIONS:
            body += _section(title, equations[element])
        body.pop()
        imports = sorted({module for _, modules in self.functions.values() for module in modules})
        out = ['"""{} - generated from XMILE by the BPTK-Py compiler, target py-sddsl."""'.format(name), ""]
        out += ["import {}".format(module) for module in imports] + ([""] if imports else [])
        out += ["from BPTK_Py import Model",
                "from BPTK_Py import sd_functions as sd",
                "",
                "",
                "class {}(Model):".format(self._class_name(name)),
                "",
                "    def __init__(self):",
                "        super().__init__(starttime={}, stoptime={}, dt={}, name={!r})".format(
                    float(specs["start"]), float(specs["stop"]), float(specs["dt"]), name),
                ""]
        out += ["        " + line if line else "" for line in body]
        out += ["", "", "def simulation_model():", "    return {}()".format(self._class_name(name)), ""]
        return "\n".join(out)

    def function(self, name, lines, imports=()):
        """A user-defined function the model needs, written once before the elements."""
        self.functions.setdefault(name, (lines, imports))
        return name

    @staticmethod
    def _class_name(name):
        words = re.split(r"[^0-9a-zA-Z]+", name)
        result = "".join(word[:1].upper() + word[1:] for word in words if word) or "XmileModel"
        return "_" + result if result[0].isdigit() else result

    def _check(self, entities):
        name = self.IR.get("name")
        method = self.IR["specs"].get("method") or "Euler"
        if method.lower() != "euler":
            raise GeneratorError("Model '{}' integrates with {}: BPTK-Py integrates with Euler "
                                 "only".format(name, method))
        if self.IR.get("imports"):
            raise GeneratorError("Model '{}' imports data from '{}': BPTK-Py reads no data "
                                 "imports".format(name, self.IR["imports"][0]))
        for model in self.IR["models"].values():
            for module in model["entities"].get("module", []):
                if module.get("url"):
                    raise GeneratorError("The module '{}' of model '{}' is kept in a file of its own, "
                                         "'{}': the compiler reads modules kept in the model "
                                         "file".format(module["name"], name, module["url"]))
        for kind, entity in entities:
            conveyor = entity.get("conveyor")
            if conveyor and conveyor["options"]:
                raise GeneratorError("The conveyor '{}' uses {}: BPTK-Py's conveyors have no {}".format(
                    entity["name"], ", ".join(conveyor["options"]), " and no ".join(conveyor["options"])))
            if entity.get("leak_zone"):
                raise GeneratorError("The leakage flow '{}' leaks from a zone of its conveyor: BPTK-Py's "
                                     "conveyors leak along the whole belt".format(entity["name"]))
            if len(entity["dimensions"]) > 2:
                raise GeneratorError(
                    "'{}' in model '{}' has {} dimensions: BPTK-Py takes vectors and matrices, no "
                    "more than 2".format(entity["name"], self.IR.get("name"), len(entity["dimensions"])))

    # ── arrays ───────────────────────────────────────────────────────────────

    def labels(self, dimension):
        return self.IR["dimensions"][dimension]["labels"]

    def named(self, dimensions):
        """Whether an array is a named one: a dimension without labels of its own counts
        from 1 in XMILE and from 0 in an unnamed SD DSL array, so the index is shifted;
        beside a dimension with labels it keeps its numbers as names."""
        return any(self.IR["dimensions"][dimension]["size"] is None for dimension in dimensions)

    def key(self, dimensions, position, label):
        if self.named(dimensions):
            return repr(label)
        return str(self.labels(dimensions[position]).index(label))

    def cell_of(self, name, labels):
        """A cell of an array, as Python: `stock[0][2]` or `stock['a']['b']`."""
        dimensions = self.by_name[name]["dimensions"]
        return python_name(name) + "".join("[{}]".format(self.key(dimensions, position, label))
                                           for position, label in enumerate(labels))

    def cells(self, entity):
        dimensions = entity["dimensions"]
        if len(dimensions) == 1:
            return [(label,) for label in self.labels(dimensions[0])]
        return [(row, column) for row in self.labels(dimensions[0]) for column in self.labels(dimensions[1])]

    def _setup(self, entity):
        name, dimensions = python_name(entity["name"]), entity["dimensions"]
        if len(dimensions) == 1:
            if self.named(dimensions):
                return "{}.setup_named_vector({})".format(name, {label: 0.0 for label in self.labels(dimensions[0])})
            return "{}.setup_vector({}, 0.0)".format(name, len(self.labels(dimensions[0])))
        rows, columns = self.labels(dimensions[0]), self.labels(dimensions[1])
        if self.named(dimensions):
            return "{}.setup_named_matrix({})".format(name, {row: {column: 0.0 for column in columns} for row in rows})
        return "{}.setup_matrix([{}, {}], 0.0)".format(name, len(rows), len(columns))

    def per_cell(self, entity, write):
        """The lines `write(target, equation)` gives for each cell of an arrayed entity, or
        for the entity itself; an equation per cell, or one for all of them."""
        if not entity["dimensions"]:
            self.cell = {}
            return write(python_name(entity["name"]), self._unwrapped(entity))
        lines = []
        equations = self._unwrapped_list(entity)
        given = [tuple(label) for label in entity["labels"]]
        for cell in self.cells(entity):
            self.cell = dict(zip(entity["dimensions"], cell))
            equation = equations[given.index(cell)] if given and cell in given else equations[0]
            lines += write(self.cell_of(entity["name"], cell), equation)
        self.cell = {}
        return lines

    @staticmethod
    def _unwrapped_list(entity):
        parsed = entity["equation_parsed"]
        if entity["non_negative"] and isinstance(parsed, dict) and parsed.get("name") == "max":
            parsed = parsed["args"][1]
        return parsed if isinstance(parsed, list) else [parsed]

    def _element_kind(self, kind, entity):
        if kind == "stock":
            return "conveyor" if entity.get("conveyor") else "stock"
        if kind == "flow":
            # A uniflow is non-negative in Stella and its equation is cut at 0 already; a
            # biflow runs either way, and a non-negative stock serves it before its outflows
            return "flow" if entity["non_negative"] or entity["name"] in self.belt_flows else "biflow"
        if self._is_constant(entity):
            return "constant"
        return "converter"

    def _is_constant(self, entity):
        if entity["name"] in self.IR.get("controls", {}):
            return True
        parsed = _one(entity["equation_parsed"])
        return not entity["gf"] and not entity.get("element_gfs") and isinstance(parsed, (int, float)) and not isinstance(parsed, bool)

    @staticmethod
    def _unwrapped(entity):
        # The reader cuts a non-negative entity's equation at 0 with MAX; a stock is held
        # at 0 by its flows instead, so its own equation is the one inside
        parsed = entity["equation_parsed"]
        if entity["non_negative"] and isinstance(parsed, dict) and parsed.get("name") == "max":
            return _one(parsed["args"][1])
        return _one(parsed)

    # ── entities ─────────────────────────────────────────────────────────────

    def _stock(self, entity):
        if entity.get("conveyor"):
            return self._conveyor(entity)

        def write(target, equation):
            lines = ["{}.initial_value = {}".format(target, self.render(equation))]
            if entity["inflow"]:
                lines.append("{}.inflows = [{}]".format(target, ", ".join(self.flow_of(flow) for flow in entity["inflow"])))
            if entity["outflow"]:
                lines.append("{}.outflows = [{}]".format(target, ", ".join(self.flow_of(flow) for flow in entity["outflow"])))
            if entity["non_negative"]:
                lines.append("{}.non_negative = True".format(target))
            return lines
        return self.per_cell(entity, write)

    def _conveyor(self, entity):
        conveyor = entity["conveyor"]
        leaks = [flow for flow in entity["outflow"] if self.by_name[flow].get("leak")]
        outflows = [flow for flow in entity["outflow"] if flow not in leaks]

        def write(target, equation):
            if conveyor.get("fill_parsed"):
                initial = "[{}]".format(", ".join(self.render(part) for part in conveyor["fill_parsed"]))
            elif _is_slice(equation):
                # A fill taken from an array: the numbers of its elements in order, as a list
                initial = "[{}]".format(", ".join(self.slice_numbers(equation)))
            else:
                initial = self.render(equation)
            lines = ["{}.transit_time = {}".format(target, self.render(conveyor["len_parsed"])),
                     "{}.initial_value = {}".format(target, initial)]
            if entity["inflow"]:
                lines.append("{}.inflows = [{}]".format(target, ", ".join(self.flow_of(flow) for flow in entity["inflow"])))
            if outflows:
                lines.append("{}.outflows = [{}]".format(target, ", ".join(self.flow_of(flow) for flow in outflows)))
            if leaks:
                # A leak's own equation is the share it takes
                fractions = []
                for flow in leaks:
                    leak = self.by_name[flow]
                    self.entity = leak
                    fractions.append("{}: {}".format(self.flow_of(flow), self.render(self._leak_share(leak))))
                self.entity = entity
                lines.append("{}.leaks = {{{}}}".format(target, ", ".join(fractions)))
            if conveyor["exponential_leak"]:
                lines.append("{}.exponential_leak = True".format(target))
            return lines
        return self.per_cell(entity, write)

    def _leak_share(self, leak):
        equations = self._unwrapped_list(leak)
        if leak["dimensions"] and self.cell:
            given = [tuple(label) for label in leak["labels"]]
            cell = tuple(self.cell[dimension] for dimension in leak["dimensions"])
            return equations[given.index(cell)] if given and cell in given else equations[0]
        return equations[0]

    def flow_of(self, name):
        # A flow of an arrayed stock is the flow's cell of the stock's cell
        if self.cell and self.by_name[name]["dimensions"]:
            return self.cell_of(name, [self.cell[dimension] for dimension in self.by_name[name]["dimensions"]])
        return python_name(name)

    def _flow(self, entity):
        if entity["name"] in self.belt_flows:
            # A conveyor computes its outflows and its leaks; Stella writes 0 or a leak's
            # share as their equation, which the conveyor takes over
            return []
        # A uniflow does not run backwards: Stella cuts it at 0. A flow can carry a graphical
        # function of its own, as an aux does
        if entity.get("element_gfs"):
            self.refuse("A graphical function per element of a flow")
        lines = []
        if entity["gf"]:
            lines.append("self.points[{!r}] = {}".format(entity["name"], [[float(x), float(y)] for x, y in entity["gf"]]))

        def write(target, equation):
            rendered = self.render(equation)
            if entity["gf"]:
                rendered = "sd.lookup({}, {!r}{})".format(rendered, entity["name"], self.kind(entity["name"]))
            if entity["non_negative"]:
                rendered = "sd.max(0.0, {})".format(rendered)
            return ["{}.equation = {}".format(target, rendered)]
        return lines + self.per_cell(entity, write)

    def _aux(self, entity):
        if entity["name"] in self.IR.get("controls", {}):
            # Stella runs with the value its control was left at, not with the equation
            return ["{}.equation = {}".format(python_name(entity["name"]),
                                              repr(float(self.IR["controls"][entity["name"]])))]
        if entity.get("element_gfs"):
            # A graphical function per element, each a table of its own under the cell's name
            given = [tuple(label) for label in entity["labels"]]
            def write(target, equation):
                points, kind = entity["element_gfs"][given.index(tuple(self.cell[d] for d in entity["dimensions"]))]
                table = "{}[{}]".format(entity["name"], ",".join(self.cell[d] for d in entity["dimensions"]))
                return ["self.points[{!r}] = {}".format(table, [[float(x), float(y)] for x, y in points]),
                        "{}.equation = sd.lookup({}, {!r}{})".format(
                            target, self.render(equation), table, "" if kind == "continuous" else ", kind={!r}".format(kind))]
            return self.per_cell(entity, write)
        if entity["gf"]:
            points = [[float(x), float(y)] for x, y in entity["gf"]]
            lines = ["self.points[{!r}] = {}".format(entity["name"], points)]
            return lines + self.per_cell(entity, lambda target, equation: [
                "{}.equation = sd.lookup({}, {!r}{})".format(target, self.render(equation), entity["name"],
                                                            self.kind(entity["name"]))])
        return self.per_cell(entity, lambda target, equation: [
            "{}.equation = {}".format(target, self.render(equation))])

    # ── expressions ──────────────────────────────────────────────────────────

    def refuse(self, what):
        raise GeneratorError("{} in '{}': BPTK-Py has no counterpart".format(what, self.entity["name"]))

    def render(self, expression):
        expression = _one(expression)
        if isinstance(expression, (int, float)):
            return repr(float(expression))
        if isinstance(expression, str):
            # A number the parser left as text: the placeholder "0" of a variable without an
            # equation, and the numbers of some arguments
            try:
                return repr(float(expression.strip() or "0"))
            except ValueError:
                self.refuse("'{}'".format(expression))
        if isinstance(expression, (list, tuple)):
            self.refuse("A list of expressions")
        kind = expression["type"]
        if kind == "identifier":
            return self._identifier(expression["name"])
        if kind == "array":
            return self._subscripted(expression)
        if kind == "operator":
            return self._operator(expression)
        if kind == "call":
            return self._call(expression)
        self.refuse("An expression of type '{}'".format(kind))

    def _identifier(self, name):
        if name.lower() in ("runcount", "sensiruncount"):
            return _BUILTINS[name.lower()](self, [])
        if name not in self.by_name and name not in self.IR["dimensions"]:
            raise GeneratorError("'{}' in '{}' is neither a variable of the model nor a builtin BPTK-Py "
                                 "has".format(name, self.entity["name"]))
        if name in self.cell:
            # A dimension used as a number: the position of the cell along it, from 1
            return repr(float(self.labels(name).index(self.cell[name]) + 1))
        entity = self.by_name.get(name)
        if entity is None or not entity["dimensions"]:
            return python_name(name)
        if self.whole:
            return python_name(name)
        if all(dimension in self.cell for dimension in entity["dimensions"]):
            return self.cell_of(name, [self.cell[dimension] for dimension in entity["dimensions"]])
        self.refuse("The array '{}' where one value is needed".format(name))

    def _subscripted(self, expression):
        # SELF[D - 1], a neighbouring element of the variable itself, is the variable's own
        # name by now: the plugin resolveSelf replaced it
        name = expression["name"]
        if name not in self.by_name:
            self.refuse("The array '{}', which the model does not have".format(name))
        dimensions = self.by_name[name]["dimensions"]
        indices = expression["args"]
        indices = [indices] if not isinstance(indices, list) else _flat(indices)
        if len(indices) != len(dimensions):
            self.refuse("'{}' with {} indices for {} dimensions".format(name, len(indices), len(dimensions)))
        parts = [self._index(dimensions, position, index) for position, index in enumerate(indices)]
        if any(kind == "beyond" for kind, _ in parts):
            return "0.0"
        if all(kind == "label" for kind, _ in parts):
            return self.cell_of(name, [label for _, label in parts])
        if all(kind in ("label", "computed") for kind, _ in parts):
            return self._chosen(name, dimensions, parts)
        # A slice, for an aggregation: every element of a dimension, or a range of them
        rendered = []
        for position, (kind, value) in enumerate(parts):
            if kind == "all":
                rendered.append(":")
            elif kind == "range":
                rendered.append("{}:{}".format(*(self.key(dimensions, position, label) for label in value)))
            else:
                rendered.append(self.key(dimensions, position, value))
        return "{}[{}]".format(python_name(name), ", ".join(rendered))

    def _index(self, dimensions, position, index):
        """One index of a subscript: ("label", label), ("all", None) or ("range", (first, last))."""
        labels = self.labels(dimensions[position])
        index = _one(index)
        if isinstance(index, str) and index.strip() == "*":
            return "all", None
        if isinstance(index, dict) and index["type"] == "range":
            first, last = (self._index(dimensions, position, bound)[1] for bound in _flat(index["args"]))
            return "range", (first, last)
        if isinstance(index, dict) and index["type"] == "label":
            name = index["name"]
            if name == dimensions[position] or name in self.IR["dimensions"]:
                if name in self.cell:
                    return "label", self.cell[name]
                return "all", None
            if name in labels:
                return "label", name
            if name in self.by_name:
                # A variable as the index: the cell is chosen while the model runs
                return "computed", self._identifier(name)
        number = self._static(index)
        if number is None:
            return "computed", self.render(index)
        if not (float(number).is_integer() and 1 <= number <= len(labels)):
            # Beyond the array: 0, as for an index computed while the model runs - mostly
            # in the branch of an IF the cell never takes, as SELF[D - 1] where D = 1
            return "beyond", None
        # A number on a dimension with labels is a position, as in XMILE
        return "label", labels[int(number) - 1]

    def _chosen(self, name, dimensions, parts):
        """A cell chosen while the model runs, by an index it computes: each possible cell
        under the condition that the index names it, 0 beyond the array."""
        for position, (kind, value) in enumerate(parts):
            if kind == "computed":
                choice = "0.0"
                labels = self.labels(dimensions[position])
                for number in range(len(labels), 0, -1):
                    fixed = parts[:position] + [("label", labels[number - 1])] + parts[position + 1:]
                    choice = "sd.If({} == {}, {}, {})".format(value, float(number), self._chosen(name, dimensions, fixed), choice)
                return choice
        return self.cell_of(name, [label for _, label in parts])

    def slice_cells(self, expression):
        """The cells a subscript with a range or `*` selects, in order."""
        expression = _one(expression)
        name, dimensions = expression["name"], self.by_name[expression["name"]]["dimensions"]
        indices = expression["args"] if isinstance(expression["args"], list) else [expression["args"]]
        choices = []
        for position, index in enumerate(_flat(indices)):
            kind, value = self._index(dimensions, position, index)
            labels = self.labels(dimensions[position])
            if kind == "all":
                choices.append(labels)
            elif kind == "range":
                choices.append(labels[labels.index(value[0]):labels.index(value[1]) + 1])
            else:
                choices.append([value])
        cells = [[label] for label in choices[0]]
        for choice in choices[1:]:
            cells = [cell + [label] for cell in cells for label in choice]
        return [self.cell_of(name, cell) for cell in cells]

    def slice_numbers(self, expression):
        """The numbers a slice of constants selects: a conveyor's fill is fixed when the run starts."""
        expression = _one(expression)
        source = self.by_name[expression["name"]]
        given = [tuple(label) for label in source["labels"]]
        equations = self._unwrapped_list(source)
        numbers = []
        for cell in self.slice_cells(expression):
            labels = tuple(next(label for label in self.cells(source) if self.cell_of(source["name"], label) == cell))
            value = _one(equations[given.index(labels)] if given and labels in given else equations[0])
            if not isinstance(value, (int, float)):
                self.refuse("A fill from '{}', whose elements are not all numbers,".format(source["name"]))
            numbers.append(repr(float(value)))
        return numbers

    def _static(self, expression):
        """The value of an index the model's structure fixes: numbers, and the position of
        the cell along a dimension, combined by arithmetic; None for anything else."""
        expression = _one(expression)
        if isinstance(expression, (int, float)) and not isinstance(expression, bool):
            return float(expression)
        if isinstance(expression, str):
            try:
                return float(expression)
            except ValueError:
                return None
        if not isinstance(expression, dict):
            return None
        name = expression.get("name")
        if expression["type"] in ("identifier", "label"):
            if name in self.cell:
                return float(self.labels(name).index(self.cell[name]) + 1)
            try:
                return float(name)
            except (TypeError, ValueError):
                return None
        if expression["type"] == "operator":
            args = [self._static(arg) for arg in _flat(expression["args"])]
            if name == "()" and args[0] is not None:
                return args[0]
            if len(args) == 2 and None not in args and name in ("+", "-", "*", "/"):
                left, right = args
                return {"+": left + right, "-": left - right, "*": left * right,
                        "/": left / right if right else None}[name]
        return None

    def array(self, expression):
        """An expression read as a whole array: the argument of an aggregation."""
        whole, self.whole = self.whole, True
        try:
            return self.render(expression)
        finally:
            self.whole = whole

    def _operator(self, expression):
        name = expression["name"].lower().replace(" ", "")
        args = _flat(expression["args"])
        if _mod_bound_differently(name, args):
            self.warn("'{}' uses MOD next to *, /, + or - without parentheses: the SD DSL reads it as "
                      "the XMILE standard does, with MOD on the level of * and /, while Stella puts MOD on "
                      "the level of + and -, so the two compute differently - parentheses make it "
                      "unambiguous".format(self.entity["name"]))
        if name == "()":
            return "({})".format(self.render(args[0]))
        if name == "-" and len(args) == 2 and isinstance(args[0], str) and args[0] == "":
            return "(-{})".format(self.render(args[1]))
        if name == "+" and len(args) == 2 and isinstance(args[0], str) and args[0] == "":
            return self.render(args[1])
        if name == "not":
            return "sd.Not({})".format(self.render(args[0]))
        if name in ("and", "or"):
            return "sd.{}({}, {})".format(name.capitalize(), self.render(args[0]), self.render(args[1]))
        if name in _BINARY:
            return "({} {} {})".format(self.render(args[0]), _BINARY[name], self.render(args[1]))
        self.refuse("The operator '{}'".format(expression["name"]))

    def _call(self, expression):
        name = expression["name"].lower()
        args = _flat(expression["args"])
        builtin = _BUILTINS.get(name)
        if builtin is None:
            self.refuse("The builtin {}".format(name.upper()))
        if name == "pulse" and len(args) < 3:
            self.warn("'{}' calls PULSE without an interval: the SD DSL pulses once, as the XMILE standard "
                      "says, while Stella pulses every DT".format(self.entity["name"]))
        if name == "delay" and len(args) > 1 and not self._fixed(args[1]):
            self.warn("'{}' calls DELAY with a delay time that can change: the SD DSL reads it at every step, "
                      "while Stella keeps its initial value".format(self.entity["name"]))
        return builtin(self, args)

    def _fixed(self, expression):
        """Whether an expression cannot change during the run: a number, or a constant."""
        expression = _one(expression)
        if isinstance(expression, (int, float)):
            return True
        if isinstance(expression, dict) and expression["type"] == "identifier":
            entity = self.by_name.get(expression["name"])
            return entity is not None and self._is_constant(entity)
        return False

    def warn(self, message):
        """A [WARN] where the transpiled model computes differently from Stella - once per message,
        however many cells of an array render the equation."""
        if message not in self.warnings:
            self.warnings.add(message)
            from BPTK_Py.logger import log
            log("[WARN] {}".format(message))

    # Helpers for the builtin table

    def table(self, expression):
        """The name of the graphical function a lookup reads."""
        expression = _one(expression)
        if isinstance(expression, dict) and expression["type"] == "identifier":
            return repr(expression["name"])
        self.refuse("A lookup of something other than a graphical function")

    def kind(self, table):
        """The type of a graphical function, as the lookups take it: nothing for a continuous one."""
        kind = self.by_name[table.strip("'\"")].get("gf_type", "continuous")
        return "" if kind == "continuous" else ", kind={!r}".format(kind)

    def optional(self, args, position):
        """An optional argument, None when it is left out or NAN."""
        if len(args) <= position:
            return None
        arg = _one(args[position])
        if isinstance(arg, dict) and arg["type"] == "call" and arg["name"].lower() == "nan":
            return None
        return self.render(arg)


def _score(entity):
    """'loop' or 'pathway' for a score of loop dominance analysis - marked so by Stella, or an
    equation that is nothing but LOOPSCORE or PATHSCORE - and None for anything else."""
    marked = {"loopscore": "loop", "pathscore": "pathway"}
    if entity.get("score"):
        return marked[entity["score"]]
    equation = _one(entity.get("equation_parsed"))
    if isinstance(equation, dict) and equation.get("type") == "call":
        return marked.get(equation["name"].lower())
    return None


def _mod_bound_differently(name, args):
    """Whether MOD stands where Stella and the standard bind it differently: Stella puts MOD on the
    level of + and -, the standard on the level of * and /. `a MOD b * c` and `a + b MOD c` then
    differ; `a * b MOD c` and `a MOD b + c` do not."""
    def is_mod(arg):
        arg = _one(arg)
        return isinstance(arg, dict) and arg["type"] == "operator" and arg["name"].lower() == "mod"
    if len(args) != 2:
        return False
    if name in ("*", "/"):
        return is_mod(args[0])
    if name in ("+", "-") and not (isinstance(args[0], str) and args[0] == ""):
        return is_mod(args[1])
    return False


def _is_slice(expression):
    """A subscript that selects several elements: an initial fill taken from an array."""
    expression = _one(expression)
    if not (isinstance(expression, dict) and expression["type"] == "array"):
        return False
    indices = expression["args"] if isinstance(expression["args"], list) else [expression["args"]]
    return any((isinstance(index, str) and index.strip() == "*") or
               (isinstance(index, dict) and index["type"] == "range") for index in _flat(indices))


def _call(function, model=False, count=None):
    """A builtin whose arguments go in order; `model` puts the model first."""
    def render(generator, args):
        rendered = [generator.render(arg) for arg in args]
        if model:
            rendered.insert(0, "self")
        return "sd.{}({})".format(function, ", ".join(rendered))
    return render


def _draw(function, parameters, model=False):
    """A random function: its parameters, then seed, minimum, maximum and sample."""
    def render(generator, args):
        rendered = ["self"] if model else []
        rendered += [generator.render(arg) for arg in args[:parameters]]
        for keyword_, position in (("seed", parameters), ("minimum", parameters + 1),
                                   ("maximum", parameters + 2), ("sample", parameters + 3)):
            value = generator.optional(args, position)
            if value is not None:
                rendered.append("{}={}".format(keyword_, value))
        return "sd.{}({})".format(function, ", ".join(rendered))
    return render


def _whole(generator, arg):
    """An argument the SD DSL takes as a Python int - an order, the digits of ROUND: a
    whole number, or a constant that holds one."""
    arg = _one(arg)
    if isinstance(arg, dict) and arg["type"] == "identifier" and arg["name"] in generator.by_name:
        arg = _one(generator.by_name[arg["name"]]["equation_parsed"])
    if isinstance(arg, (int, float)) and float(arg).is_integer():
        return str(int(arg))
    generator.refuse("A number of digits or an order that is not a whole number, nor a constant that is one")


def _if(generator, args):
    return "sd.If({}, {}, {})".format(*(generator.render(arg) for arg in args[:3]))


def _round(generator, args):
    digits = _whole(generator, args[1]) if len(args) > 1 else "0"
    return "sd.round({}, {})".format(generator.render(args[0]), digits)


def _lookup(generator, args):
    table = generator.table(args[0])
    return "sd.lookup({}, {}{})".format(generator.render(args[1]), table, generator.kind(table))


def _lookupinv(generator, args):
    table = generator.table(args[0])
    return "sd.lookupinv({}, {}{})".format(generator.render(args[1]), table, generator.kind(table))


def _lookuparea(generator, args):
    # One bound is the end: LOOKUPAREA(table, 4) is the area up to 4
    table = generator.table(args[0])
    if len(args) == 1:
        return "sd.lookuparea({}{})".format(table, generator.kind(table))
    if len(args) == 2:
        return "sd.lookuparea({}, to_x={}{})".format(table, generator.render(args[1]), generator.kind(table))
    return "sd.lookuparea({}, {}{})".format(table, ", ".join(generator.render(arg) for arg in args[1:3]),
                                            generator.kind(table))


def _lookup_statistic(function):
    # Stella writes the range as (to, from); the SD DSL as (from_x, to_x)
    def render(generator, args):
        table = generator.table(args[0])
        kind = generator.kind(table)
        if len(args) == 1:
            return "sd.{}({}{})".format(function, table, kind)
        if len(args) == 2:
            return "sd.{}({}, to_x={}{})".format(function, table, generator.render(args[1]), kind)
        return "sd.{}({}, {}, {}{})".format(function, table, generator.render(args[2]), generator.render(args[1]), kind)
    return render


def _with_order(function, before):
    """A smoothing or delay of order n: the order, a Python int, after `before` arguments."""
    def render(generator, args):
        rendered = ["self"] + [generator.render(arg) for arg in args[:before]]
        rendered.append(_whole(generator, args[before]))
        rendered += [generator.render(arg) for arg in args[before + 1:]]
        return "sd.{}({})".format(function, ", ".join(rendered))
    return render


def _ramp(generator, args):
    # Without a start time the ramp starts with the run
    rendered = [generator.render(arg) for arg in args]
    if len(rendered) == 1:
        rendered.append("sd.starttime(self)")
    return "sd.ramp({})".format(", ".join(rendered))


def _between_runs(builtin):
    # ENDVAL, RUNCOUNT and SENSIRUNCOUNT read what earlier runs left; a model of the SD DSL
    # is one run, and Python carries values from one to the next
    def refuse(generator, args):
        raise GeneratorError("{} in '{}' reads earlier runs: a BPTK-Py model is one run, and Python carries "
                             "values between runs - see \"Built from Other Functions\"".format(
                                 builtin, generator.entity["name"]))
    return refuse


def _clocktime(generator, args):
    name = generator.function("clocktime", [
        "clocktime = self.function(\"clocktime\", lambda model, t: float(int(time.time())))"], ("time",))
    return "{}()".format(name)


def _is_array(generator, expression):
    expression = _one(expression)
    if isinstance(expression, dict):
        if expression["type"] == "array":
            return True
        if expression["type"] == "identifier":
            entity = generator.by_name.get(expression["name"])
            return entity is not None and bool(entity["dimensions"])
        return any(_is_array(generator, arg) for arg in _flat(expression.get("args", [])))
    return False


def _aggregate(method, scalar=None):
    """An aggregation over an array; with several arguments that are no arrays, `scalar`. As
    in Stella, an array is the only argument: `*` and ranges select cells inside an
    aggregation of one argument, and SUM and PROD take nothing else."""
    builtin = method[len("arr_"):].upper()

    def render(generator, args):
        if len(args) == 1 and _is_array(generator, args[0]):
            return "{}.{}()".format(_parenthesised(generator.array(args[0])), method)
        if scalar is None:
            if len(args) > 1:
                generator.refuse("{} of more than one argument".format(builtin))
            generator.refuse("{} of something other than an array".format(builtin))
        if any(_is_slice(arg) for arg in args):
            generator.refuse("{} of an array beside other arguments".format(builtin))
        return scalar(generator, args)
    return render


def _parenthesised(rendered):
    return rendered if re.fullmatch(r"[0-9A-Za-z_]+(\[[^\]]*\])*", rendered) else "({})".format(rendered)


def _size(generator, args):
    # Every element the argument selects - a matrix counts its cells, where the SD DSL's
    # arr_size counts its rows. The count is fixed by the model's structure.
    if len(args) > 1:
        generator.refuse("SIZE of more than one argument")
    expression = _one(args[0])
    if isinstance(expression, dict) and expression["type"] == "identifier" and expression["name"] in generator.by_name:
        dimensions = generator.by_name[expression["name"]]["dimensions"]
        count = 1
        for dimension in dimensions:
            count *= len(generator.labels(dimension))
        return repr(float(count))
    if isinstance(expression, dict) and expression["type"] == "array" and expression["name"] in generator.by_name:
        dimensions = generator.by_name[expression["name"]]["dimensions"]
        indices = expression["args"]
        indices = [indices] if not isinstance(indices, list) else _flat(indices)
        count = 1
        for position, index in enumerate(indices):
            kind, value = generator._index(dimensions, position, index)
            if kind == "all":
                count *= len(generator.labels(dimensions[position]))
            elif kind == "range":
                labels = generator.labels(dimensions[position])
                count *= labels.index(value[1]) - labels.index(value[0]) + 1
        return repr(float(count))
    generator.refuse("SIZE of something other than an array")


def _mean_of(generator, args):
    return "(({}) / {})".format(" + ".join(generator.render(arg) for arg in args), float(len(args)))


def _rank(generator, args):
    rendered = [generator.render(args[1])]
    if len(args) > 2:
        rendered.append(generator.array(args[2]))
    return "{}.arr_rank({})".format(_parenthesised(generator.array(args[0])), ", ".join(rendered))


def _interpolate(generator, args):
    return "{}.arr_interpolate({})".format(_parenthesised(generator.array(args[0])),
                                           ", ".join(generator.render(arg) for arg in args[1:]))


def _percentile(generator, args):
    rendered = [generator.render(args[1])]
    if len(args) > 2:
        rendered.append(generator.render(args[2]))
    if len(args) > 3:
        rendered.append("weights={}".format(generator.array(args[3])))
    return "{}.arr_percentile({})".format(_parenthesised(generator.array(args[0])), ", ".join(rendered))


def _derivn(generator, args):
    return "sd.derivn(self, {}, {})".format(generator.render(args[0]), _whole(generator, args[1]))


def _lookuprandom(generator, args):
    rendered = [generator.table(args[0])]
    for keyword_, position in (("seed", 1), ("minimum", 2), ("maximum", 3), ("sample", 4)):
        value = generator.optional(args, position)
        if value is not None:
            rendered.append("{}={}".format(keyword_, value))
    return "sd.lookuprandom({})".format(", ".join(rendered))


_BUILTINS = {
    # Time
    "time": lambda generator, args: "sd.time()",
    "dt": lambda generator, args: "sd.dt(self)",
    "starttime": lambda generator, args: "sd.starttime(self)",
    "stoptime": lambda generator, args: "sd.stoptime(self)",
    # Mathematics
    "abs": _call("abs"), "sqrt": _call("sqrt"), "exp": _call("exp"), "ln": _call("ln"),
    "log10": _call("log10"), "sin": _call("sin"), "cos": _call("cos"), "tan": _call("tan"),
    "arcsin": _call("arcsin"), "arccos": _call("arccos"), "arctan": _call("arctan"),
    "int": _call("floor"), "round": _round,
    "max": _aggregate("arr_max", _call("max")), "min": _aggregate("arr_min", _call("min")),
    "safediv": _call("safediv"), "rootn": _call("rootn"), "percent": _call("percent"),
    "pi": lambda generator, args: "sd.pi()", "inf": lambda generator, args: "sd.Inf()",
    "nan": lambda generator, args: "sd.nan()",
    "combinations": _call("combinations"), "permutations": _call("permutations"),
    "factorial": _call("factorial"), "gammaln": _call("gammaln"),
    "cgrowth": _call("cgrowth", model=True), "counter": _call("counter", model=True),
    "isnan": _call("isnan"), "rework": _call("rework"), "expbound": _call("expbound"),
    "logisticbound": _call("logisticbound"), "maxsoft": _call("maxsoft"), "minsoft": _call("minsoft"),
    # Arrays
    "sum": _aggregate("arr_sum"), "prod": _aggregate("arr_prod"), "mean": _aggregate("arr_mean", _mean_of),
    "stddev": _aggregate("arr_stddev"), "size": _size, "rank": _rank,
    "interpolate": _interpolate, "percentile": _percentile,
    # Conditions
    "if": _if,
    # Test inputs
    "step": _call("step"), "ramp": _ramp, "pulse": _call("pulse", model=True),
    "sinwave": _call("sinwave"), "coswave": _call("coswave"),
    # Delays and smoothing
    "delay": _call("delay", model=True), "delay1": _call("delay1", model=True),
    "delay3": _call("delay3", model=True), "delayn": _with_order("delayn", 2),
    "smth1": _call("smooth", model=True), "smth3": _call("smooth3", model=True),
    "smthn": _with_order("smoothn", 2), "trend": _call("trend", model=True),
    "forcst": _call("forecast", model=True),
    # Conveyors
    "agecount": _call("agecount"),
    # The past of a variable
    "init": _call("init", model=True), "previous": _call("previous", model=True),
    "history": _call("history", model=True), "derivn": _derivn,
    "endval": _between_runs("ENDVAL"), "runcount": _between_runs("RUNCOUNT"),
    "sensiruncount": _between_runs("SENSIRUNCOUNT"),
    "clocktime": _clocktime,
    "runcum": _call("runcum", model=True), "runmax": _call("runmax", model=True),
    "runmin": _call("runmin", model=True), "runmean": _call("runmean", model=True),
    "runcumtarget": _call("runcumtarget", model=True),
    # Finance
    "npv": _call("npv", model=True), "irr": _call("irr", model=True),
    "pmt": _call("pmt"), "fv": _call("fv"), "pv": _call("pv"),
    # Graphical functions
    "lookup": _lookup, "lookupinv": _lookupinv, "lookuparea": _lookuparea,
    "lookupmax": _lookup_statistic("lookupmax"), "lookupmin": _lookup_statistic("lookupmin"),
    "lookupmean": _lookup_statistic("lookupmean"), "lookuprandom": _lookuprandom,
    # Random numbers
    "random": lambda generator, args: "sd.random({})".format(", ".join(generator.render(arg) for arg in args)),
    "uniform": _draw("uniform", 2), "normal": _draw("normal", 2), "lognormal": _draw("lognormal", 2),
    "logistic": _draw("logistic", 2), "beta": _draw("beta", 2), "binomial": _draw("binomial", 2),
    "negbinomial": _draw("negbinomial", 2), "exprnd": _draw("exprnd", 1), "gamma": _draw("gamma", 2),
    "geometric": _draw("geometric", 1), "poisson": _draw("poisson", 1), "pareto": _draw("pareto", 2),
    "triangular": _draw("triangular", 3), "weibull": _draw("weibull", 2), "montecarlo": _draw("montecarlo", 1),
    "normalpink": _draw("normalpink", 3, model=True),
    "invnorm": _call("invnorm"), "normalcdf": _call("normalcdf"),
}
