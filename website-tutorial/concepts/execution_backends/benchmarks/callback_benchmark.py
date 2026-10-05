"""The benchmark behind callback_benchmark.md: what a user-defined function costs.

    uv run python website-tutorial/concepts/execution_backends/benchmarks/callback_benchmark.py

The workforce chain of the arrayed benchmark at twelve levels, with a market wage per
level: the wage at which a labour pool fills that level's openings. The pool's supply
curve has no inverse in closed form, so the wage is solved by bisection - a function a
modeller would actually write in Python, because the DSL cannot express a loop.

Five versions of the model, which differ only in how `wage` is computed:

* an expression - no callback, the engine's own speed
* a function that returns its argument - the crossing alone, without work
* bisection with 10, 40 and 160 iterations - the crossing plus work that grows

Both engines run through `run_scenarios`, median of three runs, each on a freshly built
model, and their results are compared.
"""

from __future__ import annotations

import math
import platform
import statistics
import sys
import time

LEVELS = 12
STEPS = (400, 4000)
VARIANTS = ("expression", "crossing only", 10, 40, 160)
RUNS = 3


def clearing_wage(openings, pool, reference, iterations):
    """The wage at which `pool` supplies `openings` people.

    Supply rises with the wage, at a rate no formula inverts - which is what makes it a
    case for a Python function rather than an equation.
    """
    def supply(wage):
        x = wage / reference
        return pool * (1.0 - math.exp(-x)) * (1.0 + 0.5 * math.sin(x))

    low, high = 0.0, 2.0 * reference
    for _ in range(iterations):
        middle = (low + high) / 2.0
        if supply(middle) < openings:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def build(levels, stoptime, variant):
    """The chain of the arrayed benchmark, plus a market wage per level."""
    from BPTK_Py import Model

    names = [f"l{i}" for i in range(levels)]
    model = Model(starttime=0.0, stoptime=stoptime, dt=1.0, name="chain")

    def vector(element, values):
        element.setup_named_vector(dict(zip(names, values)))
        return element

    headcount = vector(model.stock("headcount"), [100.0] * levels)
    hiring = vector(model.flow("hiring"), [0.0] * levels)
    promotion = vector(model.flow("promotion"), [0.0] * levels)
    attrition = vector(model.flow("attrition"), [0.0] * levels)
    cost = vector(model.converter("cost"), [0.0] * levels)

    hiring_rate = vector(model.constant("hiring_rate"), [12.0] + [1.0] * (levels - 1))
    promotion_rate = vector(model.constant("promotion_rate"), [0.12] * (levels - 1) + [0.0])
    attrition_rate = vector(model.constant("attrition_rate"), [0.08] * levels)
    salary = vector(model.constant("salary"), [50000.0 + 1000.0 * i for i in range(levels)])

    hiring.equation = hiring_rate
    promotion.equation = headcount * promotion_rate
    attrition.equation = headcount * attrition_rate
    cost.equation = headcount * salary
    for i, name in enumerate(names):
        arriving = hiring[name] if i == 0 else hiring[name] + promotion[names[i - 1]]
        headcount[name].equation = arriving - promotion[name] - attrition[name]

    # The market wage: what it takes to refill each level's openings from its pool
    pool = vector(model.constant("pool"), [20.0] * levels)
    openings = vector(model.converter("openings"), [0.0] * levels)
    openings.equation = promotion + attrition
    wage = vector(model.converter("wage"), [0.0] * levels)

    if variant == "expression":
        wage.equation = salary * 1.1
    elif variant == "crossing only":
        market_wage = model.function(
            "market_wage", lambda model, t, openings, pool, reference: reference)
        wage.equation = market_wage(openings, pool, salary)
    else:
        market_wage = model.function(
            "market_wage", lambda model, t, openings, pool, reference:
            clearing_wage(openings, pool, reference, variant))
        wage.equation = market_wage(openings, pool, salary)

    hiring_cost = vector(model.converter("hiring_cost"), [0.0] * levels)
    hiring_cost.equation = hiring * wage
    total_hiring_cost = model.converter("total_hiring_cost")
    total_hiring_cost.equation = hiring_cost.arr_sum()
    total_cost = model.converter("total_cost")
    total_cost.equation = cost.arr_sum()

    equations = ([f"wage[{name}]" for name in names]
                 + ["total_hiring_cost", "total_cost"])
    return model, equations


def run(stoptime, variant, backend):
    from BPTK_Py import bptk

    model, equations = build(LEVELS, stoptime, variant)
    instance = bptk()
    instance.register_model(model)
    started = time.perf_counter()
    results = instance.run_scenarios(scenario_managers=["smChain"], scenarios=["base"],
                                     equations=equations, backend=backend)
    return (time.perf_counter() - started) * 1000.0, results


def main():
    print(f"{platform.machine()}, Python {sys.version.split()[0]}\n")
    print("| Timesteps | Wage computed by | Python engine | Rust engine | Speedup |")
    print("|---|---|---|---|---|")
    largest_difference = 0.0
    for steps in STEPS:
        for variant in VARIANTS:
            timings, results = {}, {}
            for backend in ("python", "rust"):
                measured = [run(steps, variant, backend) for _ in range(RUNS)]
                timings[backend] = statistics.median(m[0] for m in measured)
                results[backend] = measured[0][1]
            difference = (results["python"] - results["rust"]).abs().max().max()
            largest_difference = max(largest_difference, float(difference))
            label = variant if isinstance(variant, str) else f"bisection, {variant} iterations"
            print(f"| {steps:,} | {label} | {timings['python']:,.1f} ms | "
                  f"{timings['rust']:,.1f} ms | {timings['python'] / timings['rust']:.1f}× |")
    print(f"\nLargest difference between the engines: {largest_difference}")


if __name__ == "__main__":
    main()
