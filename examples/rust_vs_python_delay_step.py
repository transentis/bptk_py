"""
Step-by-step delay() parity: Rust vs Python backend.

Demonstrates a subtle difference between the two backends when a model uses
sd.delay() and is driven step-by-step via bptk.begin_session() + run_step().

Finding
-------
The result of delay() in step mode depends on whether its INPUT can be correctly
re-evaluated at a past time t:

  * input is a per-step-OVERRIDDEN CONSTANT (set via run_step(settings=...))
        -> Python COLLAPSES the delay (zero lag); Rust stays correct.
  * input is a LOOKUP table (function of time)          -> both correct.
  * input is a LINEAR function of time (e.g. 2*time)     -> both correct.

Why
---
Python evaluates only the requested equations each step and memoizes lazily; a
per-step override installs a time-blind `lambda t: value` (sd_simulation.change_
equation). When delay looks back and misses the memo cache, it re-reads that
lambda and gets the CURRENT value instead of the historical one -> collapse.
A lookup / linear input is a genuine function of time, so re-evaluating it at a
past t still yields the right value.

Rust pre-allocates a memo[entity][step] grid, evaluates EVERY entity at EVERY
step, and delay is a plain array lookback (memo[input][step-lag]) into an
already-written cell -> always correct, regardless of the input's form or which
equations were requested.

Practical rule: feed delay()/smooth()/trend() with a real model element
(converter / stock / flow / lookup), never a bare constant you overwrite per
step. Interactive decisions should flow through a stock/flow before being delayed.

Usage:
    python examples/rust_vs_python_delay_step.py
"""

import BPTK_Py
from BPTK_Py import Model
from BPTK_Py.sddsl import functions as sd


DELAY_DURATION = 2.0        # orders placed now arrive 2 steps later
INITIAL_INCOMING = 8.0      # pipeline value before the first real order arrives
STARTTIME, STOPTIME, DT = 1, 12, 1

# The order profile over time. Raise 8 -> 20 at t=6, dip to 12 at t=10, back to 8.
# t:           1  2  3  4  5   6   7   8   9  10  11  12
ORDER_PLAN =  [8, 8, 8, 8, 8, 20, 20, 20, 20, 12,  8,  8]


# ---------------------------------------------------------------------------
# Model builders -- same delay chain, three different delay INPUTS
#   incoming = delay(orders, 2, 8);  inventory = incoming
# ---------------------------------------------------------------------------

def build_constant():
    """orders is a bare CONSTANT, overwritten each step via run_step(settings=)."""
    model = Model(starttime=STARTTIME, stoptime=STOPTIME, dt=DT, name="const")
    orders = model.constant("orders")
    incoming = model.flow("incoming")
    inventory = model.stock("inventory")
    orders.equation = 8.0                                     # baseline; overridden per step
    incoming.equation = sd.delay(model, orders, DELAY_DURATION, INITIAL_INCOMING)
    inventory.initial_value = 0.0
    inventory.equation = incoming
    return _wrap(model)


def build_lookup():
    """orders is a LOOKUP table over time -- a genuine function of t."""
    model = Model(starttime=STARTTIME, stoptime=STOPTIME, dt=DT, name="lookup")
    orders = model.converter("orders")
    incoming = model.flow("incoming")
    inventory = model.stock("inventory")
    # encode ORDER_PLAN as a graphical function t -> order quantity
    model.points["orders_table"] = [[STARTTIME + i, q] for i, q in enumerate(ORDER_PLAN)]
    orders.equation = sd.lookup(sd.time(), "orders_table")
    incoming.equation = sd.delay(model, orders, DELAY_DURATION, INITIAL_INCOMING)
    inventory.initial_value = 0.0
    inventory.equation = incoming
    return _wrap(model)


