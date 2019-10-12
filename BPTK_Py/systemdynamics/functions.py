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


from .operators import MaxOperator, MinOperator, UnaryOperator, OperatorError
from .constant import Constant

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

    def __init__(self, element, points):
        self.element = element

        if type(points) is str:
            self.points = "\"" + points + "\""
        else:
            self.points = points

    def term(self, time="t"):
        return "model.lookup({},{})".format(self.element, self.points)

class Step(Function):
    """
    Step Function.
    """

    def __init__(self, height, timestep):
        self.height = UnaryOperator(height) if issubclass(type(height), (float)) else height
        self.timestep = UnaryOperator(timestep) if issubclass(type(timestep), (float)) else timestep

    def term(self, time="t"):
        return "{} if {}>{} else 0".format(self.height.term(time), time, self.timestep.term(time))


class Trend(Function):
    """
    Trend function.
    """

    def __init__(self, model, input_function, averaging_time, initial_value):
        self.id = model.equation_prefix
        self.averaging_time = model.converter(self.id+"averaging_time")
        self.averaging_time.equation = averaging_time
        self.initial_value = model.converter(self.id+"initial_value")
        self.initial_value.equation = initial_value
        self.exponential_average = model.stock(self.id+"exponential_average")
        self.input_function = model.converter(self.id+"input_function")
        self.input_function.equation = input_function
        self.exponential_average.initial_value = initial_value
        self.change_in_average = model.flow(self.id+"change_in_average")
        self.change_in_average.equation = (self.input_function - self.exponential_average) / self.averaging_time
        self.exponential_average.equation = self.change_in_average
        self.trend = model.converter(self.id+"trend")
        self.trend.equation = (self.input_function - self.exponential_average) / (self.exponential_average * self.averaging_time)

    def term(self, time="t"):
        return self.trend.term(time)

class Smooth(Function):
    """
    Trend function.
    """

    def __init__(self, model, input_function, averaging_time, initial_value):
        self.id = model.equation_prefix
        self.averaging_time = model.converter(self.id+"averaging_time")
        self.averaging_time.equation = averaging_time
        self.initial_value = model.converter(self.id+"initial_value")
        self.initial_value.equation = initial_value
        self.smooth = model.stock(self.id+"smooth")
        self.input_function = model.converter(self.id+"input_function")
        self.input_function.equation = input_function
        self.smooth.initial_value = initial_value
        self.change_in_smooth = model.flow(self.id+"change_in_smooth")
        self.change_in_smooth.equation = (self.input_function - self.smooth) / self.averaging_time
        self.smooth.equation = self.change_in_smooth

    def term(self, time="t"):
        return self.smooth.term(time)


def time():
    return Time()


def max(x, y):
    return MaxOperator(x, y)


def min(x, y):
    return MinOperator(x, y)


def lookup(element, points):
    return Lookup(element, points)


def trend(model, input_function,averaging_time,initial_value):
    if isinstance(initial_value, (float, Constant)):
        return Trend(model, input_function, averaging_time, initial_value)
    else:
        raise OperatorError("The initial value must be a floating point values or a constants")


def smooth(model, input_function, averaging_time, initial_value):
    if isinstance(initial_value, (float, Constant)):
        return Smooth(model, input_function, averaging_time, initial_value)
    else:
        raise OperatorError("The initial value must be a floating point values or a constants")


def step(height, timestep):
    return Step(height, timestep)

