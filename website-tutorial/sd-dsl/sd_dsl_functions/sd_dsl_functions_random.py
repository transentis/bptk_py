# Front matter the .py format cannot carry; injected on export.
# description: The random functions of the SD DSL from A to Z - drawing numbers from statistical distributions.
# keywords: system dynamics, systemdynamics, sd dsl, bptk, bptk-py, python, business simulation
# external-env: true
# /// script
# dependencies = [
#     "bptk-py",
# ]
# ///

import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Random Functions")


@app.cell
def _():
    # Added by `marimo convert`. Keep it: `marimo export html` turns markdown
    # blocks into mo.md(...) cells, which need this import.
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Random Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The functions of the SD DSL that draw random numbers from a distribution, from A to Z. Each call draws a new number in every timestep, or once per [sample](#minimum-maximum-and-sample); with a [seed](#seeds) the numbers are the same on every run. To use them, import `sd_functions` beside the `Model` class:
    """)
    return


@app.cell
def _():
    #| echo: true
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk
    import numpy as np
    bptk=bptk()
    return Model, bptk, np, sd


@app.cell
def _():
    #| echo: false
    import matplotlib.pyplot as plt
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['savefig.facecolor'] = 'white'
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Seeds

    Every random function takes an optional last argument, `seed`. Without it a function draws new numbers on every run. With it, it draws the same sequence on every run - the way to make a stochastic model repeatable, or to compare two scenarios on the same random numbers.

    The number a seeded function draws depends on three things only: the seed, the timestep - counted from the start of the run - and, in an arrayed model, the cell. It does not depend on the order the model is computed in, on the other random functions of the model, or on whether a session was interrupted and resumed. A function without a seed is not affected by one that has a seed.

    Some things follow from that:

    - **Two functions with the same seed draw the same numbers.** That is what the seed promises; give each function its own seed where they should be independent.
    - **The cells of an array draw independently** under one seed.
    - **`dt` is part of the sequence.** With another `dt` the timesteps are different, and so are the numbers.
    - The seed is a whole number of at least 0, or a model element holding one - a constant, so that a scenario can choose it. Anything else gives NaN and an `[ERROR]`.
    - The numbers are not those Stella draws for the same seed; Stella's generator is not public.
    - **The two engines draw different numbers for the same seed.** Each engine draws the same numbers on every run, and both draw from the same distribution - but a model moved from the Python engine to the Rust engine, or back, draws other numbers under the same seed.

    In the plot below, `first` and `second` use the seed from the slider and lie on top of each other. `unseeded` has no seed and changes every time the cell runs. Move the slider and both seeded curves change together.
    """)
    return


@app.cell
def _(mo):
    seed_slider = mo.ui.slider(start=0, stop=100, step=1, value=42, show_value=True, label="Seed")
    seed_slider
    return (seed_slider,)


