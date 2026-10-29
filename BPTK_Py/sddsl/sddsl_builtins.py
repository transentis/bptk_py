#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2026 transentis labs GmbH
# MIT License

"""The builtins of the SD DSL on the Python engine: what an equation's term calls at run time.

The counterpart of the Rust engine's `src/builtins.rs`. Most come from XMILE or Stella - the
statistical ones with the table of the arguments each accepts, and RANK, INTERPOLATE, IRR,
LOOKUPINV and LOOKUPAREA as functions of their own.

The term of every entry renders a call to `evaluate`, so that each argument is evaluated
exactly once - a check and a draw that each evaluated an argument of their own looked at
two different numbers whenever that argument was itself random.

An argument outside what a builtin accepts gives NaN, and the model reports it once per
element: the run goes on, the gap it leaves in the series is explained. A NaN or an
infinity that arrives as an argument gives NaN without a report - it is the result of
something upstream, a division by zero or an overflow, which is not this builtin's error.

The same table exists in the Rust engine (`src/builtins.rs`); the wording of the report is
made here for both, so they cannot drift apart.
"""
import math
import random

import numpy as np
import scipy.special
from scipy.optimize import brentq
from scipy.stats import norm

from ..util import floating_point as fp


# The largest count a counting distribution is asked for: numpy refuses a Poisson rate
# above about 9.22e18, and a count beyond it no longer fits the integers it is drawn as.
# The Rust engine uses the same bound.
LARGEST_COUNT = 9.2e18


def _triangular(rng, lower, mode, upper):
    if lower == mode == upper:
        return lower
    return rng.triangular(lower, mode, upper)


def _underlying_normal(mean, stddev):
    """The mean and stddev of the normal distribution whose exponential has the given
    mean and stddev."""
    variance = math.log1p((stddev / mean) ** 2)
    return math.log(mean) - variance / 2, math.sqrt(variance)


def _whole(value):
    return value >= 0 and value == int(value)


def _falling_product(n, count):
    """n * (n - 1) * ... over `count` factors, multiplied in this order - the Rust engine
    multiplies in the same order, so large results agree to the last bit. Past the range
    of a float the product is infinity, and the loop ends there."""
    result = 1.0
    for i in range(int(count)):
        result *= n - i
        if math.isinf(result):
            break
    return result


def _choose(n, r):
    """n over r, built up factor by factor as the Rust engine does: each step is a whole
    number again, so the result stays exact while it fits, and the loop ends at infinity."""
    k = min(r, n - r)
    result = 1.0
    for i in range(1, int(k) + 1):
        result = result * (n - k + i) / i
        if math.isinf(result):
            break
    return result


# name -> (parameter names, the reason the arguments are invalid or None, the computation)
def flat_table(model, points):
    # A lookup table as one list of numbers, x and y by turns - the arguments a draw takes
    return [float(number) for point in model._lookup_table(points) for number in point]


_TABLE_REASON = "the table must not be negative anywhere and must have an area"


def _table_reason(*flat):
    ys = flat[1::2]
    area = sum((x1 - x0) * (y0 + y1) / 2.0 for x0, x1, y0, y1 in zip(flat[0::2], flat[2::2], ys, ys[1:]))
    return _TABLE_REASON if min(ys) < 0.0 or not area > 0.0 else None


def _lookup_random(rng, *flat):
    # A segment chosen by its area, then a point uniformly within it - one uniform draw
    # does both, by walking the areas until it is used up
    xs, ys = flat[0::2], flat[1::2]
    areas = [(x1 - x0) * (y0 + y1) / 2.0 for x0, x1, y0, y1 in zip(xs, xs[1:], ys, ys[1:])]
    rest = rng.uniform(0.0, 1.0) * sum(areas)
    for x0, x1, area in zip(xs, xs[1:], areas):
        if area > 0.0 and rest < area:
            return float(x0 + rest / area * (x1 - x0))
        rest -= area
    return float(xs[-1])


