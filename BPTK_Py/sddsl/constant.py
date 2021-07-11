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


class Constant(Element):
    """
    A constant in a SD DSL model
    """
    type = "Constant"

    @property
    def equation(self):
       return super().equation

    @equation.setter
    def equation(self, equation):
        self._equation = equation

        self.model.reset_cache()


        if isinstance(equation, (float)):
            self._function_string = "lambda model, t: {}".format(equation)
        else:
            raise ElementError("Constants can only contain floating point values")

        self.generate_function()



