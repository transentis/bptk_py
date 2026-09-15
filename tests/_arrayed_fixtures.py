"""Multidimensional SD DSL model builders shared across the array tests.

The flagship example is a **workforce aging chain by seniority**: a named vector
over junior / mid / senior, with per-level hiring, promotion and attrition, element-wise
salary cost, and cross-level aggregation to scalars.

Why this model and not another:

* An aging chain is the canonical use of arrays in System Dynamics, so it is the example
  a user is looking for.
* Every flow is naturally non-negative - hiring, promotion, attrition - which fits
  `Flow.build_function_string`'s `max(0, ...)` clamp by construction instead of fighting
  it. A model with a shrinking cohort expressed as a *negative* flow would silently read
  zero.
* Total cost comes from an element-wise multiply plus `arr_sum`, not from `dot`. That is
  both the more natural formulation and it avoids `dot`'s rejection of named arrays.
* One dimension of three keeps it readable on a single page.

The matrix companion is deliberately small and unnamed: its job is to reach the matrix
and `dot` paths that the flagship avoids, not to teach anything.

Builders return fresh objects on every call, following the convention in
``tests/test_rust_backend.py``: the interleaved step-parity tests stand up two
independent engines, one per backend, so a shared instance would couple them.
"""

from __future__ import annotations

import BPTK_Py
from BPTK_Py import Model


LEVELS = ("junior", "mid", "senior")
"""Seniority levels, in chain order. Promotion moves headcount along this sequence."""


def build_workforce_model(name: str = "workforce", with_aggregations: bool = True) -> Model:
    """The flagship arrayed model: a workforce aging chain over seniority levels.

    Structure, all arrayed over :data:`LEVELS` unless noted:

    ==========================  ==========  ============================================
    Element                     Kind        Equation
    ==========================  ==========  ============================================
    ``headcount[level]``        stock       net of the three flows below
    ``hiring[level]``           flow        ``hiring_rate[level]``
    ``promotion[level]``        flow        ``headcount[level] * promotion_rate[level]``
    ``attrition[level]``        flow        ``headcount[level] * attrition_rate[level]``
    ``cost[level]``             converter   ``headcount[level] * salary[level]``
    ``total_headcount``         converter   ``headcount.arr_sum()``      (scalar)
    ``total_cost``              converter   ``cost.arr_sum()``           (scalar)
    ``average_salary``          converter   ``salary.arr_mean()``        (scalar)
    ==========================  ==========  ============================================

    The chain crosses indices: what is promoted out of one level flows into the next, so
    ``headcount[mid]`` references ``promotion[junior]``. Those are ordinary references to
    a differently-indexed sub-element, which is why the flattened model serialises.

    Parameters:
        name: model name.
        with_aggregations: when False, the three scalar aggregation converters are left
            out. Both settings serialise and run on either backend; the flag exists
            so a test can isolate the arrayed chain from the aggregations built on
            top of it.

    Returns:
        The `Model`. Sub-elements are reachable as ``model.stocks["headcount[junior]"]``
        or, through the parent, as ``headcount["junior"]``.
    """
    model = Model(starttime=0.0, stoptime=10.0, dt=1.0, name=name)

    headcount = model.stock("headcount")
    hiring = model.flow("hiring")
    promotion = model.flow("promotion")
    attrition = model.flow("attrition")

    salary = model.constant("salary")
    hiring_rate = model.constant("hiring_rate")
    promotion_rate = model.constant("promotion_rate")
    attrition_rate = model.constant("attrition_rate")

    cost = model.converter("cost")

    # A team of 155: a wide junior base, fewer seniors.
    headcount.setup_named_vector({"junior": 100.0, "mid": 40.0, "senior": 15.0})

    # Lateral hiring happens at every level, most of it into the junior base.
    hiring_rate.setup_named_vector({"junior": 12.0, "mid": 3.0, "senior": 1.0})

    # A senior is never promoted out of the chain, hence 0.0 - which also gives the
    # aggregations a genuine zero to carry.
    promotion_rate.setup_named_vector({"junior": 0.15, "mid": 0.08, "senior": 0.0})
    attrition_rate.setup_named_vector({"junior": 0.10, "mid": 0.06, "senior": 0.04})
    salary.setup_named_vector({"junior": 60000.0, "mid": 90000.0, "senior": 130000.0})

    hiring.setup_named_vector({level: 0.0 for level in LEVELS})
    promotion.setup_named_vector({level: 0.0 for level in LEVELS})
    attrition.setup_named_vector({level: 0.0 for level in LEVELS})
    cost.setup_named_vector({level: 0.0 for level in LEVELS})

    for level in LEVELS:
        hiring[level].equation = hiring_rate[level]
        promotion[level].equation = headcount[level] * promotion_rate[level]
        attrition[level].equation = headcount[level] * attrition_rate[level]
        cost[level].equation = headcount[level] * salary[level]

    # The aging chain. Promotion out of a level is an inflow to the next one.
    headcount["junior"].equation = (
        hiring["junior"] - promotion["junior"] - attrition["junior"]
    )
    headcount["mid"].equation = (
        hiring["mid"] + promotion["junior"] - promotion["mid"] - attrition["mid"]
    )
    headcount["senior"].equation = (
        hiring["senior"] + promotion["mid"] - attrition["senior"]
    )

    if with_aggregations:
        total_headcount = model.converter("total_headcount")
        total_headcount.equation = headcount.arr_sum()

        total_cost = model.converter("total_cost")
        total_cost.equation = cost.arr_sum()

        average_salary = model.converter("average_salary")
        average_salary.equation = salary.arr_mean()

    return model


