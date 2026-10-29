# Front matter the .py format cannot carry; injected on export.
# description: Creating user-defined functions in the SD DSL that is part of the BPTK-Py business simulation framework.
# keywords: system dynamics, systemdynamics, sd dsl, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Creating User-defined Functions in SD Models")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Creating User-defined Functions in SD Models
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    One of the benefits of creating System Dynamics models in Python is that we can use the full power of Python to create our own functions, which we can then use in our models.

    This how-to illustrates how to do this.

    First of all, let's set up our model:
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    model = Model(starttime=1,stoptime=10,dt=0.25,name='TestModel')
    return Model, model, sd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now let's define a function we would like to use in our model. A user defined function can have as many arguments as you like, but it must accept at least a model and time parameter (you don't need to use the parameters if you don't want to).

    How you define your function is up to you - you can use any of the methods available in Python, such as class methods, using def, or lambda functions.

    The example below uses a lambda function which simply multiplies the current time ``t`` with 5.
    """)
    return


@app.cell
def _(model):
    my_model_function = model.function("my_model_function", lambda model, t: 5*t)
    return (my_model_function,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As you can see, much like with stocks and converters, we associate our function with the model by calling the model's ``function`` method.

    Next we set up a converter whose equation calls the function, and test it at ``t = 5``:
    """)
    return


@app.cell
def _(model, my_model_function):
    converter = model.converter("converter")
    converter.equation = my_model_function()
    converter(5)
    return (converter,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's plot the function over time:
    """)
    return


@app.cell
def _(converter):
    converter.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can also create a stock that has the converter as an inflow:
    """)
    return


@app.cell
def _(converter, model):
    stock = model.stock("stock")
    stock.equation = converter
    stock.plot(format="axes")
    return (stock,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can do all the usual arithmetic in an equation. Here the same converter is divided
    by time before it flows in - a second stock rather than a second equation on the first
    one, because an element whose equation is set in two cells has no defined value outside
    the cell that just set it:
    """)
    return


@app.cell
def _(converter, model, sd):
    scaled_stock = model.stock("scaled_stock")
    scaled_stock.equation = converter / sd.time()
    scaled_stock.plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The function we created above was just dependent on time and not on other model variables. Let's create a function that takes more arguments, e.g. one that multiplies a model variable with time.

    You can add as many arguments as you like, but they must come after the ``model`` and ``t`` arguments.
    """)
    return


@app.cell
def _(model):
    another_model_function = model.function("another_model_function", lambda model, t, input_function, multiplier : t*input_function*multiplier)
    return (another_model_function,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The function needs two inputs, so we define a converter for each of them and then a
    third converter that applies ``another_model_function`` to both:
    """)
    return


@app.cell
def _(another_model_function, model):
    input_function = model.converter("input_function")
    input_function.equation = 5.0
    multiplier = model.converter("multiplier")
    multiplier.equation = 1.0

    another_converter = model.converter("another_converter")
    another_converter.equation = another_model_function(input_function, multiplier)
    another_converter.plot(format="axes")
    return (another_converter,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Of course functions defined in this way can also be used within scenarios. The quickest
    way to set up a scenario manager for a given model is `register_model`, which creates a
    scenario manager named after the model with the prefix "sm" - the name is normalized to
    start with a capital letter, so `TestModel` becomes `smTestmodel` - together with a
    "base" scenario that runs the model as-is.

    Three more scenarios are added below, each with a different `multiplier`, and
    `list_scenarios` shows what the manager now holds:
    """)
    return


@app.cell
def _(another_converter, mo, model):
    from BPTK_Py.bptk import bptk

    bptk = bptk()

    bptk.reset_all_scenarios()
    bptk.register_model(model)

    bptk.register_scenarios(
        scenarios={
            "multiplier5": {"constants": {"multiplier": 5.0}},
            "multiplier10": {"constants": {"multiplier": 10.0}},
            "multiplier15": {"constants": {"multiplier": 15.0}},
        },
        scenario_manager="smTestmodel",
    )

    scenarios_to_plot = ["base", "multiplier5", "multiplier10", "multiplier15"]
    equations_to_plot = [another_converter.name]

    with mo.capture_stdout() as registered:
        bptk.list_scenarios(scenario_managers=["smTestmodel"])

    mo.plain_text(registered.getvalue())
    return bptk, equations_to_plot, scenarios_to_plot


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And plotting the four scenarios against each other shows what the multiplier does:
    """)
    return


@app.cell
def _(bptk, equations_to_plot, scenarios_to_plot):
    bptk.plot_scenarios(
        scenario_managers=["smTestmodel"],
        scenarios=scenarios_to_plot,
        equations=equations_to_plot,
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Where a user-defined function may stand

    A function computes the value of an element, so it goes where an equation goes: a
    converter, a flow, a biflow, and the equation of a stock. It can also be a stock's
    *initial value*, since an initial value is an expression like any other:

    ```python
    starting_point = model.function("starting_point", lambda model, t: 42.0)

    stock = model.stock("stock")
    stock.initial_value = starting_point()
    ```

    An initial value is evaluated before the run rather than during it, so a function
    standing there is called once, with `t` at the start time.

    ## Which functions run on the Rust engine

    A model with user-defined functions runs on the [Rust
    engine](../../concepts/execution_backends/execution_backends.md). The engine evaluates
    the model and calls back into Python at those nodes, once per node and timestep, so
    the function you wrote is the function that runs.

    The run says so at `[WARN]`, and [Execution
    Backends](../../concepts/execution_backends/execution_backends.md#part-of-a-model-can-still-be-python)
    explains what that means and what it costs.

    A function [registered with
    `elementwise=False`](../sd_dsl_multidimensional/sd_dsl_arrays_user_defined_functions.md),
    and one in a hybrid model that reads what the agents produced, cannot run on the engine; [Limitations](../../usage/limitations.md#the-rust-execution-engine)
    says why.

    ## On the server

    `/execute` refuses a model that carries user-defined functions, with HTTP 400 naming
    them. The model arrived over HTTP, and running the Python that goes with it is a
    different decision from running the model. Serve such a model from a process that
    holds the functions - a `bptk` instance with the scenario manager registered - rather
    than by posting the model itself.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Functions and arrays

    How a function handles an arrayed argument - per index, or the whole array with
    `elementwise=False` - is explained under [User-defined Functions and Arrayed
    Models](../sd_dsl_multidimensional/sd_dsl_arrays_user_defined_functions.md).
    """)
    return


if __name__ == "__main__":
    app.run()
