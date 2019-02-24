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


from .operators import MaxOperator, MinOperator

class Function:
    """
    Generic function class
    """

    def term(self, time="t"):
        return "function"

    def __str__(self):
        """
        Operator override
        :return: term as string
        """
        return self.term()

class Time(Function):
    """
    Time function

    """

    def term(self, time="t"):
        """

        :return: time of the simulation: "t"
        """
        return time




class Lookup(Function):
    """
    Lookup function. Uses the points of a graphical function for interpolation
    """

    def __init__(self, element,points):
        self.element=element

        if type(points) is str:
            self.points="\"" + points + "\""
        else:
            self.points = points

    def term(self, time="t"):
        return "model.lookup({},{})".format(self.element, self.points)


def time():
    return Time()


def max(x, y):
    return MaxOperator(x, y)


def min(x, y):
    return MinOperator(x, y)


def lookup(element, points):
    return Lookup(element, points)
