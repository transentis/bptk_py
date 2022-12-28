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


from .element import ArrayedEquation, Element
from .element import ElementError


class Constant(Element):
    """
    A constant in a SD DSL model
    """
    type = "Constant"

    def add_arr_equation(self, name, value):
        s = self.model.constant(self.name + "[" + name + "]")
        s.equation = value

    def add_arr_empty(self, name):
        return self.model.constant(self.name + "[" + name + "]")

    def get_arr_equation(self, name):
        return self.model.constants[self.name + "[" + name + "]"]

    @property
    def equation(self):
        return super().equation

    @equation.setter
    def equation(self, equation):
        if not self._handle_arrayed(equation):
            self._equation = equation
            if isinstance(equation, (float, int)):
                self._function_string = "lambda model, t: {}".format(equation)
            elif equation == None:
                self._equation = None
            else:
                raise ElementError(
                    "Constants can only contain floating point values")
        else:
            self._equation = None

        self.model.reset_cache()
        self.generate_function()