BUILTINS = {
    # The table's points, x and y by turns: no names of their own in a report
    "lookuprandom": ((), _table_reason, _lookup_random),
    "uniform": (
        ("min_value", "max_value"),
        lambda lo, hi: "min_value must not be greater than max_value" if lo > hi else None,
        lambda rng, lo, hi: random.uniform(lo, hi) if rng is np.random else rng.uniform(lo, hi)),
    "normal": (
        ("mean", "stddev"),
        lambda mean, stddev: "stddev must not be negative" if stddev < 0 else None,
        lambda rng, mean, stddev: rng.normal(mean, stddev)),
    # XMILE's mean and stddev are those of the distribution itself; numpy takes the
    # parameters of the normal distribution underneath, so they are converted first.
    "lognormal": (
        ("mean", "stddev"),
        lambda mean, stddev: ("mean must be positive" if mean <= 0
                              else "stddev must not be negative" if stddev < 0 else None),
        lambda rng, mean, stddev: rng.lognormal(*_underlying_normal(mean, stddev))),
    "logistic": (
        ("mean", "scale"),
        lambda mean, scale: "scale must not be negative" if scale < 0 else None,
        lambda rng, mean, scale: rng.logistic(mean, scale)),
    "beta": (
        ("a", "b"),
        lambda a, b: "a and b must be positive" if a <= 0 or b <= 0 else None,
        lambda rng, a, b: rng.beta(a, b)),
    "binomial": (
        ("n", "p"),
        lambda n, p: ("n must not be negative" if n < 0
                      else "n must not exceed 9.2e18" if n > LARGEST_COUNT
                      else "p must lie between 0 and 1" if p < 0 or p > 1 else None),
        lambda rng, n, p: rng.binomial(n, p)),
    "negbinomial": (
        ("n", "p"),
        lambda n, p: ("n must be positive" if n <= 0
                      else "n must not exceed 9.2e18" if n > LARGEST_COUNT
                      else "p must be greater than 0 and at most 1" if p <= 0 or p > 1
                      else None),
        lambda rng, n, p: rng.negative_binomial(n, p)),
    "exprnd": (
        ("l",),
        lambda l: "l must be positive" if l <= 0 else None,
        lambda rng, l: rng.exponential(l)),
    "gamma": (
        ("n", "scale"),
        lambda n, scale: "n and scale must be positive" if n <= 0 or scale <= 0 else None,
        lambda rng, n, scale: rng.gamma(n, scale)),
    "geometric": (
        ("p",),
        lambda p: "p must be greater than 0 and at most 1" if p <= 0 or p > 1 else None,
        lambda rng, p: rng.geometric(p)),
    "pareto": (
        ("shape", "scale"),
        lambda shape, scale: ("shape and scale must be positive"
                              if shape <= 0 or scale <= 0 else None),
        # Stella's help: the classic Pareto, starting at scale - numpy's pareto starts at 0
        lambda rng, shape, scale: (rng.pareto(shape) + 1.0) * scale),
    "poisson": (
        ("mu",),
        lambda mu: ("mu must not be negative" if mu < 0
                    else "mu must not exceed 9.2e18" if mu > LARGEST_COUNT else None),
        lambda rng, mu: rng.poisson(mu)),
    "triangular": (
        ("lower_bound", "mode", "upper_bound"),
        lambda lower, mode, upper: (
            "lower_bound <= mode <= upper_bound must hold"
            if lower > upper or mode < lower or mode > upper else None),
        _triangular),
    # 1 with the probability p percent - the caller has multiplied the probability per time
    # unit by dt already
    "montecarlo": (
        ("p",),
        lambda p: None,
        lambda rng, p: 1.0 if (random.uniform(0, 100) if rng is np.random else rng.uniform(0, 100)) < p else 0.0),
    "weibull": (
        ("shape", "scale"),
        lambda shape, scale: ("shape and scale must be positive"
                              if shape <= 0 or scale <= 0 else None),
        lambda rng, shape, scale: rng.weibull(shape) * scale),
    # Whole numbers of at least 0 only, as XMILE counts; computed as the Rust engine does,
    # one product step after another, so that both give the same number
    "factorial": (
        ("n",),
        lambda n: None if _whole(n) else "n must be a whole number of at least 0",
        lambda rng, n: _falling_product(n, n)),
    "combinations": (
        ("n", "r"),
        lambda n, r: None if _whole(n) and _whole(r) else "n and r must be whole numbers of at least 0",
        lambda rng, n, r: 0.0 if r > n else _choose(n, r)),
    "permutations": (
        ("n", "r"),
        lambda n, r: None if _whole(n) and _whole(r) else "n and r must be whole numbers of at least 0",
        lambda rng, n, r: 0.0 if r > n else _falling_product(n, r)),
    "delay": (
        ("delay_duration",),
        lambda duration: "delay_duration must not be negative" if duration < 0 else None,
        lambda rng, duration: duration),
    # The mathematical functions outside their domain: NaN and a report, where numpy and
    # the Rust engine give NaN without a word and Stella stops the run
    "sqrt": (("x",), lambda x: "x must not be negative" if x < 0 else None, lambda rng, x: math.sqrt(x)),
    "ln": (("x",), lambda x: "x must not be negative" if x < 0 else None,
           lambda rng, x: -math.inf if x == 0 else math.log(x)),
    "log10": (("x",), lambda x: "x must not be negative" if x < 0 else None,
              lambda rng, x: -math.inf if x == 0 else math.log10(x)),
    "arcsin": (("x",), lambda x: "x must lie between -1 and 1" if abs(x) > 1 else None, lambda rng, x: math.asin(x)),
    "arccos": (("x",), lambda x: "x must lie between -1 and 1" if abs(x) > 1 else None, lambda rng, x: math.acos(x)),
    "invnorm": (
        ("p", "mean", "stddev"),
        lambda p, mean, stddev: ("p must lie between 0 and 1" if p < 0 or p > 1
                                 else "stddev must be positive" if stddev <= 0 else None),
        lambda rng, p, mean, stddev: norm.ppf(p, mean, stddev)),
    "normalcdf": (
        ("left", "right", "mean", "stddev"),
        lambda left, right, mean, stddev: "stddev must be positive" if stddev <= 0 else None,
        lambda rng, left, right, mean, stddev: (norm(mean, stddev).cdf(right)
                                           - norm(mean, stddev).cdf(left))),
}