def _build_workforce_bptk(with_aggregations: bool = True,
                          manager_name: str = "workforce_mgr"):
    """The flagship model wrapped in a bptk instance with scenarios registered.

    Two scenarios, so the parity tests have a constant override to exercise: `base`, and
    `hiring_freeze`, which stops junior hiring. The override addresses a **bracketed**
    sub-element name, which is the arrayed `set_constant` path that is a known issue
    in the step-by-step runner.

    Parameters:
        with_aggregations: passed through to :func:`build_workforce_model`.
        manager_name: **pass a distinct name per test that runs scenarios.**
            `ScenarioManagerFactory` is process-global, so two `bptk()` instances share
            a manager registered under the same name - and therefore its cached results.
            That leaks across tests in one session: after a `run_scenarios` for a
            *single* scenario, a later call for two scenarios returns *mixed* column
            names, the cached one bare (`headcount[junior]`) and the new one prefixed
            (`workforce_mgr_hiring_freeze_headcount[junior]`). The values stay correct;
            only the naming is inconsistent. A unique name per test sidesteps the shared
            cache entirely.
    """
    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager(
        {manager_name: {"model": build_workforce_model(
            with_aggregations=with_aggregations)}}
    )
    bptk.register_scenarios(
        scenarios={
            "base": {},
            "hiring_freeze": {"constants": {"hiring_rate[junior]": 0.0}},
        },
        scenario_manager=manager_name,
    )
    return bptk


def build_matrix_model(name: str = "matrix_companion") -> Model:
    """A minimal unnamed 2-D model reaching the matrix and `dot` paths.

    ``allocation`` is a 2x2 unnamed matrix, ``weights`` an unnamed vector of 2, and
    ``weighted`` their `dot` product - a vector. Kept as small as the shape allows,
    because the flagship carries the exposition.
    """
    model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name=name)

    allocation = model.constant("allocation")
    allocation.setup_matrix([2, 2], [[2.0, 3.0], [4.0, 5.0]])

    weights = model.constant("weights")
    weights.setup_vector(2, [0.5, 1.5])

    weighted = model.converter("weighted")
    weighted.equation = weights.dot(allocation)

    return model


def _build_matrix_bptk():
    """The matrix companion wrapped in a bptk instance."""
    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({"matrix_mgr": {"model": build_matrix_model()}})
    bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="matrix_mgr")
    return bptk


def build_biflow_model(name: str = "arrayed_biflow") -> Model:
    """An arrayed stock driven by an arrayed **biflow**, one index rising, one falling.

    A biflow carries no `max(0, ...)` clamp, so `level[shrinking]` runs negative - which
    is the point. The flagship cannot show this: every one of its flows is a flow.
    """
    model = Model(starttime=0.0, stoptime=6.0, dt=1.0, name=name)

    level = model.stock("level")
    level.setup_named_vector({"shrinking": 10.0, "growing": 10.0})

    net = model.biflow("net")
    net.setup_named_vector({"shrinking": 0.0, "growing": 0.0})

    rate = model.constant("rate")
    rate.setup_named_vector({"shrinking": -2.0, "growing": 3.0})

    for index in ("shrinking", "growing"):
        net[index].equation = rate[index]
        level[index].equation = net[index]

    total = model.converter("total")
    total.equation = level.arr_sum()

    return model


def _build_biflow_bptk(manager_name: str = "biflow_mgr"):
    """The arrayed biflow model wrapped in a bptk instance."""
    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({manager_name: {"model": build_biflow_model()}})
    bptk.register_scenarios(scenarios={"base": {}}, scenario_manager=manager_name)
    return bptk


def build_stateful_model(name: str = "arrayed_stateful") -> Model:
    """`smooth`, `trend` and `delay` over one named vector, each index with its own state.

    The per-index history is what this reaches: a single smoothed value copied across the
    indices would still look plausible at index `low` and be wrong at `high`.
    """
    from BPTK_Py import sd_functions as sd

    model = Model(starttime=0.0, stoptime=6.0, dt=1.0, name=name)

    source = model.constant("source")
    source.setup_named_vector({"low": 4.0, "high": 9.0})

    smoothed = model.converter("smoothed")
    smoothed.equation = sd.smooth(model, source, 3.0, 1.0)

    trended = model.converter("trended")
    trended.equation = sd.trend(model, source, 3.0, 1.0)

    delayed = model.converter("delayed")
    delayed.equation = sd.delay(model, source, 2.0, 0.0)

    return model


def _build_stateful_bptk(manager_name: str = "stateful_mgr"):
    """The arrayed stateful model wrapped in a bptk instance."""
    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({manager_name: {"model": build_stateful_model()}})
    bptk.register_scenarios(scenarios={"base": {}}, scenario_manager=manager_name)
    return bptk
