#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018-2026 transentis labs GmbH
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


def _run(statistic, model, variable, from_time, to_time):
    return RunStatistic(statistic, _as_element(model, variable), from_time, to_time)


def runcum(model, variable, from_time=None, to_time=None):
    # Stella's RUNCUM: the sum of value times DT from from_time to to_time, the start and
    # the current time when left out, both included
    return _run("cum", model, variable, from_time, to_time)


def runmax(model, variable, from_time=None, to_time=None):
    # Stella's RUNMAX: the largest value so far, or within the window
    return _run("max", model, variable, from_time, to_time)


def runmin(model, variable, from_time=None, to_time=None):
    # Stella's RUNMIN: the smallest value so far, or within the window
    return _run("min", model, variable, from_time, to_time)


def runmean(model, variable, from_time=None, to_time=None):
    # Stella's RUNMEAN: the mean of the values so far, or within the window
    return _run("mean", model, variable, from_time, to_time)


def runcumtarget(model, variable, target):
    # Stella's RUNCUMTARGET: the time at which the running sum of the magnitude reaches target
    return RunCumTarget(_as_element(model, variable), target)


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


LOOKUP_KINDS = ("continuous", "extrapolate", "discrete")


def _check_kind(kind):
    # XMILE's three types of graphical function; the standard has no other
    if kind not in LOOKUP_KINDS:
        raise OperatorError("kind must be one of {}, not {!r}".format(", ".join(LOOKUP_KINDS), kind))


def lookupinv(value, points, kind="continuous"):
    # Stella's LOOKUPINV, for a monotonic table: the x at which it reaches value
    _check_kind(kind)
    return LookupInverse(value, points, kind)


def agecount(conveyor, minimum, maximum=None):
    # Stella's AGECOUNT: what has been on the conveyor at least minimum, less than maximum;
    # without a maximum everything from minimum on
    if not getattr(conveyor, "_is_conveyor", False):
        raise OperatorError("agecount counts the material on a conveyor; {} is not one.".format(
            getattr(conveyor, "name", conveyor)))
    return AgeCount(conveyor, minimum, maximum)


def lookuparea(points, from_x=None, to_x=None, kind="continuous"):
    # Stella's LOOKUPAREA: the area under the table, between from_x and to_x if given
    _check_kind(kind)
    return LookupArea(points, from_x, to_x, kind)


def lookupmax(points, from_x=None, to_x=None, kind="continuous"):
    # Stella's LOOKUPMAX: the largest value of the table between from_x and to_x, in either
    # order, or over the whole table; Stella gives the two bounds the other way round
    _check_kind(kind)
    return LookupStatistic("max", points, from_x, to_x, kind)


def lookupmin(points, from_x=None, to_x=None, kind="continuous"):
    # Stella's LOOKUPMIN: the smallest value of the table, as lookupmax
    _check_kind(kind)
    return LookupStatistic("min", points, from_x, to_x, kind)


def lookupmean(points, from_x=None, to_x=None, kind="continuous"):
    # Stella's LOOKUPMEAN: the table read as a density, its mean x - the expected value of
    # what LOOKUPRANDOM draws from it
    _check_kind(kind)
    return LookupStatistic("mean", points, from_x, to_x, kind)


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


def isnan(x):
    # Stella's ISNAN: 1 where x is NaN, 0 otherwise - NaN is the one value unequal to itself
    x = _operand(x)
    return If(x != x, 1.0, 0.0)


def rework(percentage):
    # Stella's REWORK: the leakage fraction that sends back `percentage` percent of all the
    # work, not of each pass
    percentage = _operand(percentage)
    return percentage / (100.0 + percentage)


def expbound(y_from, y_to, x, exponent, x_start, x_finish):
    # Stella's EXPBOUND: y_from up to x_start, y_to from x_finish on, and between them an
    # exponential curve - rising slowly first for a positive exponent, fast for a negative
    # one, a straight line for 0
    y_from, y_to, x, exponent = _operand(y_from), _operand(y_to), _operand(x), _operand(exponent)
    x_start, x_finish = _operand(x_start), _operand(x_finish)
    fraction = (x - x_start) / (x_finish - x_start)
    shape = If(exponent == 0.0, fraction,
               (Exp(exponent * fraction) - 1.0) / If(exponent == 0.0, 1.0, Exp(exponent) - 1.0))
    return If(x <= x_start, y_from,
              If(x >= x_finish, y_to, y_from + (y_to - y_from) * shape))


def logisticbound(y_from, y_to, x, x_middle, speed, x_start=None, x_finish=None):
    # Stella's LOGISTICBOUND: an S-curve from y_from to y_to, halfway at x_middle. With
    # x_start and x_finish it reaches y_from and y_to there exactly and holds them beyond:
    # each half is corrected by a straight line, so a speed of 0 gives two straight lines
    if (x_start is None) != (x_finish is None):
        raise OperatorError("logisticbound takes x_start and x_finish together, or neither.")
    y_from, y_to, x = _operand(y_from), _operand(y_to), _operand(x)
    x_middle, speed = _operand(x_middle), _operand(speed)

    def curve(at):
        return y_from + (y_to - y_from) / (1.0 + Exp(-speed * (at - x_middle)))

    if x_start is None:
        return curve(x)
    x_start, x_finish = _operand(x_start), _operand(x_finish)
    lower = curve(x) - (curve(x_start) - y_from) * (x_middle - x) / (x_middle - x_start)
    upper = curve(x) + (y_to - curve(x_finish)) * (x - x_middle) / (x_finish - x_middle)
    return If(x <= x_start, y_from,
              If(x >= x_finish, y_to,
                 If(x <= x_middle, lower, upper)))


