# Front matter the .py format cannot carry; injected on export.
# description: How a user-defined function of the SD DSL handles an arrayed argument - per index by default, or the whole array with elementwise=False
# keywords: system dynamics, systemdynamics, sd dsl, arrays, user-defined functions, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="User-defined Functions and Arrayed Models")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # User-defined Functions and Arrayed Models
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model

    return (Model,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    A [user-defined function](../sd_user_defined_functions/sd_user_defined_functions.md) can
    take an arrayed element as its argument, and a function says once - when it is
    registered - what that should mean.

    **By default a function is applied per index**, which is the rule every operator in
    the DSL follows: the result is an array of the same shape, and a named array keeps
    its labels.
    """)
    return


@app.cell
def _(Model):
    array_model = Model(starttime=1.0, stoptime=5.0, dt=1.0, name="arrays_and_functions")

    revenue = array_model.constant("revenue")
    revenue.setup_named_vector({"north": 100.0, "south": 250.0})

    commission = array_model.function("commission", lambda model, t, amount: amount * 0.1)

    per_region = array_model.converter("per_region")
    per_region.equation = commission(revenue)

    {name: per_region[name](1) for name in ("north", "south")}
    return array_model, commission, revenue


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **A function declared with `elementwise=False` receives the whole array instead** and
    answers once. An unnamed array arrives as a list, a named one as a dict keyed by its
    labels, and a matrix arrives nested. The result is a single value, so anything built
    on top of it is scalar too.
    """)
    return


@app.cell
def _(array_model, revenue):
    largest_region = array_model.function(
        "largest_region",
        lambda model, t, amounts: max(amounts.values()),
        elementwise=False,
    )

    peak = array_model.converter("peak")
    peak.equation = largest_region(revenue)

    peak(1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Which of the two you want is a property of the function, not of the call, so it is
    stated where the function is registered. The default is the element-wise one, because
    that is what every other operator does with an array.

    The aggregations the DSL already carries - `arr_sum`, `arr_mean`, `arr_max` and the
    rest - need no function at all, and they run on the Rust engine. Reach for
    `elementwise=False` when the reduction is one the DSL does not have.
    """)
    return




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    A function registered with `elementwise=False` cannot run on the [Rust
    engine](../../concepts/execution_backends/execution_backends.md): a callback from the
    engine answers with one number per node, and such a function is handed a whole array.
    A model that uses one runs on the Python engine; asked to run on Rust, it is refused with
    a `RustBackendError` naming the function. [Limitations](../../usage/limitations.md#the-rust-execution-engine)
    lists what else stays on the Python engine.
    """)
    return


if __name__ == "__main__":
    app.run()
