# Front matter the .py format cannot carry; injected on export.
# description: Description and overview of how vector-valued and matrix-valued SD Models can be set up and worked with
# keywords: system dynamics, systemdynamics, sd dsl, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Creating multidimensional SD Models")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Multidimensional SD Models
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    These pages are the **reference** for arrays in the SD DSL: how to give an element
    a shape, which operators work on it, what each one returns, and what is deliberately
    not supported. Every section runs its own small example, so you can read them as a
    catalogue and copy from them.

    * [Defining Arrayed Components](./sd_dsl_arrays_defining.md) – vectors and matrices,
      with numerical or named indices, and how to plot them
    * [Operations on Arrayed Components](./sd_dsl_arrays_operations.md) – the arithmetic,
      math and comparison operators, `If`, `max` and `min`, and `smooth`, `trend` and
      `delay`, each applied element by element
    * [Array Functions](./sd_dsl_arrays_functions.md) – what turns an array into one value
      or multiplies arrays: sum, product, rank, mean, median, standard deviation, maximum
      and minimum, size and `dot`
    * [User-defined Functions and Arrayed Models](./sd_dsl_arrays_user_defined_functions.md) –
      a function of your own applied per index, or handed the whole array
    * [A Simple Arrayed Model](./sd_dsl_arrays_example.md) – an investment depot with two
      accounts, from setting up the model to the plot

    For arrays in a model that does something, the Model Library has two worked examples:
    a [workforce aging chain](../../model_library/multidimensional/workforce_aging_chain.html)
    over a vector of seniority levels, and a
    [regional product portfolio](../../model_library/multidimensional/regional_product_portfolio.html)
    built on a matrix of products across regions.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Things to watch out for

    These all work; they just do not always work the way a first reading suggests.

    * **Element-wise is the default, everywhere.** Every operator applies to an array
      index by index, and so does a
      [user-defined function](./sd_dsl_arrays_user_defined_functions.md),
      unless it is registered with `elementwise=False`.
    * **An aggregation is a scalar, and it needs an element of its own.**
      `headcount.arr_sum()` is one number, and assigning it to an element you gave a
      shape raises: an arrayed element holds no value beside its cells.
    * **`arr_size` counts the first dimension**, not the cells - see [Array
      Size](./sd_dsl_arrays_functions.md#array-size).
    * **The order of a dimension is the order you declared it in.** `arr_largest`,
      `arr_rank` and `arr_median` sort, and both engines sort the same list - but a named vector's
      "first" index is the first key you set up, not the alphabetically first label.
    * **A sub-element is an element of its own.** `headcount["north"]` has its own
      equation, its own name in the result frame (`headcount[north]`), and a scenario
      overrides it under that name.
    * **A flow never goes negative**, arrayed or not. A quantity that has to move both ways
      belongs in a [biflow](../sd_dsl_stocks_and_flows/sd_dsl_stocks_and_flows.md#biflows).

    ## What Is Not Supported

    None of these fails silently - each one raises with a message that says what happened.

    * **Two dimensions is the limit.** `setup_matrix` takes exactly two sizes, and there
      is no three-dimensional array.
    * **No dimension-position operator.** XMILE's `@`, which names a position within a
      dimension, has no counterpart.
    * **No broadcasting.** Both operands of an element-wise operation need the same shape
      and the same indices - see [Standard
      Operations](./sd_dsl_arrays_operations.md#standard-operations).
    * **A named matrix whose rows carry different column labels** cannot be multiplied
      with `dot`, sliced, transposed or aggregated with `over=0`: each of these works
      across the rows. Arithmetic on such a matrix works.
    * **A `dot` of a named array with an unnamed one** - see [Array
      Dot](./sd_dsl_arrays_functions.md#array-dot).
    """)
    return


if __name__ == "__main__":
    app.run()
