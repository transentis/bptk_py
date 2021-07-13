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

    @equation.setter
    def equation(self, equation):
        self._equation = equation
        self.model.reset_cache()
        self.build_function_string()
        self.generate_function()

    def build_function_string(self):
        from .operators import Operator
        right_term = self._equation.term("t-model.dt") if type(self._equation) is Operator else self._equation
        self._function_string = "lambda model, t : max( {},{})".format(0,right_term) # A flow never gets negative
