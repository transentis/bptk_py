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

import functools

from .operators import *
from .operators import Inf as _InfOp
from .operators import _check_operand
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


def max(x, y, *more):
    # Any number of arguments, folded pairwise - two arguments give the operator they
    # always gave
    return functools.reduce(MaxOperator, more, MaxOperator(x, y))


def min(x, y, *more):
    return functools.reduce(MinOperator, more, MinOperator(x, y))


def _operand(value):
    # A plain number becomes an operator, so that comparisons and arithmetic on it build
    # an expression instead of being computed here
    return value if isinstance(value, (Operator, Element)) else UnaryOperator(value)


def _check_operands(*values):
    # An argument of a builtin is an element, an expression or a number, as an operand
    # is; None stands for an argument left out
    for value in values:
        if value is not None:
            _check_operand(value)


def _as_element(model, value):
    # The builtins that read a variable's past need an element; an expression gets a
    # converter of its own
    if isinstance(value, Element):
        return value
    holder = model.converter(model.equation_prefix + "input")
    holder.equation = value
    return holder


def init(model, variable):
    # XMILE's INIT: the value at STARTTIME
    variable = _as_element(model, variable)
    now = Time()
    return If(now <= Starttime(model), variable,
              Delay(model, variable, now - Starttime(model)))


def previous(model, variable, initial_value):
    # XMILE's PREVIOUS: the value one dt back, initial_value at the first step
    return Delay(model, _as_element(model, variable), DT(model), initial_value)


def history(model, variable, time):
    # Stella's HISTORY: the value at an earlier time of the run; 0 for a time after the
    # current one or before the start
    variable = _as_element(model, variable)
    when, now = _operand(time), Time()
    return If(And(when <= now, when >= Starttime(model)),
              Delay(model, variable, now - when), 0.0)


def derivn(model, variable, order):
    # Stella's DERIVN: the order-th derivative by repeated differences over one dt, 0
    # for the first `order` steps
    if isinstance(order, bool) or not isinstance(order, int) or order < 0:
        raise OperatorError("The order must be a whole number of at least 0")
    level = _as_element(model, variable)
    prefix = model.equation_prefix
    step = DT(model)
    for k in range(1, order + 1):
        derivative = model.converter("{}derivative_{}".format(prefix, k))
        derivative.equation = If(Time() >= Starttime(model) + (k - 0.5) * step,
                                 (level - Delay(model, level, step, 0.0)) / step, 0.0)
        level = derivative
    return level


def irr(model, stream, missing=None):
    # Stella's IRR: the rate at which the stream so far has a net present value of zero
    return Irr(_as_element(model, stream), missing)


def lookupinv(value, points):
    # Stella's LOOKUPINV, for a monotonic table: the x at which it reaches value
    return LookupInverse(value, points)


def rank(array, rank, tiebreak=None):
    # XMILE's RANK: the position of the rank-th smallest element, counting from 0
    return Rank(array, rank, tiebreak)


def interpolate(array, *weights):
    # Stella's INTERPOLATE: between an array's elements, one weight in [0, 1] per dimension
    return Interpolate(array, *weights)


def agecount(conveyor, minimum, maximum):
    # Stella's AGECOUNT: what has been on the conveyor at least minimum, less than maximum
    if not getattr(conveyor, "_is_conveyor", False):
        raise OperatorError("agecount counts the material on a conveyor; {} is not one.".format(
            getattr(conveyor, "name", conveyor)))
    return AgeCount(conveyor, minimum, maximum)


def lookuparea(points, from_x=None, to_x=None):
    # Stella's LOOKUPAREA: the area under the table, between from_x and to_x if given
    return LookupArea(points, from_x, to_x)


def ramp(slope, start_time, end_time=None):
    # XMILE's RAMP, with Stella's optional end time: 0 until start_time, then rising with
    # slope, and from end_time on holding the value reached
    now = Time()
    start = _operand(start_time)
    until = now if end_time is None else MinOperator(now, end_time)
    return If(now > start, slope * (until - start), 0.0)


def safediv(numerator, denominator, on_zero=0.0):
    # Stella's SAFEDIV: the quotient, or on_zero where the denominator is zero
    denominator = _operand(denominator)
    return If(denominator == 0.0, on_zero, _operand(numerator) / denominator)


def rootn(x, n):
    # Stella's ROOTN: the n-th root; of a negative number only for an odd n, NaN otherwise
    x, n = _operand(x), _operand(n)
    exponent = 1.0 / n
    return If(x >= 0.0, x ** exponent,
              If(n % 2.0 == 1.0, -((-x) ** exponent), Nan()))


def percent(x):
    # Stella's PERCENT: a fraction as a percentage
    return _operand(x) * 100.0


def _compounding(rate, periods):
    return (1.0 + _operand(rate)) ** periods


def pmt(rate, periods, present_value, future_value=0.0):
    # Stella's PMT: the payment per period, signed as in a spreadsheet
    rate = _operand(rate)
    growth = _compounding(rate, periods)
    return If(rate == 0.0,
              -(_operand(present_value) + future_value) / periods,
              -(present_value * growth + future_value) * rate / (growth - 1.0))


def fv(rate, periods, payment, present_value=0.0):
    # Stella's FV: the value after the periods, signed as in a spreadsheet
    rate = _operand(rate)
    growth = _compounding(rate, periods)
    return If(rate == 0.0,
              -(_operand(present_value) + payment * periods),
              -(present_value * growth + payment * (growth - 1.0) / rate))


def pv(rate, periods, payment, future_value=0.0):
    # Stella's PV: the value today, signed as in a spreadsheet
    rate = _operand(rate)
    growth = _compounding(rate, periods)
    return If(rate == 0.0,
              -(_operand(future_value) + payment * periods),
              -(future_value + payment * (growth - 1.0) / rate) / growth)


