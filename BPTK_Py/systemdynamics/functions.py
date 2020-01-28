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

from .operators import MaxOperator, MinOperator, Lookup, Trend, Smooth, Step, Exp, Time, OperatorError, Delay, AbsOperator, DT, Starttime, Stoptime, Pulse
from .constant import Constant
from .element import Element

def abs(x):
    return AbsOperator(x)

def dt(model):
    return DT(model)

def starttime(model):
    return Starttime(model)

def stoptime(model):
    return Stoptime(model)

def time():
    return Time()


def max(x, y):
    return MaxOperator(x, y)

def min(x, y):
    return MinOperator(x, y)

def lookup(element, points):
    return Lookup(element, points)

def pulse(model, volume, first_pulse=0.0, interval=0.0):
    if not isinstance(volume,(Element, float)):
        raise OperatorError("The volume must be a model element or a floating point value")
    if not isinstance(first_pulse, (float, Constant)):
        raise OperatorError("The first pulse must be a floating point values or a constant")
    if not isinstance(interval, (float, Constant)):
        raise OperatorError("The interval must be a floating point values or a constant")

    return Pulse(model, volume, first_pulse, interval)

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


def exp(x):
    return Exp(x)


def delay(model, input_function, delay_duration, initial_value=None):
    if not isinstance(input_function, Element):
        raise OperatorError("The input function must be a model element")
    if not isinstance(delay_duration, (Element, float)):
        raise OperatorError("The delay duration must be a model element or a floating point value")
    if initial_value is not None and isinstance(initial_value, (float, Constant)):
        raise OperatorError("The initial value must be a floating point values or a constant")

    return Delay(model, input_function, delay_duration, initial_value)

def uniform(min_value=0,max_value=1):
    from .operators import Random
    return Random(min_value,max_value)

def random(min_value=0,max_value=1):
    from .operators import Random
    return Random(min_value,max_value)

def round(operator, digits):
    from .operators import Round
    return Round(operator, digits)

def If(if_,then_,else_):
    from .operators import If
    return If(if_,then_,else_)

def And(lhs,rhs):
    from .operators import And
    return And(lhs,rhs)

def Or(lhs,rhs):
    from .operators import Or
    return Or(lhs,rhs)

def Not(condition):
    from .operators import Not
    return Not(condition)

def nan():
    from .operators import nan
    return nan()

def sqrt(x):
    from .operators import sqrt
    return sqrt(x)

def sin(x):
    from .operators import sin
    return sin(x)

def tan(x):
    from .operators import tan
    return tan(x)

def cos(x):
    from .operators import cos
    return cos(x)

def arccos(x):
    from .operators import arccos
    return arccos(x)

def arcsin(x):
    from .operators import arcsin
    return arcsin(x)

def arctan(x):
    from .operators import arctan
    return arctan(x)

def sinwave(amplitude,period):
    from .operators import sinwave
    return sinwave(amplitude,period)

def coswave(amplitude,period):
    from .operators import coswave
    return coswave(amplitude,period)

