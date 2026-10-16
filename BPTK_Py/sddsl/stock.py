#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License


from contextlib import contextmanager

from .element import Element
from .element import ElementError
from .operators import Operator


# A stock whose equation is built from its flow lists assigns that equation itself, and
# through it the equations of its cells. Those assignments are the lists at work, not a
# modeller replacing them, so the equation setter leaves the lists alone while one runs.
_from_flow_lists_depth = 0


@contextmanager
def _from_flow_lists():
    global _from_flow_lists_depth
    _from_flow_lists_depth += 1
    try:
        yield
    finally:
        _from_flow_lists_depth -= 1


def _leaves(element, path=()):
    """Every scalar cell of an element, keyed by its position. A scalar is its own cell."""
    if element._elements.vector_size() == 0:
        return {path: element}
    cells = {}
    for key in element._elements.equations:
        cells.update(_leaves(element[key], path + (key,)))
    return cells


def _depends_on(expression, names, seen=None):
    """Whether an expression reads an element named in `names` within the same timestep.

    By name, because a scenario runs a clone of the model whose equations still hold the
    original's elements. A stock ends the search, because it reads its flows one step
    back. Every operand of an operator is followed, including the input of a function that
    reads the past, so the answer errs on the side of a dependency.
    """
    seen = set() if seen is None else seen
    if isinstance(expression, Element):
        if expression.name in names:
            return True
        if expression.type == "Stock" or id(expression) in seen:
            return False
        seen.add(id(expression))
        return _depends_on(expression.equation, names, seen)
    if isinstance(expression, Operator):
        return any(_depends_on(operand, names, seen) for operand in expression.operands())
    if isinstance(expression, (list, tuple)):
        return any(_depends_on(item, names, seen) for item in expression)
    return False