def evaluate(model, name, t, *args):
    """The value of builtin `name` for `args`, or NaN, reported, if it does not accept them."""
    return _evaluate(model, name, t, np.random, args)


def evaluate_seeded(model, name, t, seed, cell, *args):
    """As `evaluate`, drawing from the generator that `seed` gives for this step and cell."""
    rng = _generator(model, name, t, seed, cell)
    if rng is None:
        return np.nan
    return _evaluate(model, name, t, rng, args)


def montecarlo_seeded(model, t, seed, cell, p):
    """MONTECARLO with a seed: 1 with a probability of `p` percent per time unit, else 0."""
    rng = _generator(model, "montecarlo", t, seed, cell)
    if rng is None:
        return np.nan
    return 1 if rng.uniform(0, 100) < p * model.dt else 0


def _evaluate(model, name, t, rng, args):
    parameters, invalid, compute = BUILTINS[name]
    if not all(math.isfinite(arg) for arg in args):
        return np.nan
    reason = invalid(*args)
    if reason is not None:
        model.report_invalid_argument(name, t, reason, parameters, args)
        return np.nan
    return compute(rng, *args)


_SEED_REASON = "seed must be a whole number of at least 0"

# Stella draws again until a value lies within the bounds - and after 100 draws gives up and
# draws uniformly between them; the SD DSL gives NaN and a report there instead
DRAWS_WITHIN_BOUNDS = 100
_BOUNDS_PARAMETERS = ("minimum", "maximum")
_REVERSED_REASON = "minimum must not be greater than maximum"
_MISSED_REASON = "no draw lies within minimum and maximum in {} draws".format(DRAWS_WITHIN_BOUNDS)


def sample_start(model, t, sample):
    """The time the sample that `t` lies in began: the sample is cut down to a whole number
    of steps, as Stella does, and counted from the start; one under a step is every step."""
    steps = math.floor(sample / model.dt + 1e-9) if math.isfinite(sample) else 0
    if steps <= 1:
        return t
    step = round((t - model.starttime) / model.dt)
    return model.starttime + (step - step % steps) * model.dt


