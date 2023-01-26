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


class Converter(Element):
    """
    A converter in an SD DSL model
    """
   

    type = "Converter"


    def add_arr_equation(self, name, value):
        s = self.model.converter(self.name + "." + name)
        s.equation = value
    def add_arr_empty(self, name):
        return self.model.converter(self.name + "." + name)

    def get_arr_equation(self, name):
        return self.model.converters[self.name + "." + name]

