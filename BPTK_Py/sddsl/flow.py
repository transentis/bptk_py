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


from .element import Element


class Flow(Element):
    """
    Flow in a SD DSL model.
    """
    type = "Flow"

    @property
    def equation(self):
       return super().equation

    def add_arr_equation(self, name, value):
        s = self.model.flow(self.name + "[" + name + "]")
        s.equation = value
    def add_arr_empty(self, name):
        return self.model.flow(self.name + "[" + name + "]")

    def get_arr_equation(self, name):
        return self.model.flows[self.name + "[" + name + "]"]

    @equation.setter
    def equation(self, equation):
        conveyor = getattr(self, "_conveyor", None)
        if conveyor is not None and equation is not None:
            from .element import ElementError
            raise ElementError(
                "'{}' is driven by conveyor '{}', which computes its value. Take it out of "
                "the conveyor's outflows or leaks to give it an equation.".format(self.name, conveyor.name))
        if not self._handle_arrayed(equation):
            self._equation = equation
        self.model.reset_cache()
        self.build_function_string()
        self.generate_function()

    def build_function_string(self):
        from .operators import Operator
        right_term = self._equation.term("t-model.dt") if type(self._equation) is Operator else self._equation
        driven_by = getattr(self, "_driven_by", None)
        if driven_by is not None:
            self._function_string = "lambda model, t : model.stocks['{}']._driven('{}', t)".format(
                driven_by, self.name)
            return
        constraint = getattr(self, "_constraint", None)
        if constraint is None:
            self._function_string = "lambda model, t : max( {},{})".format(0,right_term) # A flow never gets negative
            return
        # An outflow of a non-negative stock is cut back by the stock it leaves.
        wanted = "max(0, {})".format(0 if right_term is None else right_term)
        self._function_string = "lambda model, t : model.stocks['{}']._cut_back('{}', {}, t)".format(
            constraint, self.name, wanted)