def draw(model, name, t, seed, cell, site, minimum, maximum, *args):
    """A draw with bounds or a sample: drawn again until it lies within minimum and maximum,
    both included - NaN and a report when no draw of 100 does, as when minimum is greater
    than maximum; equal bounds give that value. NaN as a bound is no bound. `t` is the
    time the sample began; an unseeded draw is kept under `site` until the next one."""
    key = (site, tuple(cell), t)
    if site is not None and key in model._held_draws:
        return model._held_draws[key]
    value = _bounded(model, name, t, seed, cell, minimum, maximum, args)
    if site is not None:
        model._held_draws[key] = value
    return value


def _bounded(model, name, t, seed, cell, minimum, maximum, args):
    lower = -math.inf if math.isnan(minimum) else minimum
    upper = math.inf if math.isnan(maximum) else maximum
    if lower > upper:
        model.report_invalid_argument(name, t, _REVERSED_REASON, _BOUNDS_PARAMETERS, (minimum, maximum))
        return np.nan
    if lower == upper:
        return float(lower)
    rng = np.random if seed is None else _generator(model, name, t, seed, cell)
    if rng is None:
        return np.nan
    for _ in range(DRAWS_WITHIN_BOUNDS):
        value = _evaluate(model, name, t, rng, args)
        if not lower <= value <= upper:
            if value != value:
                return np.nan
            continue
        return value
    model.report_invalid_argument(name, t, _MISSED_REASON, _BOUNDS_PARAMETERS, (minimum, maximum))
    return np.nan


def _generator(model, name, t, seed, cell):
    """A generator of its own for one draw, made from the seed, the step and the cell.

    Nothing is carried from one step to the next, so a draw is the same whatever order the
    model is evaluated in, and a run resumed or cloned draws what the original did. The
    cell's position is part of it, so that the cells of an array draw independently.
    """
    if not math.isfinite(seed) or seed < 0 or seed != int(seed):
        model.report_invalid_argument(name, t, _SEED_REASON, ("seed",), (seed,))
        return None
    step = round((t - model.starttime) / model.dt)
    return np.random.default_rng([int(seed), step & 0xFFFFFFFFFFFFFFFF, len(cell), *cell])


def invalid_argument_message(name, element, t, reason, parameters, values):
    """The `[ERROR]` line for an invalid argument, the same for both engines."""
    arguments = ", ".join(
        "{}={}".format(parameter, float(value)) for parameter, value in zip(parameters, values))
    return ("[ERROR] {} in '{}' at t={}: {} ({}). The result is NaN wherever the "
            "arguments are invalid; later occurrences in '{}' are not reported.".format(
                name, element, float(t), reason, arguments, element))


def report_from_engine(builtin, element, t, values):
    """Log an invalid argument the Rust engine recorded, in the Python engine's words.

    The engine only knows where and with what; the reason comes from the table above, so
    the rule and its wording exist once.
    """
    from ..logger import log
    if builtin == "division":
        log(division_by_zero_message(element, t))
        return
    if builtin.startswith("seed:"):
        name = builtin[len("seed:"):]
        log(invalid_argument_message(name, element, t, _SEED_REASON, ("seed",), values))
        return
    if builtin.startswith("bounds:"):
        name, reason = builtin[len("bounds:"):].split(":")
        log(invalid_argument_message(name, element, t, _REVERSED_REASON if reason == "reversed" else _MISSED_REASON,
                                     _BOUNDS_PARAMETERS, values))
        return
    if builtin == "arr_rank":
        # The engine sends the rank and the number of values it ranks
        rank, count = values
        log(invalid_argument_message("arr_rank", element, t, _rank_reason(int(count)), ("rank",), (rank,)))
        return
    if builtin == "lookuprandom":
        log(invalid_argument_message(builtin, element, t, _TABLE_REASON, (), ()))
        return
    if builtin == "arr_percentile":
        log(invalid_argument_message(builtin, element, t, _percentile_reason(*values),
                                     _PERCENTILE_PARAMETERS, values))
        return
    parameters, invalid, _ = BUILTINS[builtin]
    log(invalid_argument_message(builtin, element, t, invalid(*values), parameters, values))


