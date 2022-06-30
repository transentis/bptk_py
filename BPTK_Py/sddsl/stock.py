#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License


from .element import ArrayedEquation, Element
from .element import ElementError
from .constant import Constant
from .converter import Converter

class Stock(Element):
    """Stock in a SD DSL model.
    """

    type = "Stock"

    def __init__(self, model, name):
        super(Stock, self).__init__(model, name)
        self.__initial_value = 0.0

    def default_function_string(self):
        return "lambda model, t : ( (0) if (t <= model.starttime) else (model.memoize('{}',t-model.dt)) )".format(self.name)

    @property
    def initial_value(self):
        return self.__initial_value

    @initial_value.setter
    def initial_value(self, initial_value):
        if isinstance(initial_value, (float, Constant, Converter)):
            self.__initial_value = initial_value
            self.build_function_string()
            self.generate_function()
        else:
            raise ElementError("Initial values must be floating point values, constants or converters")


    def update_equation(self):
        self.model.reset_cache()
        self.build_function_string()
        self.generate_function()

    @property
    def equation(self):
        return super().equation


    @equation.setter
    def equation(self, equation):
        self._equation = equation
        self.update_equation()

    def build_function_string(self):
        start_string = "lambda model, t : ( ("
        start_string += str(self.__initial_value)

        if self.equation is not None:
            if(isinstance(self._equation, ArrayedEquation)):
                start_strings = {}
                for k in self._equation.equation.keys():
                    start_strings[k] = start_string + ") if (t <= model.starttime) else (model.memoize('{}',t-model.dt))".format(self.name + "[" + str(k) + "]") + "+ model.dt*(" + self.equation.equation[k].term("t-model.dt") + ") )"
                self._function_string = start_strings
            else:
                start_string += ") if (t <= model.starttime) else (model.memoize('{}',t-model.dt))".format(self.name) + "+ model.dt*("
                self._function_string = start_string + self._equation.term("t-model.dt") + ") )"
        else:
            start_string += ") if (t <= model.starttime) else (model.memoize('{}',t-model.dt))".format(self.name) + "+ model.dt*("
            self._function_string = start_string + ")"