def build_linear():
    """orders is a LINEAR function of time (2*t) -- also a function of t."""
    model = Model(starttime=STARTTIME, stoptime=STOPTIME, dt=DT, name="linear")
    orders = model.converter("orders")
    incoming = model.flow("incoming")
    inventory = model.stock("inventory")
    orders.equation = 2.0 * sd.time()                        # linear ramp: 2,4,6,...
    incoming.equation = sd.delay(model, orders, DELAY_DURATION, INITIAL_INCOMING)
    inventory.initial_value = 0.0
    inventory.equation = incoming
    return _wrap(model)


def _wrap(model):
    """Register a single-scenario bptk instance for the given model."""
    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({"mgr": {"model": model}})
    bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
    return bptk


# ---------------------------------------------------------------------------
# Driver: step through the whole horizon, collect incoming(t)
# ---------------------------------------------------------------------------

def run_incoming(build_fn, backend, equations, inject_orders):
    """Drive begin_session + run_step. If inject_orders, override the `orders`
    constant each step via settings (constant model); otherwise the order
    profile is already encoded in the equation (lookup / linear models)."""
    bptk = build_fn()
    bptk.begin_session(scenario_managers=["mgr"], scenarios=["base"],
                       equations=equations, backend=backend)
    inc = {}
    try:
        for i in range(len(ORDER_PLAN)):
            # per-step constant override -- only the constant model uses this
            settings = ({"mgr": {"base": {"constants": {"orders": float(ORDER_PLAN[i])}}}}
                        if inject_orders else None)
            step = bptk.run_step(settings=settings)
            for t, v in step["mgr"]["base"]["incoming"].items():
                inc[float(t)] = v
    finally:
        bptk.end_session()
    return inc


def expected(order_by_t):
    """Correct shipping-delay output: incoming(t) = orders(t-lag), initial before."""
    lag = int(DELAY_DURATION / DT)
    out = {}
    for i in range(len(ORDER_PLAN)):
        t = STARTTIME + i * DT
        out[float(t)] = INITIAL_INCOMING if i < lag else order_by_t[t - DELAY_DURATION]
    return out


def report(title, build_fn, inject_orders, order_by_t):
    exp = expected(order_by_t)
    # request ONLY the delay output -- the input is NOT in the requested list,
    # which is what exposes the Python constant-override collapse.
    py = run_incoming(build_fn, "python", ["incoming"], inject_orders)
    rust = run_incoming(build_fn, "rust", ["incoming"], inject_orders)
    print("\n=== {} ===".format(title))
    print("    {:>4} {:>9} {:>8} {:>8}  {}".format("t", "expected", "python", "rust", ""))
    py_ok = rust_ok = True
    for t in sorted(exp):
        e, p, r = exp[t], py[t], rust[t]
        if abs(p - e) > 1e-9:
            py_ok = False
        if abs(r - e) > 1e-9:
            rust_ok = False
        v = "PY!=RUST" if abs(p - r) > 1e-9 else "ok"
        print("    {:>4g} {:>9g} {:>8g} {:>8g}  {}".format(t, e, p, r, v))
    print("    -> python {}, rust {}".format(
        "correct" if py_ok else "WRONG (delay collapsed)",
        "correct" if rust_ok else "WRONG"))


if __name__ == "__main__":
    order_by_t = {STARTTIME + i: q for i, q in enumerate(ORDER_PLAN)}
    linear_by_t = {STARTTIME + i: 2.0 * (STARTTIME + i) for i in range(len(ORDER_PLAN))}

    print("delay(orders, 2, 8) driven step-by-step; requesting only ['incoming']")
    print("order profile:", ORDER_PLAN)

    # (1) constant overridden per step -> Python collapses, Rust correct
    report("orders = per-step-overridden CONSTANT", build_constant, True, order_by_t)
    # (2) lookup table over time -> both correct
    report("orders = LOOKUP table over time", build_lookup, False, order_by_t)
    # (3) linear function of time -> both correct
    report("orders = LINEAR function of time (2*t)", build_linear, False, linear_by_t)