def _run_times(model, t, from_time, to_time):
    # The times of the steps from from_time to to_time, both included and none after t.
    # The bounds are read in steps, a millionth of a step to spare, so that TIME - 2 meets
    # the step it means
    def step_of(time, rounding, spare):
        # An infinite bound stays infinite: before the start, or after the current time
        return rounding((time - model.starttime) / model.dt + spare) if math.isfinite(time) else time

    times = fp.timerange(model.starttime, t, model.dt, exclusive=False)
    first = max(0.0, step_of(from_time, math.ceil, -1e-6))
    last = min(len(times) - 1.0, step_of(to_time, math.floor, 1e-6))
    return times[int(first):int(last) + 1] if first <= last else []


def run_statistic(model, statistic, stream, t, from_time, to_time):
    # Stella's RUNCUM, RUNMAX, RUNMIN and RUNMEAN over the steps from from_time to to_time,
    # the current one included: RUNCUM sums value times DT, RUNMEAN is the mean of the
    # values. A window without a step gives NaN.
    if from_time != from_time or to_time != to_time:
        return float("nan")
    times = _run_times(model, t, from_time, to_time)
    if len(times) == 0:
        return float("nan")
    values = [model.memoize(stream, time) for time in times]
    if statistic == "cum":
        total = 0.0
        for value in values:
            total += value * model.dt
        return float(total)
    if statistic == "max":
        return float(max(values))
    if statistic == "min":
        return float(min(values))
    total = 0.0
    for value in values:
        total += value
    return float(total / len(values))


def run_cum_target(model, stream, t, target):
    # Stella's RUNCUMTARGET: at the first step where the running sum of the stream's
    # magnitude times DT reaches the target, that step's time plus the share of the step
    # the rest of the target takes; NaN before, the same time after. Stella sums the
    # magnitude, unlike RUNCUM.
    if target != target:
        return float("nan")
    total = 0.0
    for time in _run_times(model, t, -math.inf, math.inf):
        rate = abs(model.memoize(stream, time))
        before, total = total, total + rate * model.dt
        if total >= target:
            return float(time + (target - before) / rate if rate > 0.0 else time)
    return float("nan")


def irr(model, stream, t, missing):
    # Stella's IRR: the rate r at which the stream's values from STARTTIME to t,
    # one per dt and each discounted by (1 + r)^(time - STARTTIME), sum to zero.
    # Several rates can do that when the stream changes sign more than once; the one
    # nearest zero is taken, and `missing` when there is none - as Stella does.
    times = fp.timerange(model.starttime, t, model.dt, exclusive=False)
    if len(times) < 2:
        return missing
    values = np.array([model.memoize(stream, time) for time in times])
    exponents = np.array(times) - model.starttime

    def npv(rate):
        return float(np.sum(values / (1.0 + rate) ** exponents))

    candidates = np.concatenate([np.linspace(-0.99, 1.0, 400), np.linspace(1.0, 10.0, 91)[1:]])
    with np.errstate(all="ignore"):
        npvs = [npv(rate) for rate in candidates]
    roots = []
    for low, high, a, b in zip(candidates, candidates[1:], npvs, npvs[1:]):
        # A root inside the interval or on one of its ends; a stream of zeros has none
        if np.isfinite(a) and np.isfinite(b) and a * b <= 0.0 and (a != 0.0 or b != 0.0):
            roots.append(brentq(npv, low, high))
    if not roots:
        return missing
    return float(min(roots, key=abs))


