"""The statistical builtins of the SD DSL on the Python engine, with the arguments each accepts.

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
from scipy.stats import norm


# The largest count a counting distribution is asked for: numpy refuses a Poisson rate
# above about 9.22e18, and a count beyond it no longer fits the integers it is drawn as.
# The Rust engine uses the same bound.
LARGEST_COUNT = 9.2e18


def _triangular(lower, mode, upper):
    if lower == mode == upper:
        return lower
    return np.random.triangular(lower, mode, upper)


# name -> (parameter names, the reason the arguments are invalid or None, the computation)
BUILTINS = {
    "uniform": (
        ("min_value", "max_value"),
        lambda lo, hi: "min_value must not be greater than max_value" if lo > hi else None,
        lambda lo, hi: random.uniform(lo, hi)),
    "normal": (
        ("mean", "stddev"),
        lambda mean, stddev: "stddev must not be negative" if stddev < 0 else None,
        lambda mean, stddev: np.random.normal(mean, stddev)),
    "lognormal": (
        ("mean", "stddev"),
        lambda mean, stddev: "stddev must not be negative" if stddev < 0 else None,
        lambda mean, stddev: np.random.lognormal(mean, stddev)),
    "logistic": (
        ("mean", "scale"),
        lambda mean, scale: "scale must not be negative" if scale < 0 else None,
        lambda mean, scale: np.random.logistic(mean, scale)),
    "beta": (
        ("a", "b"),
        lambda a, b: "a and b must be positive" if a <= 0 or b <= 0 else None,
        lambda a, b: np.random.beta(a, b)),
    "binomial": (
        ("n", "p"),
        lambda n, p: ("n must not be negative" if n < 0
                      else "n must not exceed 9.2e18" if n > LARGEST_COUNT
                      else "p must lie between 0 and 1" if p < 0 or p > 1 else None),
        lambda n, p: np.random.binomial(n, p)),
    "negbinomial": (
        ("n", "p"),
        lambda n, p: ("n must be positive" if n <= 0
                      else "n must not exceed 9.2e18" if n > LARGEST_COUNT
                      else "p must be greater than 0 and at most 1" if p <= 0 or p > 1
                      else None),
        lambda n, p: np.random.negative_binomial(n, p)),
    "exprnd": (
        ("l",),
        lambda l: "l must be positive" if l <= 0 else None,
        lambda l: np.random.exponential(l)),
    "gamma": (
        ("n", "scale"),
        lambda n, scale: "n and scale must be positive" if n <= 0 or scale <= 0 else None,
        lambda n, scale: np.random.gamma(n, scale)),
    "geometric": (
        ("p",),
        lambda p: "p must be greater than 0 and at most 1" if p <= 0 or p > 1 else None,
        lambda p: np.random.geometric(p)),
    "pareto": (
        ("shape", "scale"),
        lambda shape, scale: ("shape and scale must be positive"
                              if shape <= 0 or scale <= 0 else None),
        lambda shape, scale: np.random.pareto(shape) * scale),
    "poisson": (
        ("mu",),
        lambda mu: ("mu must not be negative" if mu < 0
                    else "mu must not exceed 9.2e18" if mu > LARGEST_COUNT else None),
        lambda mu: np.random.poisson(mu)),
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
        lambda shape, scale: np.random.weibull(shape) * scale),
    "invnorm": (
        ("p", "mean", "stddev"),
        lambda p, mean, stddev: ("p must lie between 0 and 1" if p < 0 or p > 1
                                 else "stddev must be positive" if stddev <= 0 else None),
        lambda p, mean, stddev: norm.ppf(p, mean, stddev)),
    "normalcdf": (
        ("left", "right", "mean", "stddev"),
        lambda left, right, mean, stddev: "stddev must be positive" if stddev <= 0 else None,
        lambda left, right, mean, stddev: (norm(mean, stddev).cdf(right)
                                           - norm(mean, stddev).cdf(left))),
}


def evaluate(model, name, t, *args):
    """The value of builtin `name` for `args`, or NaN, reported, if it does not accept them."""
    parameters, invalid, compute = BUILTINS[name]
    if not all(math.isfinite(arg) for arg in args):
        return np.nan
    reason = invalid(*args)
    if reason is not None:
        model.report_invalid_argument(name, t, reason, parameters, args)
        return np.nan
    return compute(*args)


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
