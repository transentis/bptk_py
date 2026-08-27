# Front matter the .py format cannot carry; injected on export.
# description: Overview of the SD DSL functions that are part of the BPTK-Py business simulation framework.
# keywords: system dynamics, systemdynamics, sd dsl, bptk, bptk-py, python, business simulation
# external-env: true
# /// script
# dependencies = [
#     "bptk-py",
# ]
# ///

import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="SD DSL Functions")


@app.cell
def _():
    # Added by `marimo convert`. Keep it: `marimo export html` turns markdown
    # blocks into mo.md(...) cells, which need this import.
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # SD DSL Functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This document illustrates how to use the operators for the SD DSL. To use the operators, you need to import the `sd_functions`, in addition to importing the `Model` class.
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
    # '%matplotlib inline' command supported automatically in marimo
    import matplotlib.pyplot as plt
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['savefig.facecolor'] = 'white'
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## IF / THEN / ELSE / AND /NOT / OR

    It is possible to write up if clauses. We even support NOT and AND / OR operators.

    Please note that these function names begin with a capital letter. This is because the actual words ``if, and, or`` etc. are protected in Python and cannot / should not be overwritten.

    An if clause requires 3 arguments: ``If ( <condition> , <then>, <else>)``

    ``condition``: Must be a boolean expression, e.g. ``sd.time() > 1`` is true iff the simulation time is larger than 1
    ``then`` : Any expression that returns a float value if the condition is true
    ``else`` : Any expression that returns a float value if the condition is false

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
    ``And(<condition1>, <condition2>)`` : Logical and between 2 conditions
    ``Or(<condition1>, <condition2>)`` : Logical or between 2 conditions
    ``Not(<condition>)`` : Logical not: True if condition is False

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
    ## ABS Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `ABS`function returns the absolute value of its input.

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
    # Registering a model whose scenario manager already exists leaves the *old*
    # model in place - `register_scenario_manager` warns and keeps it. So if you edit
    # this cell and press play, drop the registry first or you will plot the model you
    # started with rather than the one you just changed.
    bptk.reset_all_scenarios()
    bptk.register_model(model_1)
    bptk.plot_scenarios(scenario_managers=['smAbs'], scenarios=['base'], equations=['input_converter', 'abs_converter'], format="axes")
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
    The DELAY function returns a delayed value of input, using a fixed lag time of delay duration, and an optional initial value initial for the delay. If you don't specify an initial value initial, DELAY assumes the value to be the initial value of input. If you specify delay duration as a variable, the DELAY function uses the initial value for its fixed lag time

    Signature: `delay(model, input_function, delay_duration, initial_value)`

    `input_function` must be a model element
    `delay_duration` and `initial_value` must be floats or model elements.
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
    # Registering a model whose scenario manager already exists leaves the *old*
    # model in place - `register_scenario_manager` warns and keeps it. So if you edit
    # this cell and press play, drop the registry first or you will plot the model you
    # started with rather than the one you just changed.
    bptk.reset_all_scenarios()
    bptk.register_model(model_2)
    bptk.plot_scenarios(scenario_managers=['smDelay'], scenarios=['base'], equations=['input_function', 'delayed_input_1', 'delayed_input_2', 'delayed_input_3'], format="axes")
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
    The `DT` function returns the models dt..

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
    ## MAX Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `max` function always chooses the larger of its two input values.

    Signature: `max(element, element)`

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
    # Registering a model whose scenario manager already exists leaves the *old*
    # model in place - `register_scenario_manager` warns and keeps it. So if you edit
    # this cell and press play, drop the registry first or you will plot the model you
    # started with rather than the one you just changed.
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
    The `min` function always chooses the smaller of its two input values.

    Signature: `min(element, element)`

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
    # Registering a model whose scenario manager already exists leaves the *old*
    # model in place - `register_scenario_manager` warns and keeps it. So if you edit
    # this cell and press play, drop the registry first or you will plot the model you
    # started with rather than the one you just changed.
    bptk.reset_all_scenarios()
    bptk.register_model(model_6)
    bptk.plot_scenarios(scenario_managers=['smMin'], scenarios=['base'], equations=['a', 'b', 'c'], format="axes")
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

    Signature: `pulse(model, volume, first_pulse=0, interval=0)`

    Setting `interval` to 0 yields a single pulse that doesn't repeat

    `volume` can be either a variable or a constant, `first_pulse` and `interval` must be constants.
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
    # Registering a model whose scenario manager already exists leaves the *old*
    # model in place - `register_scenario_manager` warns and keeps it. So if you edit
    # this cell and press play, drop the registry first or you will plot the model you
    # started with rather than the one you just changed.
    bptk.reset_all_scenarios()
    bptk.register_model(model_7)
    bptk.plot_scenarios(scenario_managers=['smPulse'], scenarios=['base'], equations=['stock', 'flow'], format="axes")
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
    The SMOOTH function calculates the exponential average of the input, given the input function, an initial value and an averaging time.

    Signature: `smooth(model, input_function, averaging_time, initial_value)`

    `model`: The model you are writing equations for

    `input_function`: any model element

    `averaging_time`: any model element

    `initial_value`: a floating point value or constant

    The SMOOTH operator is a shorthand for the following stock and flow structure and equations:

    ![Stock and Flow Structure for the TREND Operator](smooth_model.png)
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
    # Registering a model whose scenario manager already exists leaves the *old*
    # model in place - `register_scenario_manager` warns and keeps it. So if you edit
    # this cell and press play, drop the registry first or you will plot the model you
    # started with rather than the one you just changed.
    bptk.reset_all_scenarios()
    bptk.register_model(model_8)
    bptk.plot_scenarios(scenario_managers=['smSmooth'], scenarios=['base'], equations=['input_function', 'smooth'], format="axes")
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
    The `STARTTIME` function returns the models starttime.

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
    ## STOPTIME Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `STOPTIME` function returns the models starttime.

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
    ## STEP Function
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The STEP function generates a change of specified height, which occurs at a specified time.

    Signature: `step(height, timestep)`

    `input_function`: any model element or a floating point number

    `averaging_time`: any model element or a floating point numnber

    `initial_value`: a floating point value or a constant
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
    The TREND function calculates the trend in the input, given the input, an initial value and an averaging time. The TREND is defined to be the fractional change in input compared to the exponential average of input per averaging time. The TREND function thus estimates the growth rate of is input function.

    Signature: `trend(model, input_function, averaging_time, initial_value)`

    `model`: The model you are writing equations for

    `input_function`: any model element

    `averaging_time`: any model element

    `initial_value`: a floating point value or constant

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
    trend.equation = sd.trend(model_13, input_function_2, 1.0, 2 / (1 + np.log(2)))
    return growth_rate_1, input_function_2, trend


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As an example, we set up a small model that has an input function that doubles every timestep - i.e the exponential growth rate is log 2 ≈ 0.69 and then apply the trend function to estimate the growth rate.

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
    As expexted, the plot of the trend function converges to the input growth rate:
    """)
    return


@app.cell
def _(trend):
    #| echo: true
    trend.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ROUND Function

    This function rounds any input to a specified number of digits.

    Signature:
    ``round(expression, digits)``

    ``expression`` can be any float input by any expression.
    ``digits`` must be an int value

    A minimal example that rounds random numbers between 0 and 2 to 0 digits (int number):
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    model_14 = Model(starttime=0.0, stoptime=10.0, dt=0.25, name='round')
    flow_1 = model_14.flow('round')
    flow_1.equation = sd.round(sd.random(0, 2), 0)
    flow_1.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## CEIL / FLOOR Functions

    ``ceil`` rounds its input up to the next whole number, ``floor`` rounds it down. Unlike
    ``round`` they take no digit count - they always go to the nearest integer, and they always
    go in the same direction.

    Signature:
    ``ceil(expression)`` and ``floor(expression)``

    ``expression`` can be any element that returns a float value.

    The XMILE builtin ``INT`` is ``floor``, not a rounding function - it also truncates towards
    the lower whole number.

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
    ## SQRT
    Computes the Square root of an input expression.

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
    ## LOOKUP Function

    ``lookup`` evaluates a *graphical function*: a relationship you give as a list of points
    rather than as a formula. Between two points the value is interpolated linearly; outside
    the given range it stays at the first or last point.

    Signature:
    ``lookup(element, points)``

    ``element`` is the input to look up, ``points`` a list of ``(x, y)`` tuples in ascending
    order of ``x``.

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
    ## NAN / INF / PI

    ``sd.nan()`` returns a NAN value, ``sd.Inf()`` gives you the infinity value, ```sd.pi()``` returns the number pi.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## SIN / TAN / COS and ARCCOS / ARCSIN / ARCTAN

    The SD DSl supports all trigonometric that you are also used to from other SD simulation / modelling tools

    Use ``sd.sin(x) / sd.cos(x) / sd.tan(x)`` for sinus, cosinus or tangent of x (radians) and ``sd.arcsin(x) / sd.arctan(x) / sd.arccos(x)`` for the respective arctan / arccos and arcsine operators.

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
    ## SINWAVE and COSWAVE function

    SINWAVE returns a time-dependent sine wave, with the specified amplitude and period. To generate the sine wave, the SINWAVE builtin uses the absolute value of the amplitude you specify. To produce meaningful wave results, choose a DT that's significantly smaller than the period of the wave. A DT equal to a quarter of the period gives triangle waves. A smaller DT gives results which better approximate a continuous curve.

    COSWAVE generates a time-dependent __cosine__ wave. It uses the same arguments

    Signature:
    ``sinwave(amplitude,period)``

    ``amplitude`` : Amplitude of the sine wave
    ``period`` : Period of the sine wave

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
    ## COMBINATIONS
    The COMBINATIONS operator calculates the number of r-element subsets (or r-combinations) of an n-element set without repetition.

    Arguments `n` and `r` must follow n >= r >= 0 and be integers.

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
    mean = sd.time()
    f_5.equation = sd.exprnd(mean)
    f_5.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## FACTORIAL Function
    The FACTORIAL function calculates the factorial of the single argument `n` (traditionally noted as n!). `n` must be an integer value, decimal values are not allowed.

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
    ## GAMMA Function
    The GAMMA builtin generates a series of random numbers that conforms to a gamma distribution with the specified ``shape`` and ``scale``. If unspecified, ``scale`` uses the value 1.0

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_8 = Model(starttime=0, stoptime=10, dt=0.1)
    f_7 = m_8.biflow(name='gamma')
    shape = 10
    scale = sd.time()
    f_7.equation = sd.gamma(shape, scale)
    f_7.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## GAMMALN Function

    The GAMMALN operator returns the natural log of the GAMMA function, given input n. The GAMMA function is a continuous version of the FACTORIAL builtin, with GAMMA(n) the same as FACTORIAL(n-1).

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
    ## INVNORM Function

    The INVNORM operator calculates the inverse of the NORMALCDF function (see below).

    Parameter is the ``probability p`` (any value between 0 and 1).

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_11 = Model(starttime=-0.5, stoptime=1, dt=0.1)
    f_10 = m_11.biflow(name='invnorm')
    p_2 = sd.time()
    f_10.equation = sd.invnorm(p_2)
    f_10.plot(format="axes")
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
    The LOGNORMAL operator generates a series of random numbers that conform to a Log-Normal distribution (that is, the log of the independent variable follows a normal distribution) with a specified mean and stddev (standard deviation). LOGNORMAL samples a new random number in each iteration of a simulation.

    Arguments are ``mean`` and ``standard deviation``

    Example:
    """)
    return


