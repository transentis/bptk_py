"""
Stateless-server resume parity: Rust vs Python backend with delay().

This is the sequel to `rust_vs_python_delay_step.py`. That example showed that
delay() collapses in the Python backend when its input is a per-step-overridden
CONSTANT and only the delay OUTPUT is requested. This example reproduces the
*stateless server* lifecycle, where the whole session is serialised to external
storage after every step and the process effectively restarts before the next:

    begin_session
    loop:
        run_step(settings=...)     # apply this step's constant override
        externalise                # save session_state to a FileAdapter
        drop everything            # fresh bptk + fresh model  -> in-memory memo gone
        restore                    # pull session_state back in
    (next step runs on the restored instance)

It runs the cycle twice per backend: once requesting only the delay output
(`["incoming"]`) and once requesting all equations (`["orders", "incoming"]`,
the workaround that "fixes" the plain step-mode collapse).

Finding
-------
    request              python (resume cycle)     rust
    ["incoming"]         WRONG  (delay collapses)   correct
    ["orders","incoming"] correct                   correct

Two things to take away:

  1. Rust is correct in BOTH modes -- independent of what is requested.
  2. Python's correctness in the resume cycle equals its correctness in-process:
     the real externalise/restore cycle faithfully preserves the memo, so it
     neither introduces nor fixes the collapse. It is NOT the reset_cache
     scenario (see below).

Why
---
  * Python persists the RESULT. Its history lives only in the memoisation cache
    (`model.memo`, carried as `session_state["scenario_cache"]` and round-tripped
    with numeric-key restoration by the state adapter). A per-step override
    installs a time-blind `lambda t: value` (sd_simulation.change_equation), so
    the *equations* themselves have no memory. If the delay output alone is
    requested, `orders` is only materialised late, via the delay lookback, once
    the override has already moved on -> the cache stores the WRONG history and
    the resume cycle faithfully carries that corruption forward.

  * Rust now persists the computed memo GRID (session_state["rust_state"]) and
    imports it on resume via `bptk._restore_rust_session()` -- no per-round replay.
    The recorded `settings_log` overrides are folded (last-value-wins) and re-applied
    so future steps see the right constants, but the grid itself is loaded directly:
    each `orders` cell was written at its own step with the override live then, so
    delay is a plain array lookback into an
    already-correct cell, regardless of what the caller requested.

Important nuance vs. reset_cache
--------------------------------
Requesting all equations survives THIS cycle because the memo is externalised
and restored. It does NOT survive a genuine `reset_cache()` -- i.e. dropping the
memo WITHOUT restoring it (a model edit mid-session, or any code path that
resets before the delay looks back). There the equations' lack of history is
exposed again and the delay collapses even with all equations requested. In
other words, the "all equations" workaround relies on the memo being both
correctly computed AND never dropped-without-restore; it treats the symptom, not
the cause.

The clean fix is to make the override source history-aware (store overrides per
time, or write them straight into the memo of the current step) rather than to
persist a corrupt result or bolt a second persistence path onto Python.

Usage:
    python examples/rust_vs_python_delay_resume.py
"""

import copy
import datetime
import tempfile

import BPTK_Py
from BPTK_Py import Model
from BPTK_Py.sddsl import functions as sd
from BPTK_Py.externalstateadapter.file_adapter import FileAdapter
from BPTK_Py.externalstateadapter.externalStateAdapter import InstanceState


DELAY_DURATION = 2.0        # orders placed now arrive 2 steps later
INITIAL_INCOMING = 8.0      # pipeline value before the first real order arrives
STARTTIME, STOPTIME, DT = 1, 12, 1

# The order profile over time. Raise 8 -> 20 at t=6, dip to 12 at t=10, back to 8.
# t:           1  2  3  4  5   6   7   8   9  10  11  12
ORDER_PLAN =  [8, 8, 8, 8, 8, 20, 20, 20, 20, 12,  8,  8]


# ---------------------------------------------------------------------------
# Model + bptk builder.  A FRESH one is built on every "process restart" so the
# in-memory memo starts empty and no Rust engine handle survives -- exactly the
# situation a stateless server faces when it reloads a session from storage.
# ---------------------------------------------------------------------------

