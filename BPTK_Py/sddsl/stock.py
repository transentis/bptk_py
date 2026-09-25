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
from .constant import Constant
from .converter import Converter
from .operators import Operator


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
