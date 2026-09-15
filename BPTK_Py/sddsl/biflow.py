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