def maxsoft(x, y, softness):
    # Stella's MAXSOFT: x once it lies at least softness above y, and below that a curve
    # that approaches y; a softness of 0 is the plain maximum
    x, y, softness = _operand(x), _operand(y), _operand(softness)
    soft = y + 2.0 * softness / (
        1.0 + Exp(2.0 * (1.0 - (x - y) / If(softness == 0.0, 1.0, softness))))
    return If(softness == 0.0, MaxOperator(x, y),
              If(x >= y + softness, x, soft))


def minsoft(x, y, softness):
    # Stella's MINSOFT: MAXSOFT mirrored - x once it lies at least softness below y
    return -maxsoft(-_operand(x), -_operand(y), softness)


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


def lookup(element, points, kind="continuous"):
    # The type of the table is XMILE's attribute of the graphical function; here it is
    # given where the table is read
    _check_kind(kind)
    return Lookup(element, points, kind)


def pulse(model, volume, first_pulse=None, interval=0.0):
    # Without a first pulse the pulse fires at STARTTIME, once unless an interval is given -
    # as the XMILE standard has it. Stella pulses at every DT instead.
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


def uniform(min_value=0, max_value=1, seed=None, minimum=None, maximum=None, sample=None):
    return Random(min_value, max_value, seed, minimum, maximum, sample)


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


def beta(a, b, seed=None, minimum=None, maximum=None, sample=None):
    return Beta(a, b, seed, minimum, maximum, sample)


def binomial(n, p, seed=None, minimum=None, maximum=None, sample=None):
    return Binomial(n, p, seed, minimum, maximum, sample)


def negbinomial(n, p, seed=None, minimum=None, maximum=None, sample=None):
    return NegBinomial(n, p, seed, minimum, maximum, sample)


def combinations(n, r): return Combinations(n, r)


def exprnd(l, seed=None, minimum=None, maximum=None, sample=None):
    return Exprnd(l, seed, minimum, maximum, sample)


def factorial(n): return Factorial(n)


def gamma(n, scale=1, seed=None, minimum=None, maximum=None, sample=None):
    return Gamma(n, scale, seed, minimum, maximum, sample)


def gammaln(n): return GammaLN(n)


def geometric(p, seed=None, minimum=None, maximum=None, sample=None):
    return Geometric(p, seed, minimum, maximum, sample)


def invnorm(p, mean=None, stddev=None): return Invnorm(p, mean, stddev)


def logistic(mean, scale, seed=None, minimum=None, maximum=None, sample=None):
    return Logistic(mean, scale, seed, minimum, maximum, sample)


def lognormal(mean, stddev, seed=None, minimum=None, maximum=None, sample=None):
    return Lognormal(mean, stddev, seed, minimum, maximum, sample)


def montecarlo(p, seed=None, minimum=None, maximum=None, sample=None):
    return Montecarlo(p, seed, minimum, maximum, sample)


def normal(mean, stddev, seed=None, minimum=None, maximum=None, sample=None):
    return Normal(mean, stddev, seed, minimum, maximum, sample)


def normalpink(model, mean, stddev, correlation_time, seed=None, minimum=None, maximum=None, sample=None):
    # Stella's NORMALPINK: normal noise, smoothed - each step the previous value moves the
    # share DT / correlation_time, at most all of it, towards a new normal draw, starting
    # from the mean. The draw's spread makes the noise's own stddev `stddev`. Bounds hold
    # the noise, not the draw: the draw is made again until the new value lies within
    # them. With a sample the noise moves one step per sample and holds in between.
    mean, stddev = _operand(mean), _operand(stddev)
    share = min(DT(model) / _operand(correlation_time), 1.0)
    noise = model.converter(model.equation_prefix + "normalpink")
    # Shaped as the arguments first: the previous value refers to its cells
    noise.equation = mean + 0.0 * stddev * share
    before = previous(model, noise, mean)

    def bound(limit):
        return None if limit is None else (_operand(limit) - (1.0 - share) * before) / share

    drawn = model.converter(model.equation_prefix + "normalpink_draw")
    drawn.equation = Normal(mean, stddev * Sqrt(2.0 / share - 1.0), seed, bound(minimum), bound(maximum), sample)
    moved = (1.0 - share) * before + share * drawn
    # A held draw changes only where a sample begins: the noise moves there alone
    noise.equation = moved if sample is None else If(drawn != previous(model, drawn, Nan()), moved, before)
    return noise


def lookuprandom(points, seed=None, minimum=None, maximum=None, sample=None):
    # Stella's LOOKUPRANDOM: a draw from the table read as a density, as LOOKUPMEAN reads it
    return LookupRandom(points, seed, minimum, maximum, sample)


def normalcdf(left, right, mean=0, stddev=1): return NormalCDF(left, right, mean, stddev)


def pareto(shape, scale, seed=None, minimum=None, maximum=None, sample=None):
    return Pareto(shape, scale, seed, minimum, maximum, sample)


def permutations(n, r): return Permutations(n, r)


def poisson(mu, seed=None, minimum=None, maximum=None, sample=None):
    return Poisson(mu, seed, minimum, maximum, sample)


def triangular(lower_bound, mode, upper_bound, seed=None, minimum=None, maximum=None, sample=None):
    return Triangular(lower_bound, mode, upper_bound, seed, minimum, maximum, sample)

def weibull(shape, scale, seed=None, minimum=None, maximum=None, sample=None):
    return Weibull(shape, scale, seed, minimum, maximum, sample)