def cgrowth(model, percentage):
    # Stella's CGROWTH: the rate per dt that, compounded over one time unit, grows a stock
    # by `percentage` percent whatever dt is
    step = DT(model)
    return ((1.0 + _operand(percentage) / 100.0) ** step - 1.0) / step


def counter(model, start, end):
    # Stella's COUNTER: start at STARTTIME, one up per time unit, back to start on reaching end
    start = _operand(start)
    return start + (Time() - Starttime(model)) % (end - start)


def lookup(element, points):
    return Lookup(element, points)


def pulse(model, volume, first_pulse=0.0, interval=0.0):
    _check_operands(volume, first_pulse, interval)
    return Pulse(model, volume, first_pulse, interval)


def trend(model, input_function, averaging_time, initial_trend=0.0):
    # The third argument is the trend to start with, as in XMILE - not the starting value of
    # the internal average, which it was until 3.4.0.
    _check_operands(initial_trend)
    return Trend(model, input_function, averaging_time, initial_trend)


def smooth(model, input_function, averaging_time, initial_value=None):
    # Without an initial value the average starts at the input, as XMILE's SMTH1 does.
    _check_operands(initial_value)
    return Smooth(model, input_function, averaging_time, initial_value)


def _check_order(order):
    # Stella truncates an order outside 1..255 without a word; here it is a mistake.
    if isinstance(order, bool) or not isinstance(order, int) or not 1 <= order <= 255:
        raise OperatorError("The order must be a whole number between 1 and 255")


def smooth3(model, input_function, averaging_time, initial_value=None):
    # XMILE's SMTH3: three first-order smooths in a row
    _check_operands(initial_value)
    return SmoothN(model, input_function, averaging_time, 3, initial_value)


def smoothn(model, input_function, averaging_time, order, initial_value=None):
    # XMILE's SMTHN; a stage never shorter than dt, as in Stella
    _check_operands(initial_value)
    _check_order(order)
    return SmoothN(model, input_function, averaging_time, order, initial_value,
                   floor_at_dt=True)


def delay1(model, input_function, delay_time, initial_value=None):
    # XMILE's DELAY1: a first-order material delay
    _check_operands(initial_value)
    return MaterialDelay(model, input_function, delay_time, 1, initial_value)


def delay3(model, input_function, delay_time, initial_value=None):
    # XMILE's DELAY3: three first-order material delays in a row
    _check_operands(initial_value)
    return MaterialDelay(model, input_function, delay_time, 3, initial_value)


def delayn(model, input_function, delay_time, order, initial_value=None):
    # XMILE's DELAYN; a stage never shorter than dt, as in Stella
    _check_operands(initial_value)
    _check_order(order)
    return MaterialDelay(model, input_function, delay_time, order, initial_value,
                         floor_at_dt=True)


def forecast(model, input_function, averaging_time, horizon, initial_trend=0.0):
    # XMILE's FORCST
    _check_operands(initial_trend)
    return Forecast(model, input_function, averaging_time, horizon, initial_trend)


def npv(model, input_function, rate, initial_value=None):
    # Stella's NPV
    _check_operands(initial_value)
    return Npv(model, input_function, rate, initial_value)


def step(height, timestep):  return Step(height, timestep)


def exp(x): return Exp(x)


def delay(model, input_function, delay_duration, initial_value=None):
    # The input's past is read from its own element, so an expression gets one
    _check_operands(input_function, delay_duration, initial_value)
    return Delay(model, _as_element(model, input_function), delay_duration, initial_value)


def uniform(min_value=0, max_value=1, seed=None): return Random(min_value, max_value, seed)


def random(min_value=0, max_value=1, seed=None): return Random(min_value, max_value, seed)


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


def ln(x): return Ln(x)


def log10(x): return Log10(x)


def floor(x): return Floor(x)


def ceil(x): return Ceil(x)


def trunc(x): return Trunc(x)


def sinwave(amplitude, period): return Sinwave(amplitude, period)


def coswave(amplitude, period): return Coswave(amplitude, period)


def Inf(): return _InfOp()


def pi(): return Pi()


"""
Statistical Functions
"""


def beta(a, b, seed=None): return Beta(a, b, seed)


def binomial(n, p, seed=None): return Binomial(n, p, seed)


def negbinomial(n, p, seed=None): return NegBinomial(n, p, seed)


def combinations(n, r): return Combinations(n, r)


def exprnd(l, seed=None): return Exprnd(l, seed)


def factorial(n): return Factorial(n)


def gamma(n, scale=1, seed=None): return Gamma(n, scale, seed)


def gammaln(n): return GammaLN(n)


def geometric(p, seed=None): return Geometric(p, seed)


def invnorm(p, mean=None, stddev=None): return Invnorm(p, mean, stddev)


def logistic(mean, scale, seed=None): return Logistic(mean, scale, seed)


def lognormal(mean, stddev, seed=None): return Lognormal(mean, stddev, seed)


def montecarlo(p, seed=None): return Montecarlo(p, seed)


def normal(mean, stddev, seed=None): return Normal(mean, stddev, seed)


def normalcdf(left, right, mean=0, stddev=1): return NormalCDF(left, right, mean, stddev)


def pareto(shape, scale, seed=None): return Pareto(shape, scale, seed)


def permutations(n, r): return Permutations(n, r)


def poisson(mu, seed=None): return Poisson(mu, seed)


def triangular(lower_bound, mode, upper_bound, seed=None): return Triangular(lower_bound, mode, upper_bound, seed)

def weibull(shape, scale, seed=None): return Weibull(shape, scale, seed)