def lookup_inverse(model, y, points, kind="continuous"):
    # Stella's LOOKUPINV: the x at which the table reaches y. Meant for a monotonic
    # table; on a segment that reaches y the x is interpolated, the first such segment
    # counts. A y outside what the table reaches gives the x of the end nearer to it -
    # on a monotonic table; on one that is not, NaN, as in Stella. An extrapolate table
    # goes on along that end's segment; a discrete one is read as continuous, as Stella does.
    points = model._lookup_table(points)
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if min(y0, y1) <= y <= max(y0, y1):
            return float(x0 if y0 == y1 else x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    ys = [point[1] for point in points]
    rises = all(a <= b for a, b in zip(ys, ys[1:]))
    falls = all(a >= b for a, b in zip(ys, ys[1:]))
    if not (rises or falls):
        return float("nan")
    first, last = points[0], points[-1]
    nearer_first = abs(y - first[1]) <= abs(y - last[1])
    if kind == "extrapolate" and len(points) > 1:
        (x0, y0), (x1, y1) = (points[0], points[1]) if nearer_first else (points[-2], points[-1])
        if y0 != y1:
            return float(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return float(first[0] if nearer_first else last[0])


def lookup_area(model, points, from_x=None, to_x=None, kind="continuous"):
    # Stella's LOOKUPAREA: the area under the table between from_x and to_x, the
    # whole table when they are left out or infinite. As in Stella, nothing beyond the
    # table's ends counts, though lookup holds the end values there - except on an
    # extrapolate table, whose lines go on; a discrete table's steps are integrated as
    # steps. from_x above to_x gives the area with its sign turned.
    table = model._lookup_table(points)
    if (from_x is not None and from_x != from_x) or (to_x is not None and to_x != to_x):
        return float("nan")
    start = table[0][0] if from_x is None or from_x == -math.inf else from_x
    end = table[-1][0] if to_x is None or to_x == math.inf else to_x
    if start > end:
        return -lookup_area(model, points, end, start, kind)
    if kind != "extrapolate":
        start, end = max(start, table[0][0]), min(end, table[-1][0])
    if start >= end:
        return 0.0
    xs = [start] + [x for x, _ in table if start < x < end] + [end]
    ys = [model._lookup(x, points, kind) for x in xs]
    if kind == "discrete":
        return float(sum((x1 - x0) * y0 for x0, x1, y0 in zip(xs, xs[1:], ys)))
    return float(sum((x1 - x0) * (y0 + y1) / 2.0
                     for x0, x1, y0, y1 in zip(xs, xs[1:], ys, ys[1:])))


def lookup_statistic(model, statistic, points, from_x=None, to_x=None, kind="continuous"):
    # Stella's LOOKUPMAX, LOOKUPMIN and LOOKUPMEAN between from_x and to_x, the whole table
    # when they are left out or infinite, in either order. The largest and the smallest
    # value read the table as lookup does, beyond its ends too. The mean is the mean x of
    # the table read as a density - each segment uniform, weighted by its area, as
    # LOOKUPRANDOM draws from it - so nothing beyond the ends counts but on an extrapolate
    # table; a range without area gives NaN.
    table = model._lookup_table(points)
    if (from_x is not None and from_x != from_x) or (to_x is not None and to_x != to_x):
        return float("nan")
    start = table[0][0] if from_x is None or from_x == -math.inf else from_x
    end = table[-1][0] if to_x is None or to_x == math.inf else to_x
    start, end = min(start, end), max(start, end)
    if statistic == "mean" and kind != "extrapolate":
        start, end = max(start, table[0][0]), min(end, table[-1][0])
    xs = [start] + [x for x, _ in table if start < x < end] + ([end] if end > start else [])
    ys = [model._lookup(x, points, kind) for x in xs]
    if statistic == "max":
        return float(max(ys))
    if statistic == "min":
        return float(min(ys))
    areas = [(x1 - x0) * (y0 if kind == "discrete" else (y0 + y1) / 2.0)
             for x0, x1, y0, y1 in zip(xs, xs[1:], ys, ys[1:])]
    total = sum(areas)
    if total == 0.0:
        return float("nan")
    return float(sum(area * (x0 + x1) / 2.0 for area, x0, x1 in zip(areas, xs, xs[1:])) / total)


def _rank_reason(count):
    return "rank must be a whole number from 1 to {}".format(count)


def rank(model, t, values, rank, tiebreak=None):
    # XMILE's RANK: the position of the rank-th smallest value, counting from 1 as XMILE
    # and Stella do. Equal values are ordered by the tiebreak values, then by position.
    if not (math.isfinite(rank) and rank == int(rank) and 1 <= rank <= len(values)):
        model.report_invalid_argument("arr_rank", t, _rank_reason(len(values)), ("rank",), (rank,))
        return float("nan")
    breaks = tiebreak if tiebreak is not None else [0.0] * len(values)
    order = sorted(range(len(values)), key=lambda position: (values[position], breaks[position], position))
    return float(order[int(rank) - 1] + 1)


_PERCENTILE_PARAMETERS = ("percentile", "lower", "smallest weight", "total weight")


def _percentile_reason(percentile, lower, smallest_weight, total_weight):
    if not (0.0 <= percentile <= 100.0 and 0.0 <= lower <= 100.0):
        return "percentile and lower must lie between 0 and 100"
    if smallest_weight < 0.0 or total_weight <= 0.0:
        return "the weights must not be negative and not all 0"
    return None


def _percentile_at(sorted_values, sorted_weights, percentile):
    # Stella's two rules. Without weights: the rank percentile * (n - 1) / 100, a whole
    # rank giving its value, any other the mean of its two neighbours - a staircase. With
    # weights: each value at the middle of its weight, the mean of two neighbours at the
    # border between them, a straight line in between, held beyond the outer middles.
    count = len(sorted_values)
    if sorted_weights is None:
        rank = percentile / 100.0 * (count - 1)
        lower, upper = int(math.floor(rank)), int(math.ceil(rank))
        if lower == upper:
            return sorted_values[lower]
        return (sorted_values[lower] + sorted_values[upper]) / 2.0
    total = sum(sorted_weights)
    points, below = [], 0.0
    for position, (value, weight) in enumerate(zip(sorted_values, sorted_weights)):
        points.append(((below + weight / 2.0) / total * 100.0, value))
        below += weight
        if position < count - 1:
            points.append((below / total * 100.0, (value + sorted_values[position + 1]) / 2.0))
    if percentile <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if percentile <= x1:
            return y0 if x1 == x0 else y0 + (percentile - x0) / (x1 - x0) * (y1 - y0)
    return points[-1][1]


def percentile(model, t, values, percentile, lower=0.0, weights=None):
    # Stella's PERCENTILE: see `_percentile_at`; a lower percentile above 0 is taken off
    if any(value != value for value in values) or percentile != percentile or lower != lower:
        return float("nan")
    smallest = min(weights) if weights is not None else 1.0
    total = sum(weights) if weights is not None else 1.0
    reason = _percentile_reason(percentile, lower, smallest, total)
    if reason is not None:
        model.report_invalid_argument("arr_percentile", t, reason, _PERCENTILE_PARAMETERS,
                                      (percentile, lower, smallest, total))
        return float("nan")
    order = sorted(range(len(values)), key=lambda position: (values[position], position))
    sorted_values = [float(values[position]) for position in order]
    sorted_weights = None if weights is None else [float(weights[position]) for position in order]
    result = _percentile_at(sorted_values, sorted_weights, percentile)
    if lower > 0.0:
        result -= _percentile_at(sorted_values, sorted_weights, lower)
    return float(result)


def interpolate(values, columns, *weights):
    # Stella's INTERPOLATE: multilinear between the elements of a vector or a matrix,
    # each weight in [0, 1] - 0 is the first element of its dimension, 1 the last.
    if not all(math.isfinite(weight) for weight in weights):
        return float("nan")
    weights = [min(1.0, max(0.0, weight)) for weight in weights]

    def along(line, weight):
        if len(line) == 1:
            return float(line[0])
        position = weight * (len(line) - 1)
        lower = min(int(math.floor(position)), len(line) - 2)
        share = position - lower
        return float(line[lower] + share * (line[lower + 1] - line[lower]))

    if columns <= 0:
        return along(values, weights[0])
    rows = [values[start:start + columns] for start in range(0, len(values), columns)]
    return along([along(row, weights[1]) for row in rows], weights[0])


def maximum(a, b):
    # NaN in either gives NaN, as on the Rust engine: Python's max keeps the first argument
    # when a comparison with NaN fails, so max(nan, 1) and max(1, nan) differed
    return math.nan if math.isnan(a) or math.isnan(b) else max(a, b)


def minimum(a, b):
    return math.nan if math.isnan(a) or math.isnan(b) else min(a, b)


def division_by_zero_message(element, t):
    """The `[ERROR]` line for a division by zero, the same for both engines."""
    return ("[ERROR] division by zero in '{}' at t={}. The result is NaN wherever it divides "
            "by zero; later occurrences in '{}' are not reported.".format(element, float(t), element))


def divide(model, t, a, b):
    # NaN and one report per element for a divisor of 0, on both engines: Python raised
    # ZeroDivisionError for a float and gave inf for a numpy number, such as a draw of 0
    if b == 0:
        model.report_division_by_zero(t)
        return math.nan
    return a / b


def modulo(model, t, a, b):
    # Floored, as XMILE's MOD and the Rust engine
    if b == 0:
        model.report_division_by_zero(t)
        return math.nan
    return a % b


def power(model, t, a, b):
    # 0 to a negative power divides by zero. Otherwise C's pow, as on the Rust engine: a
    # negative base to a fractional power is NaN rather than Python's complex number, and
    # a result too large is infinity rather than OverflowError
    if a == 0 and b < 0:
        model.report_division_by_zero(t)
        return math.nan
    with np.errstate(all="ignore"):
        return float(np.power(float(a), float(b)))


def round_half_away(v, d=0):
    """Rounded to `d` digits, half away from zero - Python's round() rounds half to even.
    Compared on the fractional part, because floor(x + 0.5) turns 0.49999999999999994 into
    1. Digits beyond what a float holds leave the value as it is, or give 0 below it - as on
    the Rust engine."""
    if not math.isfinite(d):
        return math.nan
    if not math.isfinite(v) or d > 308:
        return v
    if d < -308:
        return 0.0
    factor = 10.0 ** d
    scaled = abs(v) * factor
    if math.isinf(scaled):
        return v
    whole = math.floor(scaled)
    return math.copysign(whole + (1.0 if scaled - whole >= 0.5 else 0.0), v) / factor


def largest(values, rank):
    # The rank-th largest value. A rank below 1 or beyond the values gives the smallest, a
    # fractional one is cut to a whole number, and NaN gives NaN - as on the Rust engine
    if math.isnan(rank):
        return math.nan
    ordered = sorted(values, reverse=True)
    return ordered[-1] if rank < 1 or rank > len(ordered) else ordered[int(rank) - 1]



def delay_lag(model, t, duration):
    """How far a delay reaches back: its duration in whole steps, half a step rounded up, as
    the Rust engine counts it - the time read before rounded half to even, so a duration of
    half a step reached back none, one, none, one step in turn. A negative duration would
    read the future: NaN, reported once. Infinity never arrives, NaN gives NaN unreported."""
    if duration < 0:
        parameters, invalid, _ = BUILTINS["delay"]
        model.report_invalid_argument("delay", t, invalid(duration), parameters, (duration,))
        return math.nan
    if not math.isfinite(duration):
        return duration
    steps = duration / model.dt
    whole = math.floor(steps)
    return (whole + (1 if steps - whole >= 0.5 else 0)) * model.dt


def gamma_ln(x):
    # As Stella: NaN for every argument of 0 and below, where gamma has poles and changes sign
    return math.nan if x <= 0 else float(scipy.special.gammaln(x))


def in_domain(model, name, t, x):
    """A mathematical function of one argument: NaN and a report for a finite argument
    outside its domain; an infinite one goes where the function takes it, unreported - a
    NaN or an infinity comes from further up the model."""
    parameters, invalid, compute = BUILTINS[name]
    if math.isnan(x):
        return math.nan
    if math.isinf(x):
        with np.errstate(all="ignore"):
            return float({"sqrt": np.sqrt, "ln": np.log, "log10": np.log10,
                          "arcsin": np.arcsin, "arccos": np.arccos}[name](x))
    reason = invalid(x)
    if reason is not None:
        model.report_invalid_argument(name, t, reason, parameters, (x,))
        return math.nan
    return compute(None, x)
