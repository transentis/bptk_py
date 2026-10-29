# Front matter the .py format cannot carry; injected on export.
# description: The deterministic functions of the SD DSL from A to Z - time, delays and smoothing, finance, lookups, rounding and mathematics.
# keywords: system dynamics, systemdynamics, sd dsl, bptk, bptk-py, python, business simulation
# external-env: true
# /// script
# dependencies = [
#     "bptk-py",
# ]
# ///

import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Deterministic Functions")


@app.cell
def _():
    # Added by `marimo convert`. Keep it: `marimo export html` turns markdown
    # blocks into mo.md(...) cells, which need this import.
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Deterministic Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The functions of the SD DSL that give the same result on every run, from A to Z. To use them, import `sd_functions` beside the `Model` class:
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
    ## ABS Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `ABS` function returns the absolute value of its input.

    Signature: `abs(input)`

    `input` may be any model element.
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_1 = Model(starttime=0.0, stoptime=10.0, dt=0.1, name='abs')
    input_converter = model_1.converter('input_converter')
    input_converter.equation = sd.time() - 5
    abs_converter = model_1.converter('abs_converter')
    abs_converter.equation = sd.abs(input_converter)
    bptk.reset_all_scenarios()
    bptk.register_model(model_1)
    bptk.plot_scenarios(
        scenario_managers=['smAbs'],
        scenarios=['base'],
        equations=['input_converter', 'abs_converter'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## CEIL / FLOOR / TRUNC Functions

    ``ceil`` rounds its input up to the next whole number, ``floor`` rounds it down. Unlike
    ``round`` they take no digit count - they always go to the nearest integer, and they always
    go in the same direction.

    Signature:
    ``ceil(expression)``, ``floor(expression)`` and ``trunc(expression)``

    ``expression`` can be any element that returns a float value.

    ``trunc(expression)`` cuts off the fractional part instead, towards zero. For a negative
    number that is the other direction: ``floor(-2.5)`` is -3, ``trunc(-2.5)`` is -2. The XMILE
    builtin ``INT`` is ``floor``.

    The example divides time by three, so the two functions step at different moments:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model_rounding = Model(starttime=0.0, stoptime=10.0, dt=0.1, name='rounding')
    third_of_time = model_rounding.converter('third_of_time')
    third_of_time.equation = sd.time() / 3
    rounded_up = model_rounding.converter('rounded_up')
    rounded_up.equation = sd.ceil(third_of_time)
    rounded_down = model_rounding.converter('rounded_down')
    rounded_down.equation = sd.floor(third_of_time)
    rounded_up.plot(format="axes")
    return


@app.cell
def _(rounded_down):
    #| echo: true
    rounded_down.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## CGROWTH Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    CGROWTH turns a growth rate per time unit, in percent, into the rate per `dt` that compounds to it. A stock whose inflow is `stock * cgrowth(model, 10)` grows by 10 percent per time unit, whatever `dt` is - with `stock * 0.10` it grows faster the smaller `dt` is. The example runs both with `dt = 0.25`: after ten time units `compounded` stands at 259, which is 100 × 1.1¹⁰, and `simple` above it.

    Signature: `cgrowth(model, percentage)`
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_cgrowth = Model(starttime=0.0, stoptime=10.0, dt=0.25, name='cgrowth')
    compounded = model_cgrowth.stock('compounded')
    compounded.initial_value = 100.0
    compounded.equation = compounded * sd.cgrowth(model_cgrowth, 10.0)
    simple = model_cgrowth.stock('simple')
    simple.initial_value = 100.0
    simple.equation = simple * 0.10
    bptk.reset_all_scenarios()
    bptk.register_model(model_cgrowth)
    bptk.plot_scenarios(
        scenario_managers=['smCgrowth'],
        scenarios=['base'],
        equations=['compounded', 'simple'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## COMBINATIONS
    The COMBINATIONS operator calculates the number of r-element subsets (or r-combinations) of an n-element set without repetition.

    Arguments `n` and `r` must be whole numbers of at least 0; anything else gives NaN and an `[ERROR]`. An `r` greater than `n` gives 0.

    Example using `n` as time - because `n` must be an integer, we have to wrap it in a user defined function.
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_5 = Model(starttime=3, stoptime=10, dt=1)
    f_4 = m_5.flow(name='combinations')
    n_1 = m_5.function('n', lambda model, t: int(t))
    r = 3
    f_4.equation = sd.combinations(n_1(), r)
    f_4.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## COUNTER Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    COUNTER describes a cycle in time: it starts at `start` at STARTTIME, rises by one per time unit and falls back to `start` on reaching `end`.

    Signature: `counter(model, start, end)`
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model_counter = Model(starttime=1.0, stoptime=22.0, dt=0.25, name='counter')
    weekday = model_counter.converter('weekday')
    weekday.equation = sd.counter(model_counter, 1.0, 8.0)
    weekday.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## DELAY Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The DELAY function returns a delayed value of input, using a lag time of delay duration, and an optional initial value initial for the delay. If you don't specify an initial value initial, DELAY assumes the value to be the initial value of input. A delay duration that changes during the run is read at every step, so the lag follows it - Stella fixes it at its initial value instead. A negative delay duration would read the future: it gives NaN and an `[ERROR]`, as Stella refuses it.

    Signature: `delay(model, input_function, delay_duration, initial_value)`

    Each argument can be a number, a model element or an expression.
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_2 = Model(starttime=0.0, stoptime=10.0, dt=0.5, name='delay')
    input_function = model_2.converter('input_function')
    input_function.equation = sd.time()
    delayed_input_1 = model_2.converter('delayed_input_1')
    delayed_input_2 = model_2.converter('delayed_input_2')
    delayed_input_3 = model_2.converter('delayed_input_3')
    delayed_input_1.equation = sd.delay(model_2, input_function, 1.0, 1.0)
    delayed_input_2.equation = sd.delay(model_2, input_function, 2.0, 0.0)
    delayed_input_3.equation = sd.delay(model_2, input_function, 2.5, 0.5)
    bptk.reset_all_scenarios()
    bptk.register_model(model_2)
    bptk.plot_scenarios(
        scenario_managers=['smDelay'],
        scenarios=['base'],
        equations=['input_function', 'delayed_input_1', 'delayed_input_2', 'delayed_input_3'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## DELAY1 / DELAY3 / DELAYN Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    DELAY1, DELAY3 and DELAYN are material delays of first, third and n-th order: what goes in comes out again, spread over time. `delay1` is one stock that drains at its content divided by the delay time. `delay3` and `delayn` chain three or n such stocks, each with its share of the delay time, so the output starts later and rises more steeply - the higher the order, the closer it comes to DELAY.

    With a constant delay time they behave exactly like SMOOTH, SMOOTH3 and SMOOTHN. When the delay time changes they do not: a material delay passes on everything that went in, a smooth does not.

    Signatures: `delay1(model, input_function, delay_time, initial_value=None)`, `delay3(model, input_function, delay_time, initial_value=None)` and `delayn(model, input_function, delay_time, order, initial_value=None)`

    `delay_time`: any model element

    `initial_value`: the output at the start, a number, a model element or an expression. Left out, the delay starts at the input

    `order`: a whole number between 1 and 255. `delayn` keeps every stage at least one `dt` long, so a delay shorter than `order * dt` is lengthened to that, as in Stella
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_delays = Model(starttime=0.0, stoptime=20.0, dt=0.25, name='delays')
    delays_input = model_delays.converter('step_input')
    delays_input.equation = 5.0 + sd.step(10.0, 3.0)
    model_delays.converter('delay1').equation = sd.delay1(model_delays, delays_input, 5.0)
    model_delays.converter('delay3').equation = sd.delay3(model_delays, delays_input, 5.0)
    model_delays.converter('delay9').equation = sd.delayn(model_delays, delays_input, 5.0, 9)
    bptk.reset_all_scenarios()
    bptk.register_model(model_delays)
    bptk.plot_scenarios(
        scenario_managers=['smDelays'],
        scenarios=['base'],
        equations=['step_input', 'delay1', 'delay3', 'delay9'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## DERIVN Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    DERIVN is the n-th derivative of a variable over time, taken as repeated differences over one `dt`. It is 0 for the first `order` steps, because there is no earlier value to take a difference from.

    Signature: `derivn(model, variable, order)`

    `order`: a whole number of at least 0
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_derivn = Model(starttime=0.0, stoptime=10.0, dt=0.25, name='derivn')
    distance = model_derivn.converter('distance')
    distance.equation = sd.time() ** 2.0
    model_derivn.converter('speed').equation = sd.derivn(model_derivn, distance, 1)
    model_derivn.converter('acceleration').equation = sd.derivn(model_derivn, distance, 2)
    bptk.reset_all_scenarios()
    bptk.register_model(model_derivn)
    bptk.plot_scenarios(
        scenario_managers=['smDerivn'],
        scenarios=['base'],
        equations=['speed', 'acceleration'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## DT Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `DT` function returns the model's dt.

    Signature: `dt(model)`
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model_3 = Model(starttime=5, stoptime=12, dt=0.25, name='dt')
    dt = model_3.converter('dt')
    dt.equation = sd.dt(model_3)
    dt.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## EXP Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `exp` function returns the exponential value of the input.

    Signature: `exp(element)`

    `element` can be any model element (stock, flow, converter, constant)
    """)
    return


@app.cell
def _(Model, np, sd):
    #| echo: true
    model_4 = Model(starttime=0, stoptime=10, dt=0.1, name='exp')
    growth_rate = model_4.constant('growth_rate')
    growth_rate.equation = np.log(2)
    exp = model_4.converter('exp')
    exp.equation = sd.exp(growth_rate * sd.time())
    exp.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## EXPBOUND / LOGISTICBOUND Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Both functions take a value from `y_from` to `y_to` while `x` moves along, as Stella's `EXPBOUND` and `LOGISTICBOUND` do, with the same arguments in the same order.

    `expbound(y_from, y_to, x, exponent, x_start, x_finish)` is `y_from` up to `x_start` and `y_to` from `x_finish` on. In between it follows an exponential curve: a positive `exponent` starts slowly and rises steeply at the end, a negative one the other way round, and `0` gives a straight line.

    `logisticbound(y_from, y_to, x, x_middle, speed, x_start=None, x_finish=None)` is an S-curve, halfway between `y_from` and `y_to` at `x_middle`; `speed` sets how steep it is there. Without `x_start` and `x_finish` it only comes close to `y_from` and `y_to`. With them - both or neither - it reaches `y_from` at `x_start` and `y_to` at `x_finish` and holds them beyond: each half of the curve is bent by a straight line until it does. A `speed` of `0` makes the curve two straight lines that meet at `x_middle`.
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_bounds = Model(starttime=0.0, stoptime=12.0, dt=0.25, name='bounds')
    model_bounds.converter('slow_start').equation = sd.expbound(1.0, 9.0, sd.time(), 2.0, 2.0, 8.0)
    model_bounds.converter('fast_start').equation = sd.expbound(1.0, 9.0, sd.time(), -2.0, 2.0, 8.0)
    model_bounds.converter('s_curve').equation = sd.logisticbound(1.0, 9.0, sd.time(), 5.0, 1.0)
    model_bounds.converter('s_curve_bounded').equation = sd.logisticbound(1.0, 9.0, sd.time(), 5.0, 1.0, 1.0, 10.0)
    bptk.reset_all_scenarios()
    bptk.register_model(model_bounds)
    bptk.plot_scenarios(
        scenario_managers=['smBounds'],
        scenarios=['base'],
        equations=['slow_start', 'fast_start', 's_curve', 's_curve_bounded'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## FACTORIAL Function
    The FACTORIAL function calculates the factorial of the single argument `n` (traditionally noted as n!). `n` must be a whole number of at least 0; a fraction or a negative number gives NaN and an `[ERROR]`. From 171 on the result is infinity.

    The following example wraps the time `t` in a user-defined function to ensure that this value is always an integer.
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_7 = Model(starttime=0, stoptime=5, dt=1)
    f_6 = m_7.flow(name='factorial')
    n_2 = m_7.function('n', lambda model, t: int(t))
    f_6.equation = sd.factorial(n_2())
    f_6.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## FORECAST Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    FORECAST extrapolates the input over a horizon with its trend: `input * (1 + trend * horizon)`, where the trend is that of TREND with the same averaging time and initial trend.

    Signature: `forecast(model, input_function, averaging_time, horizon, initial_trend=0.0)`

    `averaging_time`, `horizon`: any model element

    `initial_trend`: the trend at the start, a number, a model element or an expression
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_forecast = Model(starttime=0.0, stoptime=20.0, dt=0.25, name='forecast')
    sales = model_forecast.converter('sales')
    sales.equation = 100.0 + sd.step(50.0, 5.0)
    model_forecast.converter('forecast').equation = sd.forecast(model_forecast, sales, 4.0, 5.0)
    bptk.reset_all_scenarios()
    bptk.register_model(model_forecast)
    bptk.plot_scenarios(
        scenario_managers=['smForecast'],
        scenarios=['base'],
        equations=['sales', 'forecast'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## GAMMALN Function

    The GAMMALN operator returns the natural log of the GAMMA function, given input n. The GAMMA function is a continuous version of the FACTORIAL builtin, with GAMMA(n) the same as FACTORIAL(n-1). For `n` of 0 and below it gives NaN, as Stella does.

    Only argument is ``n``
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_9 = Model(starttime=0, stoptime=10, dt=0.1)
    f_8 = m_9.biflow(name='gammaln')
    n_3 = sd.time()
    f_8.equation = sd.gammaln(n_3)
    f_8.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## IF / THEN / ELSE / AND / NOT / OR

    It is possible to write up if clauses. We even support NOT and AND / OR operators.

    Please note that these function names begin with a capital letter. This is because the actual words ``if, and, or`` etc. are protected in Python and cannot / should not be overwritten.

    An if clause requires 3 arguments: ``If ( <condition> , <then>, <else>)``

    ``condition``: Must be a boolean expression, e.g. ``sd.time() > 1`` is true iff the simulation time is larger than 1
    ``then``: Any expression that returns a float value if the condition is true
    ``else``: Any expression that returns a float value if the condition is false

    A simple if clause may look like this:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model = Model(starttime=0.0,stoptime=10.0,dt=0.1,name='if')
    converter = model.converter("converter")
    converter.equation = sd.If( sd.time()>5, 10, 5 )
    converter.plot(format="axes")
    return (converter,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You see that its value is 5 until ``t`` reaches 6.

    You can also add ``and`` / ``or`` / ``not`` conditions easily:

    Signature:
    ``And(<condition1>, <condition2>)``: Logical and between 2 conditions
    ``Or(<condition1>, <condition2>)``: Logical or between 2 conditions
    ``Not(<condition>)``: Logical not: True if condition is False

    Each condition within the operators has to return a boolean value. Nesting of the operators is easily possible!
    """)
    return


@app.cell
def _(converter, sd):
    #| echo: true
    converter.equation = sd.If( sd.And(sd.time()>5,sd.time()>10), 10, 5 ) # 5 (else case) as long as t <= 10, then 10
    converter.equation = sd.If( sd.Or( sd.And(sd.time()>5,sd.time()>10), True), 10, 5 ) # Always 10 (then condition, because Or always evaluates to True)
    converter.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## INIT / PREVIOUS / HISTORY Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Three ways to read what a variable was earlier in the run. `init` is its value at the start. `previous` is its value one `dt` back, and `initial_value` at the first step - which also lets a variable refer to its own last value, as XMILE's `PREVIOUS(SELF, ...)` does. `history` is its value at a given time; for a time after the current one or before the start it gives 0, as Stella does.

    Signatures: `init(model, variable)`, `previous(model, variable, initial_value)` and `history(model, variable, time)`

    `variable` is a model element or an expression; `initial_value` and `time` can be numbers, model elements or expressions.
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_past = Model(starttime=0.0, stoptime=10.0, dt=0.5, name='past')
    position = model_past.converter('position')
    position.equation = sd.time() ** 2.0
    model_past.converter('start').equation = sd.init(model_past, position)
    model_past.converter('one_step_back').equation = sd.previous(model_past, position, 0.0)
    model_past.converter('two_time_units_ago').equation = sd.history(model_past, position, sd.time() - 2.0)
    steps = model_past.converter('steps')
    steps.equation = sd.previous(model_past, steps, 0.0) + 1.0
    bptk.reset_all_scenarios()
    bptk.register_model(model_past)
    bptk.plot_scenarios(
        scenario_managers=['smPast'],
        scenarios=['base'],
        equations=['position', 'start', 'one_step_back', 'two_time_units_ago', 'steps'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## INVNORM Function

    The INVNORM operator calculates the inverse of the NORMALCDF function (see below): the value below which a share ``p`` of a normal distribution lies.

    Parameters are the ``probability p`` (between 0 and 1), and optionally the ``mean`` (default 0) and the ``stddev`` (default 1). Either of the two may be given without the other.

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_11 = Model(starttime=0.05, stoptime=0.95, dt=0.05)
    f_10 = m_11.biflow(name='invnorm')
    p_2 = sd.time()
    f_10.equation = sd.invnorm(p_2, mean=100, stddev=15)
    f_10.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## IRR Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    IRR is the internal rate of return of a stream of payments so far: the rate at which their net present value is zero, each value discounted by `(1 + rate) ** (TIME - STARTTIME)`. The stream needs payments in both directions. Where there are several such rates the one nearest zero is taken, and where there is none - at the first step, or for a stream that only ever pays in - the function gives `missing`, or NaN without one.

    The example pays 100 in the first year and gets 10 back every year after. The rate of return starts deep below zero and climbs towards 10 percent as the payments go on.

    Signature: `irr(model, stream, missing=None)`
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model_irr = Model(starttime=1.0, stoptime=40.0, dt=1.0, name='irr')
    cash_flow = model_irr.converter('cash_flow')
    cash_flow.equation = sd.If(sd.time() < 2.0, -100.0, 10.0)
    model_irr.converter('return_rate').equation = sd.irr(model_irr, cash_flow)
    model_irr.converter('return_rate').plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## LN / LOG10 Functions

    ``ln`` returns the natural logarithm of its input, ``log10`` the logarithm to base 10.

    Signature:
    ``ln(expression)`` and ``log10(expression)``

    ``expression`` can be any element that returns a positive float value - the logarithm of
    zero or of a negative number is undefined, so make sure your input stays above zero over
    the whole simulation period.

    The example below starts at ``t = 1`` for exactly that reason:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model_ln = Model(starttime=1.0, stoptime=10.0, dt=0.1, name='logarithms')
    natural_log = model_ln.converter('natural_log')
    natural_log.equation = sd.ln(sd.time())
    log_base_10 = model_ln.converter('log_base_10')
    log_base_10.equation = sd.log10(sd.time())
    natural_log.plot(format="axes")
    return


@app.cell
def _(log_base_10):
    #| echo: true
    log_base_10.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## LOOKUP Function

    ``lookup`` evaluates a *graphical function*: a relationship you give as a list of points
    rather than as a formula. Between two points the value is interpolated linearly; outside
    the given range it stays at the first or last point.

    Signature:
    ``lookup(element, points, kind="continuous")``

    ``element`` is the input to look up, ``points`` a list of ``(x, y)`` tuples, in any
    order - they are sorted by ``x``. Two points at the same ``x`` are refused with an
    error naming it, since the table would have two values there.

    ``kind`` is the type of the graphical function; XMILE has three:

    - ``"continuous"``, the default: linear between the points, the first or the last value
      outside them
    - ``"extrapolate"``: linear between the points, and outside them on along the first or
      the last segment
    - ``"discrete"``: a step function - the value of the nearest point at or below the input,
      the first value below the table

    In XMILE and Stella the type belongs to the graphical function itself; in the SD DSL it is
    given where the table is read, so a table read in several places needs it in each.

    This is the DSL equivalent of a graphical function in a XMILE model, and it is the right
    tool whenever a relationship is known empirically but has no closed form:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model_lookup = Model(starttime=0.0, stoptime=10.0, dt=0.1, name='lookup')
    effectiveness = model_lookup.converter('effectiveness')
    effectiveness.equation = sd.lookup(
        sd.time(), [(0.0, 0.0), (2.0, 0.8), (5.0, 1.0), (8.0, 0.4), (10.0, 0.1)]
    )
    effectiveness.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The same table read three ways, with an input that runs past both of its ends:
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_kinds = Model(starttime=0.0, stoptime=12.0, dt=0.1, name='kinds')
    model_kinds.points['peak'] = [(2.0, 0.0), (4.0, 5.0), (6.0, 20.0), (8.0, 10.0), (10.0, 0.0)]
    for kind in ('continuous', 'extrapolate', 'discrete'):
        model_kinds.converter(kind).equation = sd.lookup(sd.time(), 'peak', kind=kind)
    bptk.reset_all_scenarios()
    bptk.register_model(model_kinds)
    bptk.plot_scenarios(
        scenario_managers=['smKinds'],
        scenarios=['base'],
        equations=['continuous', 'extrapolate', 'discrete'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## LOOKUPINV / LOOKUPAREA Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `lookupinv` reads a lookup table backwards: the `x` at which it reaches a value. It is meant for a table that only rises or only falls; a value beyond what the table reaches gives the `x` of the nearer end - on a table that does not only rise or only fall it gives NaN, as in Stella. `lookuparea` is the area under the table between two `x` values, or under all of it; as in Stella, nothing beyond the table's ends counts.

    Signatures: `lookupinv(value, points, kind="continuous")` and `lookuparea(points, from_x=None, to_x=None, kind="continuous")`

    `points` is a list of `(x, y)` points or the name of a table in `model.points`, and `kind` the type of table, as for `lookup`. On an extrapolate table `lookupinv` goes on along the end segments and `lookuparea` counts the lines beyond the ends too; a discrete table's area is the sum of its steps, and `lookupinv` reads it as continuous, as Stella does.

    The example feeds the time into the same table three ways: `forwards` reads it as `lookup` does, `backwards` asks at which `x` the table reaches the time, and `area_so_far` is the area under the table from 0 to the time. Past the last point at `x = 4` the table stays at 6, so `backwards` stops at 4 once the time reaches 6, and the area stops growing at 14.
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_lookups = Model(starttime=0.0, stoptime=6.0, dt=0.25, name='lookups')
    model_lookups.points['demand'] = [(0.0, 0.0), (2.0, 4.0), (4.0, 6.0)]
    model_lookups.converter('forwards').equation = sd.lookup(sd.time(), 'demand')
    model_lookups.converter('backwards').equation = sd.lookupinv(sd.time(), 'demand')
    model_lookups.converter('area_so_far').equation = sd.lookuparea('demand', 0.0, sd.time())
    bptk.reset_all_scenarios()
    bptk.register_model(model_lookups)
    bptk.plot_scenarios(
        scenario_managers=['smLookups'],
        scenarios=['base'],
        equations=['forwards', 'backwards', 'area_so_far'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## LOOKUPMAX / LOOKUPMIN / LOOKUPMEAN Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `lookupmax` and `lookupmin` are the largest and the smallest value of a lookup table, between two `x` values or over all of it; a bound inside a segment counts with the value the table has there. `lookupmean` reads the table as a probability density and gives its mean `x` - the average of what `lookuprandom` draws from it. As in Stella, each segment counts as flat at its average height, so on a sloping segment the mean is the segment's middle; a table that has no area in the range gives NaN.

    Signatures: `lookupmax(points, from_x=None, to_x=None, kind="continuous")`, and the same for `lookupmin` and `lookupmean`

    `points` and `kind` are as for `lookup`. `from_x` and `to_x` can come in either order. Stella writes the range the other way round - `LOOKUPMAX(table, to, from)`, with `from` left out meaning the start of the table - so `LOOKUPMAX(table, 8)` is `sd.lookupmax("table", to_x=8.0)`. Beyond the table's ends `lookupmax` and `lookupmin` read it as `lookup` does, while `lookupmean` counts nothing there, except on an extrapolate table.

    In the example the table rises to a peak of 20 at `x = 6`. `window_max` and `window_min` look at the two units of `x` up to the time; `mean_so_far` is the mean `x` of the table from its start up to the time:
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_lookup_statistics = Model(starttime=2.0, stoptime=12.0, dt=0.25, name='lookup_statistics')
    model_lookup_statistics.points['peak'] = [(2.0, 0.0), (4.0, 5.0), (6.0, 20.0), (8.0, 10.0), (10.0, 0.0)]
    model_lookup_statistics.converter('window_max').equation = sd.lookupmax('peak', sd.time() - 2.0, sd.time())
    model_lookup_statistics.converter('window_min').equation = sd.lookupmin('peak', sd.time() - 2.0, sd.time())
    model_lookup_statistics.converter('mean_so_far').equation = sd.lookupmean('peak', None, sd.time())
    bptk.reset_all_scenarios()
    bptk.register_model(model_lookup_statistics)
    bptk.plot_scenarios(
        scenario_managers=['smLookup_statistics'],
        scenarios=['base'],
        equations=['window_max', 'window_min', 'mean_so_far'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## MAX Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `max` function always chooses the largest of its input values - two or more.

    Signature: `max(element, element, ...)`

    `element` can be any model element (stock, flow, converter, constant)
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model_5 = Model(starttime=0.0, stoptime=10.0, dt=1.0, name='max')
    a = model_5.converter('a')
    a.equation = 5.0+sd.step(5.0, 5.0)
    a.plot(format="axes")
    return a, model_5


@app.cell
def _(model_5, sd):
    #| echo: true
    b = model_5.converter('b')
    b.equation= 10.0 - sd.step(5.0, 5.0)
    b.plot(format="axes")
    return (b,)


@app.cell
def _(a, b, bptk, model_5, sd):
    #| echo: true
    c = model_5.converter('c')
    c.equation=sd.max(a,b)
    bptk.reset_all_scenarios()
    bptk.register_model(model_5)
    bptk.plot_scenarios(scenario_managers=['smMax'], scenarios=['base'], equations=['a', 'b', 'c'], format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## MIN Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `min` function always chooses the smallest of its input values - two or more.

    Signature: `min(element, element, ...)`

    `element` can be any model element (stock, flow, converter, constant)
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_6 = Model(starttime=0, stoptime=10, dt=1, name='min')
    a_1 = model_6.converter('a')
    a_1.equation = 5.0 + sd.step(5.0, 5.0)
    b_1 = model_6.converter('b')
    b_1.equation = 10.0 - sd.step(5.0, 5.0)
    c_1 = model_6.converter('c')
    c_1.equation = sd.min(a_1, b_1)
    bptk.reset_all_scenarios()
    bptk.register_model(model_6)
    bptk.plot_scenarios(scenario_managers=['smMin'], scenarios=['base'], equations=['a', 'b', 'c'], format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## MAXSOFT / MINSOFT Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `maxsoft(x, y, softness)` is a maximum with a rounded corner, Stella's `MAXSOFT`. It is `x` as long as `x` lies at least `softness` above `y`. Below that it does not switch to `y` at a kink but bends towards it, and approaches it only gradually: where `x` and `y` are equal, the result is still about a quarter of `softness` above them. A `softness` of `0` is the plain `max`.

    `minsoft(x, y, softness)` is the mirror image, Stella's `MINSOFT`: `x` as long as it lies at least `softness` below `y`, then bending towards `y` from below.

    In the example a falling `x` meets a floor of 1, once hard and twice softened:
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_soft = Model(starttime=0.0, stoptime=12.0, dt=0.25, name='soft')
    falling = model_soft.converter('falling')
    falling.equation = 6.0 - sd.time()
    model_soft.converter('hard').equation = sd.maxsoft(falling, 1.0, 0.0)
    model_soft.converter('soft_2').equation = sd.maxsoft(falling, 1.0, 2.0)
    model_soft.converter('soft_5').equation = sd.maxsoft(falling, 1.0, 5.0)
    bptk.reset_all_scenarios()
    bptk.register_model(model_soft)
    bptk.plot_scenarios(
        scenario_managers=['smSoft'],
        scenarios=['base'],
        equations=['hard', 'soft_2', 'soft_5'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## NAN / INF / PI / ISNAN

    ``sd.nan()`` returns a NAN value, ``sd.Inf()`` gives you the infinity value, ```sd.pi()``` returns the number pi.

    ``sd.isnan(x)`` is 1 where `x` is NaN and 0 otherwise, as Stella's `ISNAN`. A comparison cannot do this: NaN is unequal to every number, itself included.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## NORMALCDF Function
    The NORMALCDF operator calculates the cumulative Normal distribution function between the specified z-scores, or, when the mean and stddev (standard deviation) are given, between two data values.

    Arguments are the ``left`` and ``right`` boundaries and optionally ``mean`` and ``stddev``. If not given, mean will be set to 0, stddev to 1.

    A really simple example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_16 = Model(starttime=-4, stoptime=4, dt=0.1)
    f_15 = m_16.biflow(name='normalCDF')
    left = -4
    right = sd.time()
    mean_4 = 0
    stddev = 1
    f_15.equation = sd.normalcdf(left, right, mean_4, stddev)
    f_15.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## NPV Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    NPV accumulates the net present value of a stream: in every step the input, discounted by `1 / (1 + rate) ** (TIME - STARTTIME + DT)`, is added. `rate` is the discount rate per time unit of the model.

    Signature: `npv(model, input_function, rate, initial_value=None)`

    `rate`: any model element

    `initial_value`: where the value starts, a number, a model element or an expression. Left out, it starts at the input, as in Stella
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_npv = Model(starttime=0.0, stoptime=20.0, dt=1.0, name='npv')
    payments = model_npv.converter('payments')
    payments.equation = 100.0
    model_npv.converter('npv').equation = sd.npv(model_npv, payments, 0.05, 0.0)
    model_npv.converter('undiscounted').equation = sd.npv(model_npv, payments, 0.0, 0.0)
    bptk.reset_all_scenarios()
    bptk.register_model(model_npv)
    bptk.plot_scenarios(
        scenario_managers=['smNpv'],
        scenarios=['base'],
        equations=['npv', 'undiscounted'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## PERMUTATIONS
    The PERMUTATIONS operator calculates the number of permutations of an n-element set with r-element subsets.

    Arguments are ``n`` and ``r``, whole numbers of at least 0; anything else gives NaN and an ``[ERROR]``. An ``r`` greater than ``n`` gives 0.

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_18 = Model(starttime=1, stoptime=10, dt=0.1)
    f_17 = m_18.biflow(name='permutations')
    n_4 = 7.0
    r_1 = 3
    f_17.equation = sd.permutations(n_4, r_1)
    f_17.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## PMT / FV / PV Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The three financial functions of a loan or a savings plan with a fixed rate per period, signed as in a spreadsheet: money paid out is negative.

    Signatures: `pmt(rate, periods, present_value, future_value=0.0)` - the payment per period; `fv(rate, periods, payment, present_value=0.0)` - the value after the periods; `pv(rate, periods, payment, future_value=0.0)` - the value today. All arguments can be model elements.

    The example takes the number of periods from the time, so each curve shows one function over loans and savings plans of 1 to 20 years at 5 percent: the instalment on a loan of 1000, the savings from paying in 100 a year, and the loan that 100 a year pays off.
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_financial = Model(starttime=1.0, stoptime=20.0, dt=1.0, name='financial')
    periods = sd.time()
    model_financial.converter('instalment').equation = sd.pmt(0.05, periods, 1000.0)
    model_financial.converter('savings').equation = sd.fv(0.05, periods, -100.0)
    model_financial.converter('loan').equation = sd.pv(0.05, periods, -100.0)
    bptk.reset_all_scenarios()
    bptk.register_model(model_financial)
    bptk.plot_scenarios(
        scenario_managers=['smFinancial'],
        scenarios=['base'],
        equations=['instalment', 'savings', 'loan'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## PULSE Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `PULSE` function generates a pulse input of a specified size (volume). When using the PULSE builtin, you have the option of setting the time at which the PULSE will first fire (first pulse), as well as the interval between subsequent PULSEs. Each time that it fires a pulse, the framework pulses the specified volume over a period of one time step (DT). Thus, the instantaneous value taken on by the PULSE function is volume/DT.

    Signature: `pulse(model, volume, first_pulse=None, interval=0)`

    Without `first_pulse` the pulse fires at the start time. A pulse time between two steps fires in the step after it, so no volume is lost. Setting `interval` to 0 - or leaving it out - yields a single pulse that doesn't repeat, as in the XMILE standard; Stella differs here, see [XMILE, Stella and the SD DSL](../../xmile/xmile_in_the_sd_dsl/xmile_in_the_sd_dsl.md#xmile-stella-and-the-sd-dsl).

    Each argument can be a number, a model element or an expression, and is read at every step.
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_7 = Model(starttime=0.0, stoptime=10.0, dt=0.25, name='pulse')
    stock = model_7.stock('stock')
    stock.initial_value = 0.0
    flow = model_7.flow('flow')
    flow.equation = sd.pulse(model_7, 10.0, 2.0, 2.0)
    stock.equation = flow
    bptk.reset_all_scenarios()
    bptk.register_model(model_7)
    bptk.plot_scenarios(
        scenario_managers=['smPulse'],
        scenarios=['base'],
        equations=['stock', 'flow'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## RAMP Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    RAMP is 0 until `start_time` and then rises with `slope`; from `end_time` on, if one is given, it holds the value it has reached.

    Signature: `ramp(slope, start_time, end_time=None)`
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_ramp = Model(starttime=0.0, stoptime=15.0, dt=0.25, name='ramp')
    model_ramp.converter('ramp').equation = sd.ramp(2.0, 3.0)
    model_ramp.converter('ramp_until_8').equation = sd.ramp(2.0, 3.0, 8.0)
    bptk.reset_all_scenarios()
    bptk.register_model(model_ramp)
    bptk.plot_scenarios(
        scenario_managers=['smRamp'],
        scenarios=['base'],
        equations=['ramp', 'ramp_until_8'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## REWORK Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `rework(percentage)` is Stella's `REWORK`: the fraction for a flow that sends work back upstream to be done again, chosen so that `percentage` percent of all the work that enters comes back - not `percentage` percent of each pass. With the plain fraction `percentage / 100` the reworked units would be inspected again and fail again, so more than that would come back over the run; `rework(10.0)` is 10 / 110, about 0.0909.

    In the example 100 units enter at time 1 and pass an inspection that sends `rework(10.0)` of them back; 10 units fail in all, and all 100 get through in the end:
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_rework = Model(starttime=0.0, stoptime=20.0, dt=1.0, name='rework')
    wip = model_rework.stock('wip')
    done = model_rework.stock('done')
    failed_in_all = model_rework.stock('failed_in_all')
    entering = model_rework.flow('entering')
    inspecting = model_rework.flow('inspecting')
    failing = model_rework.flow('failing')
    entering.equation = sd.pulse(model_rework, 100.0, 1.0)
    inspecting.equation = wip
    failing.equation = inspecting * sd.rework(10.0)
    wip.equation = entering - inspecting + failing
    done.equation = inspecting - failing
    failed_in_all.equation = failing
    bptk.reset_all_scenarios()
    bptk.register_model(model_rework)
    bptk.plot_scenarios(
        scenario_managers=['smRework'],
        scenarios=['base'],
        equations=['done', 'failed_in_all'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ROUND Function

    This function rounds any input to a specified number of digits. A half rounds away
    from zero, as a spreadsheet rounds: 2.5 becomes 3, -2.5 becomes -3.

    Signature:
    ``round(expression, digits)``

    ``expression`` can be any float input by any expression.
    ``digits`` must be an int value

    The example rounds a sine wave with an amplitude of 2.5 to whole numbers. At its peaks the wave is exactly 2.5 and -2.5, and the rounded curve reaches 3 and -3 there:
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_14 = Model(starttime=0.0, stoptime=10.0, dt=0.25, name='round')
    wave = model_14.converter('wave')
    wave.equation = sd.sinwave(2.5, 10.0)
    model_14.converter('rounded').equation = sd.round(wave, 0)
    bptk.reset_all_scenarios()
    bptk.register_model(model_14)
    bptk.plot_scenarios(
        scenario_managers=['smRound'],
        scenarios=['base'],
        equations=['wave', 'rounded'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## RUNCUM / RUNMAX / RUNMIN / RUNMEAN / RUNCUMTARGET Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    These functions look back over the run so far, as Stella's functions of the same names do.

    Signatures: `runcum(model, variable, from_time=None, to_time=None)`, and the same for `runmax`, `runmin` and `runmean`; `runcumtarget(model, variable, target)`

    - `runcum` is the sum of the values times DT - the area under the variable, as a stock filled by it would hold, but with the current step already counted.
    - `runmax` and `runmin` are the largest and the smallest value, `runmean` the mean of the values.
    - `from_time` and `to_time` make a window, both ends included: `sd.runmax(model, orders, sd.time() - 3.0, sd.time())` is the largest value of the last three time units. Left out, they are the start of the run and the current time; the current step is the last one any window can reach. A window without a step in it - `sd.runcum(model, orders, sd.starttime(model), sd.time() - sd.dt(model))` at the start - gives NaN.
    - `runcumtarget` is the time at which the running sum reaches `target`, interpolated within the step that gets there; NaN until then. Like Stella, it sums the **magnitude** of the variable, so a negative value counts towards the target as much as a positive one - unlike `runcum`.

    `variable` can be an element or an expression. Stella's further arguments, which read another run, have no counterpart.

    In the example `orders` swing around a rising line. `last_3_max` follows their peaks over the last three time units; `reached_500` is the time at which 500 units have been ordered, a little after 4:
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_running = Model(starttime=0.0, stoptime=12.0, dt=0.25, name='running')
    orders = model_running.converter('orders')
    orders.equation = 100.0 + 40.0 * sd.sinwave(1.0, 6.0) + 5.0 * sd.time()
    model_running.converter('last_3_max').equation = sd.runmax(model_running, orders, sd.time() - 3.0, sd.time())
    model_running.converter('mean_so_far').equation = sd.runmean(model_running, orders)
    model_running.converter('reached_500').equation = sd.runcumtarget(model_running, orders, 500.0)
    bptk.reset_all_scenarios()
    bptk.register_model(model_running)
    bptk.plot_scenarios(
        scenario_managers=['smRunning'],
        scenarios=['base'],
        equations=['orders', 'last_3_max', 'mean_so_far', 'reached_500'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## SAFEDIV / ROOTN / PERCENT Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `safediv(numerator, denominator, on_zero=0.0)` divides, and gives `on_zero` where the denominator is zero. `rootn(x, n)` is the n-th root - of a negative number only for an odd `n`, NaN otherwise. `percent(x)` is `x` times 100.

    In the example the denominator, `time - 5`, passes through zero at time 5: `quotient` is -1 there instead of an error, and very large on either side. `cube_root` takes the root of the same numbers, negative ones included, and `share` turns `time / 100` into percent.
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_misc = Model(starttime=0.0, stoptime=10.0, dt=0.5, name='misc')
    centred = sd.time() - 5.0
    model_misc.converter('quotient').equation = sd.safediv(10.0, centred, -1.0)
    model_misc.converter('cube_root').equation = sd.rootn(centred, 3.0)
    model_misc.converter('share').equation = sd.percent(sd.time() / 100.0)
    bptk.reset_all_scenarios()
    bptk.register_model(model_misc)
    bptk.plot_scenarios(
        scenario_managers=['smMisc'],
        scenarios=['base'],
        equations=['quotient', 'cube_root', 'share'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## SIN / TAN / COS and ARCCOS / ARCSIN / ARCTAN

    The SD DSL supports all trigonometric functions that you are also used to from other SD simulation / modelling tools.

    Use ``sd.sin(x) / sd.cos(x) / sd.tan(x)`` for sine, cosine or tangent of x (radians) and ``sd.arcsin(x) / sd.arctan(x) / sd.arccos(x)`` for the respective arctan / arccos and arcsine operators.

    Let's easily plot sin / cos and tan for the current simulation time:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_1 = Model(starttime=0, stoptime=10, dt=0.1)
    x = sd.time()
    sin = m_1.biflow(name='sin')
    sin.equation = sd.sin(x)
    sin.plot(format="axes")
    return m_1, x


@app.cell
def _(m_1, sd, x):
    #| echo: true
    tan = m_1.biflow(name='tan')
    tan.equation = sd.tan(x)
    tan.plot(format="axes")
    return


@app.cell
def _(m_1, sd, x):
    #| echo: true
    cos = m_1.biflow(name='cos')
    cos.equation = sd.cos(x)
    cos.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## SINWAVE and COSWAVE Functions

    SINWAVE returns a time-dependent sine wave, with the specified amplitude and period. To generate the sine wave, the SINWAVE builtin uses the absolute value of the amplitude you specify. To produce meaningful wave results, choose a DT that's significantly smaller than the period of the wave. A DT equal to a quarter of the period gives triangle waves. A smaller DT gives results which better approximate a continuous curve.

    COSWAVE generates a time-dependent __cosine__ wave. It uses the same arguments.

    Signature:
    ``sinwave(amplitude,period)``

    ``amplitude``: Amplitude of the sine wave
    ``period``: Period of the sine wave

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_2 = Model(starttime=0, stoptime=10, dt=0.1)
    amplitude = 10
    period = 5
    f_1 = m_2.biflow(name='sinwave')
    f_1.equation = sd.sinwave(amplitude, period)
    f_1.plot(format="axes")
    return amplitude, m_2, period


@app.cell
def _(amplitude, m_2, period, sd):
    #| echo: true
    g = m_2.biflow('coswave')
    g.equation = sd.coswave(amplitude, period)
    g.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## SMOOTH Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The SMOOTH function calculates the exponential average of the input, given the input function, an averaging time and, optionally, an initial value.

    Signature: `smooth(model, input_function, averaging_time, initial_value=None)`

    `model`: The model you are writing equations for

    `input_function`: any model element

    `averaging_time`: any model element

    `initial_value`: a number, a model element or an expression. Left out, the average starts at the input

    The SMOOTH operator is a shorthand for the following stock and flow structure and equations:

    ![Stock and Flow Structure for the SMOOTH Operator](smooth_model.png)
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_8 = Model(starttime=1.0, stoptime=10.0, dt=0.1, name='smooth')
    input_function_1 = model_8.converter('input_function')
    input_function_1.equation = sd.step(10.0, 3.0)
    smooth = model_8.converter('smooth')
    smooth.equation = sd.smooth(model_8, input_function_1, 2.0, 0.0)
    bptk.reset_all_scenarios()
    bptk.register_model(model_8)
    bptk.plot_scenarios(
        scenario_managers=['smSmooth'],
        scenarios=['base'],
        equations=['input_function', 'smooth'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## SMOOTH3 / SMOOTHN Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    SMOOTH3 and SMOOTHN smooth the input in three or n stages, each with its share of the averaging time. The output reacts later than with SMOOTH and approaches the input in an S-curve rather than at once.

    Signatures: `smooth3(model, input_function, averaging_time, initial_value=None)` and `smoothn(model, input_function, averaging_time, order, initial_value=None)`

    `averaging_time`: any model element

    `initial_value`: a number, a model element or an expression. Left out, the smooth starts at the input

    `order`: a whole number between 1 and 255. `smoothn` keeps every stage at least one `dt` long, as in Stella
    """)
    return


@app.cell
def _(Model, bptk, sd):
    #| echo: true
    model_smooths = Model(starttime=0.0, stoptime=20.0, dt=0.25, name='smooths')
    smooths_input = model_smooths.converter('step_input')
    smooths_input.equation = 5.0 + sd.step(10.0, 3.0)
    model_smooths.converter('smooth').equation = sd.smooth(model_smooths, smooths_input, 5.0)
    model_smooths.converter('smooth3').equation = sd.smooth3(model_smooths, smooths_input, 5.0)
    model_smooths.converter('smooth9').equation = sd.smoothn(model_smooths, smooths_input, 5.0, 9)
    bptk.reset_all_scenarios()
    bptk.register_model(model_smooths)
    bptk.plot_scenarios(
        scenario_managers=['smSmooths'],
        scenarios=['base'],
        equations=['step_input', 'smooth', 'smooth3', 'smooth9'],
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## SQRT
    Computes the square root of an input expression. A negative input gives NaN and an `[ERROR]`.

    Signature:
    ``sqrt(expression)``

    ``expression`` can be any element that returns a float value.

    Simple Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m= Model(starttime=0,stoptime=10,dt=1)
    f = m.flow(name="sqrt")

    val = sd.time() 

    f.equation = sd.sqrt(val)
    f.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## STARTTIME Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `STARTTIME` function returns the model's starttime.

    Signature: `starttime(model)`
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model_9 = Model(starttime=5, stoptime=12, dt=1, name='starttime')
    starttime = model_9.converter('starttime')
    starttime.equation = sd.starttime(model_9)
    starttime.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## STEP Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The STEP function generates a change of specified height, which occurs at a specified time:
    it is 0 before `timestep` and `height` from `timestep` on, as XMILE's STEP is.

    Signature: `step(height, timestep)`

    `height`: any model element or a floating point number

    `timestep`: any model element or a floating point number
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model_11 = Model(starttime=1, stoptime=10, dt=1, name='step')
    step = model_11.converter('step')
    step.equation = sd.step(10.0, 5.0)
    step.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## STOPTIME Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `STOPTIME` function returns the model's stoptime.

    Signature: `stoptime(model)`
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model_10 = Model(starttime=5, stoptime=12, dt=1, name='stoptime')
    stoptime = model_10.converter('stoptime')
    stoptime.equation = sd.stoptime(model_10)
    stoptime.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## TIME Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `time` function returns the current simulation time.

    Signature: `time()`
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model_12 = Model(starttime=0, stoptime=10, dt=1, name='time')
    stock_1 = model_12.stock('stock')
    stock_1.initial_value = 0.0
    inflow = model_12.flow('inflow')
    inflow.equation = sd.time()
    stock_1.equation = inflow
    inflow.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## TREND Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The TREND function calculates the trend in the input, given the input, an averaging time and, optionally, the trend to start with. The TREND is defined to be the fractional change in input compared to the exponential average of input per averaging time. The TREND function thus estimates the growth rate of its input function.

    Signature: `trend(model, input_function, averaging_time, initial_trend=0.0)`

    `model`: The model you are writing equations for

    `input_function`: any model element

    `averaging_time`: any model element

    `initial_trend`: the trend at the start, a number, a model element or an expression. The exponential average then starts at `input / (1 + initial_trend * averaging_time)`, as in XMILE

    The TREND operator is a shorthand for the following stock and flow structure and equations:

    ![Stock and Flow Structure for the TREND Operator](trend_model.png)
    """)
    return


@app.cell
def _(Model, np, sd):
    #| echo: true
    model_13 = Model(starttime=1, stoptime=10, dt=0.01, name='trend')
    growth_rate_1 = model_13.constant('growth_rate')
    growth_rate_1.equation = np.log(2)
    input_function_2 = model_13.converter('input_function')
    input_function_2.equation = sd.exp(growth_rate_1 * sd.time())
    trend = model_13.converter('trend')
    trend.equation = sd.trend(model_13, input_function_2, 1.0, growth_rate_1)
    return growth_rate_1, input_function_2, trend


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As an example, we set up a small model that has an input function that doubles every timestep - i.e. the exponential growth rate is log 2 ≈ 0.69 and then apply the trend function to estimate the growth rate.

    Here is a plot of the growth rate, which is constant:
    """)
    return


@app.cell
def _(growth_rate_1):
    #| echo: true
    growth_rate_1.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This gives an input function which doubles in value on every timestep:
    """)
    return


@app.cell
def _(input_function_2):
    #| echo: true
    input_function_2.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As expected, the plot of the trend function converges to the input growth rate:
    """)
    return


@app.cell
def _(trend):
    #| echo: true
    trend.plot(format="axes")
    return


if __name__ == "__main__":
    app.run()
