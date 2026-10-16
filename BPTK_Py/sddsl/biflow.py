#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2020 transentis labs GmbH
# MIT License


from . import element as _element_module
from .element import Element

class Biflow(Element):
    """
    Biflow in a SD DSL model
    """
    type = "Biflow"

    def add_arr_equation(self, name, value):
        b = self.model.biflow(self.name + "[" + name + "]")
        b.equation = value

    def add_arr_empty(self, name):
        return self.model.biflow(self.name + "[" + name + "]")

    def get_arr_equation(self, name):
        return self.model.biflows[self.name + "[" + name + "]"]
    @property
    def equation(self):
        return super().equation

    @equation.setter
    def equation(self, equation):
        if not self._handle_arrayed(equation):
            self._equation = equation
        else:
            self._equation = None
        self.model.reset_cache()
        self.build_function_string()
        self.generate_function()

    def build_function_string(self):
        constraint = getattr(self, "_constraint", None)
        if constraint is None:
            self._function_string = "lambda model, t: {}".format(self.equation)
            return
        # A biflow of a non-negative stock is cut back by that stock while it drains it.
        wanted = 0 if self.equation is None else self.equation
        self._function_string = "lambda model, t : model.stocks['{}']._cut_back('{}', {}, t)".format(
            constraint, self.name, wanted)

    def wanted(self, t):
        """The value of the equation at `t`, before a non-negative stock cuts it back."""
        if "_wanted" not in vars(self) or self._wanted_for is not self._equation:
            # Compiled where every equation is, so the names its term uses resolve.
            term = 0 if self._equation is None else self._equation
            self._wanted = eval("lambda model, t: {}".format(term), vars(_element_module))
            self._wanted_for = self._equation
        return self._wanted(self.model, t)
