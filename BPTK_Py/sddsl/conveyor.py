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

import math

from . import belt as belts
from . import element as _element_module
from .element import Element, ElementError, _reshaping
from .operators import Operator
from .stock import Stock, _leaves


def _is_value(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            or isinstance(value, (Element, Operator)))


def _compiled(value):
    """A function of (model, t) for a number, an element or an expression."""
    if isinstance(value, (int, float)):
        number = float(value)
        return lambda model, t: number
    return eval("lambda model, t: {}".format(value.term("t")), vars(_element_module))


class Conveyor(Stock):
    """A conveyor in a SD DSL model: a stock that works like a conveyor belt.

    Material put on at one end comes off at the other after the transit time; leakage flows
    take a share of it on the way. The conveyor computes its outflow and its leakage
    flows itself, so they carry no equation of their own.
    """

    _is_conveyor = True

    def __init__(self, model, name):
        super(Conveyor, self).__init__(model, name)
        self._transit = None
        self._initial = 0.0
        self._initial_set = False
        self._leaks = []                 # (flow, fraction) in order of priority
        self._exponential = False
        self._fifo = False
        self._plan = None
        self._driving = []

    def default_function_string(self):
        return "lambda model, t: model.stocks['{}']._contents(t)".format(self.name)

    # -- what the modeller sets ---------------------------------------------------------

    @property
    def initial_value(self):
        return self._initial

    @initial_value.setter
    def initial_value(self, initial_value):
        if isinstance(initial_value, (list, tuple)):
            if not initial_value or not all(
                    isinstance(value, (int, float)) and not isinstance(value, bool)
                    for value in initial_value):
                raise ElementError(
                    "The initial value of conveyor '{}' is a list, and a list has to hold "
                    "numbers - one per time unit on the belt, the first leaving "
                    "first.".format(self.name))
            initial_value = list(initial_value)
        elif not _is_value(initial_value):
            raise ElementError(
                "The initial value of conveyor '{}' is a {}. It has to be a number, an "
                "element, an expression or a list of numbers.".format(
                    self.name, type(initial_value).__name__))
        self._initial = initial_value
        self._initial_set = True
        # Set on the whole, it is the start of every cell; a cell set afterwards keeps its own.
        for cell in _leaves(self).values():
            if cell is not self:
                cell._initial_set = False
        self._changed()

    @property
    def equation(self):
        return None

    @equation.setter
    def equation(self, equation):
        # Giving a conveyor a shape assigns None to each of its cells.
        if equation is not None:
            raise ElementError(
                "'{}' is a conveyor and has no equation: what enters comes from "
                "{}.inflows, what leaves from the belt itself.".format(self.name, self.name))

    @property
    def non_negative(self):
        return True

    @non_negative.setter
    def non_negative(self, non_negative):
        raise ElementError(
            "'{}' is a conveyor, and a conveyor never falls below zero: its outflow and "
            "its leakage take only what lies on the belt.".format(self.name))

    @property
    def transit_time(self):
        """How long material stays on the belt, in time units."""
        return self._transit

    @transit_time.setter
    def transit_time(self, transit_time):
        if not _is_value(transit_time):
            raise ElementError(
                "The transit time of conveyor '{}' is a {}. It has to be a number, an "
                "element or an expression.".format(self.name, type(transit_time).__name__))
        if isinstance(transit_time, (int, float)) and not transit_time > 0:
            raise ElementError(
                "The transit time of conveyor '{}' is {}. It has to be greater than "
                "zero.".format(self.name, transit_time))
        self._transit = transit_time
        self._changed()

    @property
    def inflows(self):
        return list(self._inflows)

    @inflows.setter
    def inflows(self, flows):
        flows = list(flows)
        for flow in flows:
            if not isinstance(flow, Element) or flow.type != "Flow":
                raise ElementError(
                    "The inflows of conveyor '{}' have to be flows: what enters a conveyor "
                    "cannot be negative. {} is a {}.".format(
                        self.name, getattr(flow, "name", flow), getattr(flow, "type", type(flow).__name__)))
        self._inflows = flows
        self._changed()

    @property
    def outflows(self):
        return list(self._outflows)

    @outflows.setter
    def outflows(self, flows):
        flows = list(flows)
        if len(flows) > 1:
            raise ElementError(
                "A conveyor has one outflow, the end of its belt; '{}' was given {}. "
                "Leakage goes into {}.leaks.".format(self.name, len(flows), self.name))
        self._take_over(flows, self._leak_flows())
        self._outflows = flows
        self._changed()

    @property
    def leaks(self):
        """The leakage flows and the share each takes, in order of priority."""
        return dict(self._leaks)

    @leaks.setter
    def leaks(self, leaks):
        if not isinstance(leaks, dict):
            raise ElementError(
                "The leaks of conveyor '{}' are a dict: each leakage flow and the share it "
                "takes, as in {{deaths: 0.02}}.".format(self.name))
        for flow, fraction in leaks.items():
            if not _is_value(fraction):
                raise ElementError(
                    "The leak fraction of '{}' on conveyor '{}' is a {}. It has to be a "
                    "number, an element or an expression.".format(
                        getattr(flow, "name", flow), self.name, type(fraction).__name__))
        self._take_over(list(self._outflows), list(leaks))
        self._leaks = list(leaks.items())
        self._changed()

    @property
    def exponential_leak(self):
        """True: a leak fraction is a rate per time unit on what is left. False, the
        default as in XMILE: the share of a cohort that leaks over its time on the belt."""
        return self._exponential

    @exponential_leak.setter
    def exponential_leak(self, exponential):
        self._exponential = self._boolean("exponential_leak", exponential)
        self._changed()

    @property
    def fifo(self):
        """True: a change of the transit time speeds up or slows down the whole belt, and
        nothing overtakes. False, the default: material keeps the transit time it entered
        with, and newer material can leave first."""
        return self._fifo

    @fifo.setter
    def fifo(self, fifo):
        self._fifo = self._boolean("fifo", fifo)
        self._changed()

    def _boolean(self, name, value):
        if not isinstance(value, bool):
            raise ElementError("{} of conveyor '{}' has to be True or False.".format(name, self.name))
        return value

    def _leak_flows(self):
        return [flow for flow, _ in self._leaks]

    def _take_over(self, outflows, leaks):
        """Checks the flows the belt is to drive, and frees those it no longer drives."""
        driven = outflows + leaks
        for flow in driven:
            if not isinstance(flow, Element) or flow.type != "Flow":
                raise ElementError(
                    "The outflow and the leaks of conveyor '{}' have to be flows; {} is "
                    "not.".format(self.name, getattr(flow, "name", flow)))
            if sum(other is flow for other in driven) > 1:
                raise ElementError(
                    "'{}' is named twice among the outflow and the leaks of conveyor "
                    "'{}'.".format(flow.name, self.name))
            owner = getattr(flow, "_conveyor", None)
            if owner is not None and owner is not self:
                raise ElementError(
                    "'{}' is already driven by conveyor '{}'.".format(flow.name, owner.name))
            if owner is None and any(leaf.equation is not None for leaf in _leaves(flow).values()):
                raise ElementError(
                    "'{}' has an equation, but conveyor '{}' computes its value. Remove "
                    "the equation first: {}.equation = None.".format(flow.name, self.name, flow.name))
        for flow in self._outflows + self._leak_flows():
            if not any(flow is other for other in driven):
                self._release(flow)
        for flow in driven:
            for leaf in _leaves(flow).values():
                leaf._conveyor = self
            flow._conveyor = self

    def _release(self, flow):
        for leaf in list(_leaves(flow).values()) + [flow]:
            leaf._conveyor = None
            leaf._driven_by = None
            leaf.build_function_string()
            leaf.generate_function()

    # -- arrays -------------------------------------------------------------------------

    def add_arr_equation(self, name, value):
        cell = self.model.conveyor(self.name + "[" + name + "]")
        cell.equation = value

    def add_arr_empty(self, name):
        return self.model.conveyor(self.name + "[" + name + "]")

    def get_arr_equation(self, name):
        return self.model.stocks[self.name + "[" + name + "]"]

    # -- wiring the cells ---------------------------------------------------------------

    def _changed(self):
        self.model.reset_cache()
        self._distribute()

    def _distribute(self):
        """Gives every cell the flows, the transit time and the fractions of its own.

        Arrayed flows and elements contribute their cell at the same position; scalar
        ones are shared. What is not set yet is checked when the model runs.
        """
        for flow in self._driving:
            flow._driven_by = None
            flow.build_function_string()
            flow.generate_function()
        self._driving = []
        cells = _leaves(self)
        arrayed = len(cells) > 1 or () not in cells

        def cell_of(value, path, what):
            if isinstance(value, Element) and value._elements.vector_size() > 0:
                leaves = _leaves(value)
                if path not in leaves:
                    raise ElementError(
                        "'{}' and the {} '{}' have different shapes.".format(self.name, what, value.name))
                return leaves[path]
            if isinstance(value, Operator) and value.is_any_subelement_arrayed():
                raise ElementError(
                    "The {} of conveyor '{}' is an arrayed expression. Give it an element "
                    "of its own and use that.".format(what, self.name))
            return value

        driven = self._outflows + self._leak_flows()
        if arrayed:
            for flow in driven:
                if flow._elements.vector_size() == 0:
                    _give_shape(flow, self)
                for leaf in _leaves(flow).values():
                    leaf._conveyor = self
        for path, cell in cells.items():
            initial = cell._initial if (cell is self or cell._initial_set) else self._initial
            cell._plan_source = {
                "inflows": [cell_of(flow, path, "inflow").name for flow in self._inflows],
                "outflow": [cell_of(flow, path, "outflow").name for flow in self._outflows],
                "leaks": [(cell_of(flow, path, "leak").name, cell_of(fraction, path, "leak fraction"))
                          for flow, fraction in self._leaks],
                "transit": None if self._transit is None else cell_of(self._transit, path, "transit time"),
                "initial": initial if isinstance(initial, list) else cell_of(initial, path, "initial value"),
                "exponential": self._exponential,
                "fifo": self._fifo,
            }
            cell._plan = None
            for name in cell._plan_source["outflow"] + [name for name, _ in cell._plan_source["leaks"]]:
                flow = self.model.flows[name]
                flow._driven_by = cell.name
                flow.build_function_string()
                flow.generate_function()
                self._driving.append(flow)

    def _resolved(self):
        """The plan of this cell, compiled, after checking that it is complete."""
        if self._plan is not None:
            return self._plan
        source = getattr(self, "_plan_source", None)
        if source is None:
            self._distribute()
            source = self._plan_source
        if source["transit"] is None:
            raise ElementError("Conveyor '{}' has no transit time.".format(self.name))
        if not source["outflow"]:
            raise ElementError(
                "Conveyor '{}' has no outflow: {}.outflows names the flow its belt empties "
                "into.".format(self.name, self.name))
        initial = source["initial"]
        self._plan = {
            "inflows": source["inflows"],
            "outflow": source["outflow"][0],
            "leaks": [name for name, _ in source["leaks"]],
            "fractions": [_compiled(fraction) for _, fraction in source["leaks"]],
            "transit": _compiled(source["transit"]),
            "initial": initial if isinstance(initial, list) else _compiled(initial),
            "exponential": source["exponential"],
            "fifo": source["fifo"],
        }
        return self._plan

    # -- running ------------------------------------------------------------------------

    def _memo(self, kind):
        key = "{}\x00{}".format(self.name, kind)
        memo = self.model.memo.get(key)
        if memo is None:
            memo = self.model.memo[key] = {}
        return memo

    def _step_of(self, t):
        return max(0, int(round((t - self.model.starttime) / self.model.dt)))

    def _transit_at(self, plan, t):
        transit = plan["transit"](self.model, t)
        if not (isinstance(transit, (int, float)) and math.isfinite(transit) and transit > 0):
            raise ElementError(
                "The transit time of conveyor '{}' is {} at t={}. It has to be greater "
                "than zero.".format(self.name, transit, t))
        return transit

    def _fractions_at(self, plan, t):
        fractions = [fraction(self.model, t) for fraction in plan["fractions"]]
        for name, fraction in zip(plan["leaks"], fractions):
            if not (math.isfinite(fraction) and fraction >= 0):
                raise ElementError(
                    "The leak fraction of '{}' on conveyor '{}' is {} at t={}. It has to "
                    "be zero or more.".format(name, self.name, fraction, t))
        return fractions

    def _belt(self, step):
        states = self._memo("belt")
        if step in states:
            return states[step]
        self.model._memo_filled = True
        if 0 not in states:
            plan = self._resolved()
            start = self.model.starttime
            initial = plan["initial"]
            states[0] = belts.filled(
                plan["fifo"], plan["exponential"], start, self.model.dt,
                self._transit_at(plan, start), self._fractions_at(plan, start),
                initial if isinstance(initial, list) else initial(self.model, start))
            if step == 0:
                return states[0]
        done = step - 1
        while done not in states:
            done -= 1
        for earlier in range(done, step):
            self._advance(earlier)
        return states[step]

    def _advance(self, step):
        """Moves the belt through timestep `step`; returns what left it."""
        # An input that reads the conveyor's own outflow within the step is a cycle, which
        # the model's evaluation reports by the names on it.
        moves = self._memo("moves")
        if step in moves:
            return moves[step]
        model = self.model
        plan = self._resolved()
        t = model.starttime + step * model.dt
        current = self._belt(step)
        inflow = sum(model.memoize(name, t) for name in plan["inflows"]) * model.dt
        exited, leaked, following = current.advance(
            t, model.dt, inflow, self._transit_at(plan, t), self._fractions_at(plan, t))
        moves[step] = (exited, leaked)
        self._memo("belt")[step + 1] = following
        return moves[step]

    def _contents(self, t):
        return self._belt(self._step_of(t)).contents()

    def _driven(self, flow, t):
        """The value of a flow the belt drives: its outflow or one of its leaks."""
        plan = self._resolved()
        step = self._step_of(t)
        self._belt(step)
        exited, leaked = self._advance(step)
        if flow == plan["outflow"]:
            return exited / self.model.dt
        return leaked[plan["leaks"].index(flow)] / self.model.dt

    def _agecount(self, t, minimum, maximum):
        return self._belt(self._step_of(t)).agecount(t, minimum, maximum)


def _give_shape(flow, conveyor):
    """Gives a scalar flow the shape of an arrayed conveyor, with no equation in its cells."""
    with _reshaping():
        def mirror(target, source):
            target.arrayed = True
            target.named_arrayed = source.named_arrayed
            for key in source._elements.equations:
                target._elements[key] = None
                if source[key]._elements.vector_size() > 0:
                    mirror(target[key], source[key])
        mirror(flow, conveyor)
