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

from .operators import *
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
    if not isinstance(volume, (Element, float)):
        raise OperatorError("The volume must be a model element or a floating point value")
    if not isinstance(first_pulse, (float, Constant)):
        raise OperatorError("The first pulse must be a floating point values or a constant")
    if not isinstance(interval, (float, Constant)):
        raise OperatorError("The interval must be a floating point values or a constant")

    return Pulse(model, volume, first_pulse, interval)


def trend(model, input_function, averaging_time, initial_value):
    if isinstance(initial_value, (float, Constant)):
        return Trend(model, input_function, averaging_time, initial_value)
    else:
        raise OperatorError("The initial value must be a floating point values or a constants")


def smooth(model, input_function, averaging_time, initial_value):
    if isinstance(initial_value, (float, Constant)):
        return Smooth(model, input_function, averaging_time, initial_value)
    else:
        raise OperatorError("The initial value must be a floating point values or a constants")


def step(height, timestep):  return Step(height, timestep)


def exp(x): return Exp(x)


def delay(model, input_function, delay_duration, initial_value=None):
    if not isinstance(input_function, Element):
        raise OperatorError("The input function must be a model element")
    if not isinstance(delay_duration, (Element, float)):
        raise OperatorError("The delay duration must be a model element or a floating point value")
    if initial_value is not None and not isinstance(initial_value, (float, Constant)):
        raise OperatorError("The initial value must be a floating point values or a constant")

    return Delay(model, input_function, delay_duration, initial_value)


def uniform(min_value=0, max_value=1): return Random(min_value, max_value)


def random(min_value=0, max_value=1): return Random(min_value, max_value)


def round(operator, digits): return Round(operator, digits)


def If(if_, then_, else_):
    from .operators import If
    return If(if_, then_, else_)


def And(lhs, rhs):
    from .operators import And
    return And(lhs, rhs)


def Or(lhs, rhs):
    from .operators import Or
    return Or(lhs, rhs)


def Not(condition):
    from .operators import Not
    return Not(condition)


def nan(): return Nan()


def sqrt(x): return Sqrt(x)


def sin(x): return Sin(x)


def tan(x): return Tan(x)


def cos(x): return Cos(x)


def arccos(x): return Arccos(x)


def arcsin(x): return Arcsin(x)


def arctan(x): return Arctan(x)


def sinwave(amplitude, period): return Sinwave(amplitude, period)


def coswave(amplitude, period): return Coswave(amplitude, period)


def Inf(): return Inf()


def pi(): return Pi()


"""
Statistical Functions
"""


def beta(a, b): return Beta(a, b)


def binomial(n, p): return Binomial(n, p)


def combinations(n, r): return Combinations(n, r)


def exprnd(l): return Exprnd(l)


def factorial(n): return Factorial(n)


def gamma(n, scale=1): return Gamma(n, scale)


def gammaln(n): return GammaLN(n)


def geometric(p): return Geometric(p)


def invnorm(p, mean=None, stddev=None): return Invnorm(p, mean, stddev)


def logistic(mean, scale): return Logistic(mean, scale)


def lognormal(mean, stddev): return Lognormal(mean, stddev)


def montecarlo(p): return Montecarlo(p)


def normal(mean, stddev): return Normal(mean, stddev)


def normalcdf(left, right, mean=0, stddev=1): return NormalCDF(left, right, mean, stddev)


def pareto(shape, scale): return Pareto(shape, scale)


def permutations(n, r): return Permutations(n, r)


def poisson(mu): return Poisson(mu)


def triangular(lower_bound, mode, upper_bound): return Triangular(lower_bound, mode, upper_bound)

def weibull(shape, scale): return Weibull(shape, scale)