@app.cell
def _(Model, sd):
    #| echo: true
    m_13 = Model(starttime=0, stoptime=10, dt=0.1)
    f_12 = m_13.biflow(name='lognormal')
    mean_2 = 0
    stdev = 1
    f_12.equation = sd.lognormal(mean_2, stdev)
    f_12.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## MONTECARLO Function
    The MONTECARLO operator randomly generates a series of zeros and ones from a Bernoulli distribution based on the probability you've provided. The probability is the percentage probability of an event happening per unit of simulation time. The probability value can be either a variable or a constant, but should evaluate to a number between 0 and 100.

    MONTECARLO is equivalent to the following logic:

    IF (RANDOM(0,100,<seed>) < probability*DT THEN 1 ELSE 0

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
    ## PARETO Function
    The PARETO operator generates a series of random numbers that conforms to a distribution whose log is exponentially distributed with a specified shape and scale

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
    ## PERMUTATIONS
    The PERMUTATIONS operator calculates the number of permutations of an n-element set with r-element subsets.

    Arguments are ``n`` and ``r``. Note that both numbers should be integer values and must follow n >= r >= 0.

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

    RANDOM and UNIFORM both draw a random number between a minimum and maximum value that conforms to a uniform distribution. For compatibility to modelling practices, we included both into the SD DSL (just as the Stella Architect builtins).

    Arguments are the ``min_value`` and ``max_value`` between which the random number should lie. If not given, the random number is between 0 and 1.

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
