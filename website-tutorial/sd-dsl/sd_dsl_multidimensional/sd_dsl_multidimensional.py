# Front matter the .py format cannot carry; injected on export.
# description: Description and overview how vector-valued and matrix-valued SD Models can bet setup and worked with
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
      [user-defined function](../sd_user_defined_functions/sd_user_defined_functions.md):
      it is called once per index, and the result is an array of the same shape. A
      function that wants the whole array instead is registered with
      `elementwise=False` - and that one does not run on the Rust engine: a run that
      asks for it raises, and a run that does not stays in Python. The element-wise
      form runs on the engine like everything else here.
    * **An aggregation is a scalar, and it needs an element of its own.**
      `headcount.arr_sum()` is one number, and assigning it to an element you gave a
      shape raises: an arrayed element holds no value beside its cells.
    * **The order of a dimension is the order you declared it in.** `arr_rank` and
      `arr_median` sort, and both engines sort the same list - but a named vector's
      "first" index is the first key you set up, not the alphabetically first label.
    * **A sub-element is an element of its own.** `headcount["north"]` has its own
      equation, its own name in the result frame (`headcount[north]`), and a scenario
      overrides it under that name.

    ## What Is Not Supported

    Worth knowing before you build on arrays. None of these fails silently - each one
    raises with a message that says what happened.

    * **Two dimensions is the limit.** `setup_matrix` takes exactly two sizes, and there
      is no three-dimensional array.
    * **A named matrix in a `dot` needs the same column labels in every row.** Such a
      matrix is legal everywhere else - a `dot` is the one operation that sums over an
      axis and therefore needs a single set of column labels to sum over.
    * **A `dot` cannot mix a named array with an unnamed one.** There is nothing for the
      labels to line up against, so it raises.
    * **There is no aggregation over a single dimension.** `arr_sum` and `arr_prod` take
      a `dimensions` argument, but the only values it accepts are `"*"` (the default) and
      an integer equal to the array's depth - both of which aggregate every cell.
      Aggregating along the rows of a matrix would have to return a vector, which is not
      supported; where you need it, address the rows yourself. A row of a named matrix is
      a named vector in its own right, so `matrix['north'].arr_sum()` is the total of
      that row.
    * **`arr_size` counts the first dimension**, not the number of cells: 2 for a
      $2 \times 3$ matrix.
    * **There is no broadcasting.** Both operands of an element-wise operation must have
      the same shape and the same indices; a vector and a matrix is an error.
    * **No transpose, and no dimension-position operator.** The XMILE standard has both -
      a transpose, and `@` to name a position within a dimension - and the SD DSL has
      never implemented either, because nothing in the model library or the test corpus
      has needed one. Where you would reach for a transpose, address the cells the other
      way round when you set the matrix up; a row of a named matrix is a named vector, so
      `matrix['north']` is that row and there is no need to turn the matrix around to get
      at it.
    * **A flow never goes negative**, arrayed or not: every flow equation is wrapped in
      `max(0, ...)`. A quantity that has to move both ways belongs in a **biflow**, which
      takes the same `setup_vector` and `setup_named_vector` as any other element.
    """)
    return


if __name__ == "__main__":
    app.run()