@app.cell
def _(Model, bptk, sd, seed_slider):
    #| echo: true
    model_seeds = Model(starttime=0.0, stoptime=20.0, dt=1.0, name='seeds')
    model_seeds.converter('first').equation = sd.normal(100.0, 10.0, seed=seed_slider.value)
    model_seeds.converter('second').equation = sd.normal(100.0, 10.0, seed=seed_slider.value)
    model_seeds.converter('unseeded').equation = sd.normal(100.0, 10.0)
    bptk.reset_all_scenarios()
    bptk.register_model(model_seeds)
    bptk.plot_scenarios(
        scenario_managers=['smSeeds'],
        scenarios=['base'],
        equations=['first', 'second', 'unseeded'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Minimum, Maximum and Sample

    Every random function but `random` takes three more optional arguments after the seed, as in Stella: `minimum`, `maximum` and `sample`.

    - **`minimum` and `maximum` keep a draw within them.** The function draws again until a number lies between them, both included. Leave one out, or give it as NaN, for no bound on that side; equal bounds give that number.
    - **Bounds the distribution practically never reaches give NaN and an `[ERROR]`**: after 100 draws outside them the function gives up. Stella draws a uniform number between the bounds there instead, which hides that they miss the distribution. A minimum above the maximum gives NaN and an `[ERROR]` too.
    - **`sample` holds a number for a while** rather than drawing a new one in every timestep: from the start of the run, a new number is drawn once per `sample` time units. A sample is cut down to a whole number of timesteps, as Stella does; one shorter than two timesteps draws in every timestep.

    In the plot below `bounded` draws from the same distribution as `free`, within 90 and 110, and `held` keeps each number for the sample from the slider:
    """)
    return


@app.cell
def _(mo):
    sample_slider = mo.ui.slider(start=1, stop=10, step=1, value=4, show_value=True, label="Sample")
    sample_slider
    return (sample_slider,)


@app.cell
def _(Model, bptk, sample_slider, sd):
    #| echo: true
    model_bounds = Model(starttime=0.0, stoptime=40.0, dt=1.0, name='bounds')
    model_bounds.converter('free').equation = sd.normal(100.0, 10.0, seed=1)
    model_bounds.converter('bounded').equation = sd.normal(100.0, 10.0, seed=2, minimum=90.0, maximum=110.0)
    model_bounds.converter('held').equation = sd.normal(100.0, 10.0, seed=3, sample=sample_slider.value)
    bptk.reset_all_scenarios()
    bptk.register_model(model_bounds)
    bptk.plot_scenarios(
        scenario_managers=['smBounds'],
        scenarios=['base'],
        equations=['free', 'bounded', 'held'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## BETA Function
    The BETA operator generates a series of random numbers that conforms to a beta distribution defined by two shape arguments, ``alpha`` and ``beta``.

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_3 = Model(starttime=0, stoptime=10, dt=0.1)
    f_2 = m_3.biflow(name='beta')
    alpha = 1
    beta = 2
    f_2.equation = sd.beta(alpha, beta)
    f_2.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## BINOMIAL
    This operator generates a series of random numbers from a discrete probability distribution of the number of successes in a sequence of trials with a given success probability. The success probability should be a number between 0 and 1.

    Arguments are ``number of trials (n)`` and ``success probability (p)``.

    A quick example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_4 = Model(starttime=0, stoptime=10, dt=0.1)
    f_3 = m_4.flow(name='binomial')
    n = 100
    p = 0.1
    f_3.equation = sd.binomial(n, p)
    f_3.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## EXPRND Function
    This operator generates a series of exponentially distributed random numbers with a given ``mean``.

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_6 = Model(starttime=0, stoptime=10, dt=0.1)
    f_5 = m_6.flow(name='exprnd')
    mean = sd.time() + 1
    f_5.equation = sd.exprnd(mean)
    f_5.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## GAMMA Function
    The GAMMA builtin generates a series of random numbers that conforms to a gamma distribution with the specified ``shape`` and ``scale``. If unspecified, ``scale`` uses the value 1.0.

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_8 = Model(starttime=0, stoptime=10, dt=0.1)
    f_7 = m_8.biflow(name='gamma')
    shape = 10
    scale = sd.time() + 1
    f_7.equation = sd.gamma(shape, scale)
    f_7.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## GEOMETRIC Function

    The GEOMETRIC operator generates a series of random numbers from a discrete probability distribution of the number of trials before the first success with a given ``success probability (p)``.

    ``p`` is the only parameter. It should be any value between 0 and 1.

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_10 = Model(starttime=0, stoptime=10, dt=0.1)
    f_9 = m_10.biflow(name='geometric')
    p_1 = 0.1
    f_9.equation = sd.geometric(p_1)
    f_9.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## LOGISTIC Function

    The LOGISTIC operator generates a series of random numbers that conforms to a logistic distribution with a specified ``mean`` and ``scale``.

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_12 = Model(starttime=-1, stoptime=10, dt=0.1)
    f_11 = m_12.biflow(name='logistic')
    mean_1 = 0
    scale_1 = 1
    f_11.equation = sd.logistic(mean_1, scale_1)
    f_11.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## LOGNORMAL Function
    The LOGNORMAL operator generates a series of random numbers that conform to a Log-Normal distribution (that is, the log of the independent variable follows a normal distribution). LOGNORMAL samples a new random number in each iteration of a simulation.

    Arguments are ``mean`` and ``standard deviation`` of the numbers drawn, as in XMILE - not of the normal distribution underneath. The mean has to be positive.

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_13 = Model(starttime=0, stoptime=10, dt=0.1)
    f_12 = m_13.biflow(name='lognormal')
    mean_2 = 2
    stdev = 1
    f_12.equation = sd.lognormal(mean_2, stdev)
    f_12.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## LOOKUPRANDOM Function

    `lookuprandom(points, seed=None, minimum=None, maximum=None, sample=None)` draws from a lookup table read as a probability density: the higher the table at an `x`, the more often values near it are drawn. As in Stella, each segment between two points of the table is chosen by its area, and the value is then drawn uniformly within the segment - so the mean of the draws is what `lookupmean` gives for the same table. `points` is a list of `(x, y)` points or the name of a table in `model.points`; the table must not fall below 0 and must have an area, or the draw is NaN and an `[ERROR]`. `seed`, `minimum`, `maximum` and `sample` work as for every random function.

    The table is read when the value is drawn, so a scenario that sets other points changes what is drawn. In the example the table rises to a peak at 2, and most draws fall between 1 and 3:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_lookuprandom = Model(starttime=0, stoptime=100, dt=1)
    m_lookuprandom.points['peak'] = [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 1.0), (4.0, 0.0)]
    drawn = m_lookuprandom.converter('drawn')
    drawn.equation = sd.lookuprandom('peak', seed=4)
    drawn.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## MONTECARLO Function
    The MONTECARLO operator randomly generates a series of zeros and ones from a Bernoulli distribution based on the probability you've provided. The probability is the percentage probability of an event happening per unit of simulation time. The probability value can be either a variable or a constant, but should evaluate to a number between 0 and 100.

    MONTECARLO is equivalent to the following logic:

    IF RANDOM(0,100,<seed>) < probability*DT THEN 1 ELSE 0

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_14 = Model(starttime=0, stoptime=10, dt=0.1)
    f_13 = m_14.biflow(name='montecarlo')
    probability = 50
    f_13.equation = sd.montecarlo(probability)
    f_13.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## NEGBINOMIAL Function

    The NEGBINOMIAL operator generates a series of random numbers from a negative binomial
    distribution: how many independent trials with success probability ``p`` it takes to reach
    ``n`` successes.

    Signature:
    ``negbinomial(n, p)``

    ``n`` is the number of successes to reach, ``p`` the probability of success in one trial.
    Both may be elements or plain numbers.

    Because it counts trials rather than successes, the smaller ``p`` gets the larger the
    numbers become:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_negbinomial = Model(starttime=1, stoptime=10, dt=0.1)
    f_negbinomial = m_negbinomial.biflow(name='negbinomial')
    successes = 5
    success_probability = 0.4
    f_negbinomial.equation = sd.negbinomial(successes, success_probability)
    f_negbinomial.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## NORMAL Function
    The NORMAL operator generates a series of normally distributed random numbers with a specified mean and stddev (standard deviation).

    Arguments are ``mean`` and the ``standard deviation`` of the underlying normal distribution.

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_15 = Model(starttime=0, stoptime=10, dt=1)
    f_14 = m_15.biflow(name='normal')
    mean_3 = 0
    stdev_1 = 1
    f_14.equation = sd.normal(mean_3, stdev_1)
    f_14.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## NORMALPINK Function

    `normalpink(model, mean, stddev, correlation_time, seed=None, minimum=None, maximum=None, sample=None)` is Stella's `NORMALPINK`: normally distributed noise that does not jump freely from step to step but drifts, the way a demand or a price fluctuates. Each step it moves the share `DT / correlation_time` of the way from its previous value towards a new normal draw, starting from `mean`; over a long run its values have the mean `mean` and the standard deviation `stddev`, and two neighbouring steps are correlated by `1 - DT / correlation_time`. A correlation time of at most one DT makes it plain `normal` noise; 0 gives NaN and an `[ERROR]`. It keeps its previous value, so it takes the model first.

    It is the pink noise of Sterman's *Business Dynamics* (2000): white noise smoothed over the correlation time, its spread raised so that the smoothed noise keeps the standard deviation asked for.

    - `seed` makes the noise the same on every run, as for every random function.
    - `minimum` and `maximum` bound the noise itself: where a step would leave them, the draw is made again from the same previous value. Stella instead moves on from the value it rejects, which pulls the noise towards the bound - see [XMILE, Stella and the SD DSL](../../xmile/xmile_in_the_sd_dsl/xmile_in_the_sd_dsl.md#xmile-stella-and-the-sd-dsl).
    - `sample` holds the whole noise: it takes one step per sample and keeps its value in between.

    In the example the same mean and spread once as plain `normal` noise and once with a correlation time of 10:
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    m_pink = Model(starttime=0, stoptime=100, dt=1, name='pink')
    m_pink.converter('white').equation = sd.normal(100.0, 10.0, seed=3)
    m_pink.converter('pink').equation = sd.normalpink(m_pink, 100.0, 10.0, 10.0, seed=3)
    bptk.reset_all_scenarios()
    bptk.register_model(m_pink)
    bptk.plot_scenarios(scenario_managers=['smPink'], scenarios=['base'], equations=['white', 'pink'], format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## PARETO Function
    The PARETO operator generates a series of random numbers that conforms to a distribution whose log is exponentially distributed with a specified shape and scale: the classic Pareto distribution, which starts at `scale`.

    Arguments are ``shape`` and ``scale``.

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_17 = Model(starttime=1, stoptime=10, dt=0.1)
    f_16 = m_17.biflow(name='pareto')
    shape_1 = 1
    scale_2 = 1
    f_16.equation = sd.pareto(shape_1, scale_2)
    f_16.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## POISSON Function
    The POISSON operator generates a series of random numbers that conform to a Poisson distribution. The mean value of the output is mu * DT.

    Only argument is ``mu``, a float or integer number or any operator that returns a number.

    Example (with an increasing ``mu`` expressed as the current simulation time):
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_19 = Model(starttime=1, stoptime=10, dt=0.1)
    f_18 = m_19.biflow(name='poisson')
    mu = sd.time()
    f_18.equation = sd.poisson(mu)
    f_18.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## RANDOM / UNIFORM Function

    RANDOM and UNIFORM both draw a random number between a minimum and maximum value that conforms to a uniform distribution. For compatibility with modelling practices, we included both in the SD DSL (just as the Stella Architect builtins).

    Arguments are the ``min_value`` and ``max_value`` between which the random number should lie. If not given, the random number is between 0 and 1. ``uniform`` also takes [minimum, maximum and sample](#minimum-maximum-and-sample); ``random`` takes only a seed, as in Stella.

    Simple example where the number always lies between DT and the current simulation time:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_20 = Model(starttime=1, stoptime=10, dt=0.1)
    f_19 = m_20.biflow(name='uniform / random')
    min_value = 0.1
    max_value = sd.time()
    f_19.equation = sd.random(min_value, max_value)
    f_19.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## TRIANGULAR Function
    The TRIANGULAR operator generates a series of random numbers that conforms to a triangular distribution with a specified ``lower bound``, ``mode``, and ``upper bound``.

    A simple example with the current simulation time as upper bound:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_21 = Model(starttime=1, stoptime=10, dt=0.1)
    f_20 = m_21.biflow(name='triangular')
    lower_bound = 0
    mode = 1
    upper_bound = sd.time()
    f_20.equation = sd.triangular(lower_bound, mode, upper_bound)
    f_20.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## WEIBULL Function
    The WEIBULL operator generates a series of random numbers that conforms to a Weibull distribution with the specified ``shape`` and ``scale``.

    Let's create a quick example with ``scale`` set to the current simulation time:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_22 = Model(starttime=1, stoptime=10, dt=0.1)
    f_21 = m_22.biflow(name='weibull')
    shape_2 = 1
    scale_3 = sd.time()
    f_21.equation = sd.weibull(shape_2, scale_3)
    f_21.plot(format="axes")
    return


if __name__ == "__main__":
    app.run()