class Stock(Element):
    """Stock in a SD DSL model.
    """

    type = "Stock"

    def __init__(self, model, name):
        super(Stock, self).__init__(model, name)
        self.__initial_value = 0.0
        self._inflows = []
        self._outflows = []
        self._non_negative = False
        self._written_directly = False
        self._constrained = []

    def default_function_string(self):
        return "lambda model, t : ( (0) if (t <= model.starttime) else (model.memoize('{}',t-model.dt)) )".format(self.name)

    @property
    def initial_value(self):
        return self.__initial_value

    @initial_value.setter
    def initial_value(self, initial_value):
        # A number, an element or an expression built from them. The engines have always
        # treated an initial value as a full expression - the JSON format serializes it
        # the way it serializes an equation, and the Python side renders it with `str()`,
        # which is the element's or the operator's term - so the setter used to be
        # narrower than either of them. A bool is an int in Python and is refused
        # deliberately: `True` as a starting level is a slip, not an intention.
        acceptable = (
            isinstance(initial_value, (int, float)) and not isinstance(initial_value, bool)
            or isinstance(initial_value, (Element, Operator))
        )
        if not acceptable:
            raise ElementError(
                "The initial value of stock '{}' is a {}. It has to be a number, another "
                "element - a constant or a converter - or an expression built from them. "
                "A value that has to be computed, by a user-defined function for "
                "instance, belongs in a converter that the stock then starts "
                "from.".format(self.name, type(initial_value).__name__))

        self.__initial_value = initial_value
        self.build_function_string()
        self.generate_function()

    def add_arr_equation(self, name, value):
        s = self.model.stock(self.name + "[" + name + "]")
        s.equation = value

    def add_arr_empty(self, name):
        return self.model.stock(self.name + "[" + name + "]")

    def get_arr_equation(self, name):
        return self.model.stocks[self.name + "[" + name + "]"]

    @property
    def equation(self):
        return super().equation

    @equation.setter
    def equation(self, equation):
        if _from_flow_lists_depth == 0:
            if self._non_negative:
                raise ElementError(
                    "'{}' is a non-negative stock, so its equation comes from its flow "
                    "lists: set {}.inflows and {}.outflows instead, or set non_negative "
                    "to False first.".format(self.name, self.name, self.name))
            self._release_outflows()
            self._inflows = []
            self._outflows = []
            self._written_directly = equation is not None
        self._set_equation(equation)

    def _set_equation(self, equation):
        if not self._handle_arrayed(equation):
            self._equation = equation
        self.model.reset_cache()
        self.build_function_string()
        self.generate_function()

    def build_function_string(self):
        start_string = "lambda model, t : ( ("
        start_string += str(self.__initial_value) + \
            ") if (t <= model.starttime) else (model.memoize('{}',t-model.dt))".format(self.name)

        if self.equation is not None:
            start_string += "+ model.dt*("
            if isinstance(self._equation, (float, int)):
                self._function_string = start_string + \
                    str(self._equation) + ") )"
            else:
                self._function_string = start_string + \
                    self._equation.term("t-model.dt") + ") )"
        else:
            self._function_string = start_string + ")"

    @property
    def inflows(self):
        """The flows into the stock, as a list. Setting it builds the equation."""
        return list(self._inflows)

    @inflows.setter
    def inflows(self, flows):
        self._set_flow_lists(flows, self._outflows)

    @property
    def outflows(self):
        """The flows out of the stock, as a list, in the order of their priority."""
        return list(self._outflows)

    @outflows.setter
    def outflows(self, flows):
        self._set_flow_lists(self._inflows, flows)

    @property
    def non_negative(self):
        """Whether the outflows are cut back so that the stock stops at zero."""
        return self._non_negative

    @non_negative.setter
    def non_negative(self, non_negative):
        if not isinstance(non_negative, bool):
            raise ElementError(
                "non_negative of stock '{}' is a {}. It has to be True or False.".format(
                    self.name, type(non_negative).__name__))
        if non_negative and self._written_directly:
            raise ElementError(
                "'{}' has an equation that was written directly. A non-negative stock "
                "needs to know which flows leave it and in which order: set {}.inflows "
                "and {}.outflows instead of the equation.".format(self.name, self.name, self.name))
        before = self._non_negative
        self._non_negative = non_negative
        try:
            self._constrain_outflows()
        except ElementError:
            self._non_negative = before
            self._constrain_outflows()
            raise

    def _set_flow_lists(self, inflows, outflows):
        inflows = list(inflows)
        outflows = list(outflows)
        for flow in inflows + outflows:
            if not isinstance(flow, Element) or flow.type not in ("Flow", "Biflow"):
                raise ElementError(
                    "The flows of stock '{}' have to be flows or biflows of the model; "
                    "one of them is a {}.".format(self.name, getattr(flow, "type", type(flow).__name__)))
        for flow in outflows:
            owner = getattr(flow, "_drained_by", None)
            if owner is not None and owner is not self:
                raise ElementError(
                    "'{}' is already an outflow of stock '{}'. A flow leaves one stock "
                    "only.".format(flow.name, owner.name))

        before = (self._inflows, self._outflows, self._written_directly, self._equation)
        try:
            self._assign_flow_lists(inflows, outflows)
        except ElementError:
            # Back to what the stock was: its old lists, or the equation written directly.
            old_inflows, old_outflows, written_directly, equation = before
            if old_inflows or old_outflows:
                self._assign_flow_lists(old_inflows, old_outflows)
            else:
                self._release_outflows()
                self._inflows, self._outflows = [], []
                with _from_flow_lists():
                    self._set_equation(equation)
                self._written_directly = written_directly
            raise

    def _assign_flow_lists(self, inflows, outflows):
        self._release_outflows()
        self._inflows = inflows
        self._outflows = outflows
        self._written_directly = False
        for flow in outflows:
            flow._drained_by = self

        equation = None
        for flow in inflows:
            equation = flow if equation is None else equation + flow
        for flow in outflows:
            equation = -flow if equation is None else equation - flow
        with _from_flow_lists():
            self._set_equation(equation)
        self._constrain_outflows()

    def _release_outflows(self):
        for flow in self._outflows:
            flow._drained_by = None
        self._unconstrain()

    def _unconstrain(self):
        for flow in self._constrained:
            flow._constraint = None
            flow.build_function_string()
            flow.generate_function()
        self._constrained = []

    def _constrain_outflows(self):
        """Hands every outflow of every cell to the cell that cuts it back.

        A cell keeps the names of its own inflows and outflows; which of them it may count
        is decided when the model runs, since a flow's equation can still change after
        the lists are set.
        """
        self._unconstrain()
        cells = _leaves(self)
        for cell in cells.values():
            cell._non_negative = self._non_negative
            cell._cut = None
        if not self._non_negative:
            return

        def cell_of(flow, path, is_outflow):
            if flow._elements.vector_size() == 0:
                if is_outflow and len(cells) > 1:
                    raise ElementError(
                        "'{}' is arrayed and its outflow '{}' is not. An outflow drains one "
                        "cell only; give it the stock's shape.".format(self.name, flow.name))
                return flow
            # The equation built from the lists has already matched the shapes.
            return _leaves(flow)[path]

        for path, cell in cells.items():
            outflows = [cell_of(flow, path, True) for flow in self._outflows]
            inflows = [cell_of(flow, path, False) for flow in self._inflows]
            cut = outflows + [flow for flow in inflows if flow.type == "Biflow"]
            for flow in cut:
                if getattr(flow, "_constraint", None) is not None:
                    raise ElementError(
                        "'{}' is already cut back by the non-negative stock '{}'. A flow "
                        "can be cut back by one stock only.".format(flow.name, flow._constraint))
            cell._cut = ([flow.name for flow in inflows], [flow.name for flow in outflows])
            cell._cut_plan_version = None
            cell._check_cut()
            for flow in cut:
                flow._constraint = cell.name
                flow.build_function_string()
                flow.generate_function()
                self._constrained.append(flow)

    def _check_cut(self):
        """What flows in, for this cell, after checking the order its flows are served in.

        Returns (name, how) for every flow that counts towards what may leave: a flow with
        its value, a biflow with what it brings in. Worked out again whenever the model
        has changed since the last time.
        """
        version = self.model._structure_version
        if getattr(self, "_cut_plan_version", None) == version:
            return self._cut_plan
        inflows, outflows = self._cut

        def element(name):
            return self.model.flows.get(name) or self.model.biflows[name]

        # The order the cell serves what leaves it: the outflows, then the biflows among
        # the inflows, for when they run backwards.
        served = outflows + [name for name in inflows if name in self.model.biflows]
        for position, name in enumerate(served):
            for later in served[position + 1:]:
                if _depends_on(element(name).equation, {later}):
                    raise ElementError(
                        "'{}' comes before '{}' in the outflows of '{}', but depends on "
                        "it. An outflow that depends on another one takes the lower "
                        "priority: put it later in the list. A biflow among the inflows "
                        "comes after every outflow.".format(name, later, self.name))
        # A flow that depends on an outflow of the same stock cannot count towards what
        # that outflow may take - it would wait for itself. As in Stella, it is left out,
        # and only the stock's content is available.
        counted = []
        for name in inflows:
            if not _depends_on(element(name), set(outflows)):
                counted.append((name, "flow" if name in self.model.flows else "in"))
        for name in outflows:
            if name in self.model.biflows and not _depends_on(element(name).equation, set(outflows)):
                counted.append((name, "out"))
        self._cut_plan = counted
        self._cut_plan_version = version
        return self._cut_plan

    def _cut_back(self, flow, wanted, t):
        """What `flow` may move at `t`.

        A flow that brings material in moves what it wants. One that takes material out
        takes at most what is left once the flows served before it have had theirs.
        """
        inflows, outflows = self._cut
        is_outflow = flow in outflows
        if (wanted <= 0) if is_outflow else (wanted >= 0):
            return wanted
        model = self.model
        available = model.memoize(self.name, t) / model.dt
        for name, how in self._check_cut():
            if how == "flow":
                available += model.memoize(name, t)
            else:
                brought = model.biflows[name].wanted(t)
                available += max(0, brought if how == "in" else -brought)
        for earlier in outflows:
            if earlier == flow:
                return max(0, min(wanted, available))
            available -= max(0, model.memoize(earlier, t))
        for earlier in inflows:
            if earlier == flow:
                break
            available -= max(0, -model.memoize(earlier, t))
        return -max(0, min(-wanted, available))
