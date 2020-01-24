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


from .element import Element
from .element import ElementError
from .constant import Constant
from .converter import Converter

class Stock(Element):

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


    @property
    def equation(self):
        return super().equation


    @equation.setter
    def equation(self, equation):
        self._equation = equation

        self.model.reset_cache()
        self.build_function_string()
        self.generate_function()

    def build_function_string(self):
        self.function_string = "lambda model, t : ( ("
        self.function_string += str(self.__initial_value)
        self.function_string += ") if (t <= model.starttime) else (model.memoize('{}',t-model.dt))".format(self.name)

        if self._equation is not None:
            self.function_string += "+ model.dt*("
            self.function_string += self._equation.term("t-model.dt")
            self.function_string += ") )"
        else:
            self.function_string += ")"



