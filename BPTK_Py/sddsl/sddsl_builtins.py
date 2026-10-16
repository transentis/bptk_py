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


# name -> (parameter names, the reason the arguments are invalid or None, the computation)
BUILTINS = {
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
        lambda rng, shape, scale: rng.pareto(shape) * scale),
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
    "weibull": (
        ("shape", "scale"),
        lambda shape, scale: ("shape and scale must be positive"
                              if shape <= 0 or scale <= 0 else None),
        lambda rng, shape, scale: rng.weibull(shape) * scale),
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


def _generator(model, name, t, seed, cell):
    """A generator of its own for one draw, made from the seed, the step and the cell.

    Nothing is carried from one step to the next, so a draw is the same whatever order the
    model is evaluated in, and a run resumed or cloned draws what the original did. The
    cell's position is part of it, so that the cells of an array draw independently.
    """
    if not math.isfinite(seed) or seed < 0 or seed != int(seed):
        model.report_invalid_argument(
            name, t, "seed must be a whole number of at least 0", ("seed",), (seed,))
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
    parameters, invalid, _ = BUILTINS[builtin]
    log(invalid_argument_message(builtin, element, t, invalid(*values), parameters, values))


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


def lookup_inverse(model, y, points):
    # Stella's LOOKUPINV: the x at which the table reaches y. Meant for a monotonic
    # table; on a segment that reaches y the x is interpolated, the first such segment
    # counts. A y outside what the table reaches gives the x of the end nearer to it.
    points = model._lookup_table(points)
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if min(y0, y1) <= y <= max(y0, y1):
            return float(x0 if y0 == y1 else x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    first, last = points[0], points[-1]
    return float(first[0] if abs(y - first[1]) <= abs(y - last[1]) else last[0])


def lookup_area(model, points, from_x=None, to_x=None):
    # Stella's LOOKUPAREA: the area under the table between from_x and to_x, the
    # whole table when they are left out. Beyond its ends a table holds its end
    # values, as lookup does; from_x above to_x gives the area with its sign turned.
    table = model._lookup_table(points)
    start = table[0][0] if from_x is None else from_x
    end = table[-1][0] if to_x is None else to_x
    if start > end:
        return -lookup_area(model, points, end, start)
    xs = [start] + [x for x, _ in table if start < x < end] + [end]
    ys = [model._lookup(x, points) for x in xs]
    return float(sum((x1 - x0) * (y0 + y1) / 2.0
                     for x0, x1, y0, y1 in zip(xs, xs[1:], ys, ys[1:])))


def rank(model, t, values, rank, tiebreak=None):
    # XMILE's RANK: the position of the rank-th smallest value, counting from 0. Equal
    # values are ordered by the tiebreak values, then by position.
    if not (math.isfinite(rank) and rank == int(rank) and 1 <= rank <= len(values)):
        model.report_invalid_argument(
            "rank", t, "rank must be a whole number from 1 to {}".format(len(values)),
            ("rank",), (rank,))
        return float("nan")
    breaks = tiebreak if tiebreak is not None else [0.0] * len(values)
    order = sorted(range(len(values)), key=lambda position: (values[position], breaks[position], position))
    return float(order[int(rank) - 1])


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