def build_bptk():
    """orders is a bare CONSTANT, overwritten each step via run_step(settings=)."""
    model = Model(starttime=STARTTIME, stoptime=STOPTIME, dt=DT, name="const")
    orders = model.converter("orders")
    incoming = model.flow("incoming")
    inventory = model.stock("inventory")
    orders.equation = 8.0                                    # baseline; overridden per step
    incoming.equation = sd.delay(model, orders, DELAY_DURATION, INITIAL_INCOMING)
    inventory.initial_value = 0.0
    inventory.equation = incoming

    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({"mgr": {"model": model}})
    bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="mgr")
    return bptk


# ---------------------------------------------------------------------------
# Driver: step through the whole horizon, but externalise + restart + restore
# around every single step.
# ---------------------------------------------------------------------------

def run_cycle(backend, equations):
    """Drive begin_session + run_step, round-tripping the entire session through
    a FileAdapter (with compression, as the server does) after each step and
    rebuilding the bptk instance from scratch before the next one."""
    adapter = FileAdapter(compress=True, path=tempfile.mkdtemp())
    instance_id = "inst-{}-{}".format(backend, "_".join(equations))

    bptk = build_bptk()
    bptk.begin_session(scenario_managers=["mgr"], scenarios=["base"],
                       equations=equations, backend=backend)

    inc = {}
    for i in range(len(ORDER_PLAN)):
        settings = {"mgr": {"base": {"constants": {"orders": float(ORDER_PLAN[i])}}}}
        step = bptk.run_step(settings=settings)
        for t, v in step["mgr"]["base"]["incoming"].items():
            inc[float(t)] = v

        # ---- externalise the whole session to storage ----
        state = InstanceState(
            state=copy.deepcopy(bptk.session_state),
            instance_id=instance_id,
            time=str(datetime.datetime.now()),
            timeout=3600,
            step=bptk.session_state["step"],
        )
        adapter.save_instance(state)

        # ---- simulate a process restart: drop everything, build fresh ----
        del bptk
        bptk = build_bptk()                          # fresh model -> empty memo, no rust_model

        # ---- pull the externalised state back in ----
        loaded = adapter.load_instance(instance_id)
        bptk.session_state = loaded.state

    return inc


def expected(order_by_t):
    """Correct shipping-delay output: incoming(t) = orders(t-lag), initial before."""
    lag = int(DELAY_DURATION / DT)
    out = {}
    for i in range(len(ORDER_PLAN)):
        t = STARTTIME + i * DT
        out[float(t)] = INITIAL_INCOMING if i < lag else order_by_t[t - DELAY_DURATION]
    return out


def report(title, equations, order_by_t):
    exp = expected(order_by_t)
    py = run_cycle("python", equations)
    rust = run_cycle("rust", equations)
    print("\n=== {} ===".format(title))
    print("    requesting {}".format(equations))
    print("    {:>4} {:>9} {:>8} {:>8}  {}".format("t", "expected", "python", "rust", ""))
    py_ok = rust_ok = True
    for t in sorted(exp):
        e = exp[t]
        p = py.get(t)
        r = rust.get(t)
        if p is None or abs(p - e) > 1e-9:
            py_ok = False
        if r is None or abs(r - e) > 1e-9:
            rust_ok = False
        v = "PY!=RUST" if (p is None or r is None or abs(p - r) > 1e-9) else "ok"
        print("    {:>4g} {:>9g} {:>8} {:>8}  {}".format(t, e, _fmt(p), _fmt(r), v))
    print("    -> python {}, rust {}".format(
        "correct" if py_ok else "WRONG (delay collapsed)",
        "correct" if rust_ok else "WRONG"))


def _fmt(x):
    return "{:g}".format(x) if isinstance(x, (int, float)) else str(x)


if __name__ == "__main__":
    order_by_t = {STARTTIME + i: q for i, q in enumerate(ORDER_PLAN)}

    print("delay(orders, 2, 8) driven step-by-step, with the FULL session")
    print("externalised to a FileAdapter and the process restarted after each step.")
    print("order profile:", ORDER_PLAN)

    # (1) only the delay output requested -> Python collapses, Rust correct
    report("only the delay OUTPUT requested", ["incoming"], order_by_t)
    # (2) all equations requested -> the memo carries orders' history; both correct
    report("ALL equations requested (the step-mode 'fix')", ["orders", "incoming"], order_by_t)
