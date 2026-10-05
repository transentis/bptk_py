# Front matter the .py format cannot carry; injected on export.
# description: How to give an SD DSL element a shape - vectors, matrices, named indices - and how to plot it
# keywords: system dynamics, systemdynamics, sd dsl, arrays, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Defining Arrayed Components")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Defining Arrayed Components
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The examples on this page share one model, set up here:
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk

    model = Model(starttime=0.0, stoptime=15.0, dt=1.0, name="Arrays")
    return bptk, model, sd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    There are two options for arrayed components:

    - Vectors (one dimensional arrays)
    - Matrices (two dimensional arrays)

    Moreover, both types of arrays - Vectors and Matrices - can be setup:

    - using numerical indices
    - using string-valued indices (named arrays)

    Lets have a look at some examples:
    """)
    return

@app.cell
def _(model):
    ## Defining a Vector (with numerical indices)
    # Define an sd dsl element
    plain_vector = model.converter('plain_vector')
    # Create a vector of length 2 with different values
    plain_vector.setup_vector(2, [2.0, 3.0])
    # Create a vector of length 2 with identical values
    plain_vector.setup_vector(2, 3.0)
    return

@app.cell
def _(model):
    ## Defining a named Vector (with string-valued indices)
    # Define an sd dsl element
    labelled_vector = model.converter('labelled_vector')
    # Create a named vector of length 2 using string-valued indices
    labelled_vector.setup_named_vector({'value1': 4.0, 'value2': 5.0})
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As can be seen, we need two parameters for setting up a Vector using numerical indices.
    Moreover, there is one optional parameter.

    | Parameter | Type | Meaning |
    |-|-|-|
    | size | Integer | Defines the length of the Vector |
    | values | List of Float/Integer | Defines the values of the Vector elements |
    | set_stack_equation | Boolean | (optional) If the element is a stock, the initial value is set (False) or the equation is set (True). Default is False. |

    And we need one parameter (+ one optional parameter) for setting up a Vector using string indices:

    | Parameter | Type | Meaning |
    |-|-|-|
    | values | Dictionary | Defines the string-values indices and their values |
    | set_stack_equation | Boolean | (optional) If the element is a stock, the initial value is set (False) or the equation is set (True). Default is False. |

    `values` is either one value per index, or a **single** value that every index gets -
    `setup_vector(2, 3.0)` above is the short form of `setup_vector(2, [3.0, 3.0])`.
    `set_stack_equation` has a section of its own below.

    For matrices, we can proceed completely similar.
    """)
    return

@app.cell
def _(model):
    ## Defining a Matrix (with numerical indices)
    # Define an sd dsl element
    plain_matrix = model.converter('plain_matrix')
    # Create a matrix of size 2x2 with different values
    plain_matrix.setup_matrix([2, 2], [[2.0, 3.0], [4.0, 5.0]])
    # Create a matrix of size 2x2 whose four cells all hold 3.0
    plain_matrix.setup_matrix([2, 2], 3.0)
    return

@app.cell
def _(model):
    ## Defining a named Matrix (with string-valued indices)
    # Define an sd dsl element
    labelled_matrix = model.converter('labelled_matrix')
    # Create a named matrix of size 2x2 using string-valued indices
    labelled_matrix.setup_named_matrix({
        'value1': {'value11': 2.0, 'value12': 3.0},
        'value2': {'value21': 4.0, 'value22': 5.0},
    })
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As can be seen, we need two parameters (+ one optional parameter) for setting up a Matrix using numerical indices:

    | Parameter | Type | Meaning |
    |-|-|-|
    | size | List (tuple) of Integer | Defines the size of the Matrix |
    | values | List of Lists of Float/Integer | Defines the values of the Matrix elements |
    | set_stack_equation | Boolean | (optional) If the element is a stock, the initial value is set (False) or the equation is set (True). Default is False. |

    And we need one parameter (+ one optional parameter) for setting up a Matrix using string-valued indices:

    | Parameter | Type | Meaning |
    |-|-|-|
    | values | Dictionary | Defines the string-values indices and their values |
    | set_stack_equation | Boolean | (optional) If the element is a stock, the initial value is set (False) or the equation is set (True). Default is False. |

    A matrix takes a single value as well: `setup_matrix([2, 2], 3.0)` gives a
    2x2 matrix whose four cells all hold 3.0.
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## What `set_stack_equation` does
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    For every element except a stock, the values handed to `setup_vector` and its three
    siblings are simply the sub-elements' values, and `set_stack_equation` changes
    nothing.

    A **stock** is the one case where those values could mean two different things, and
    this is the flag that decides which:

    - `False`, the default: each value is the **initial value** of its sub-stock. The
      sub-stock starts there and then accumulates whatever flows you give it.
    - `True`: each value becomes the sub-stock's **equation**, that is its net change per
      unit of time. The sub-stock starts at 0.0 and adds that value at every step.

    So the same call means "start at 10 and 20" or "grow by 10 and 20 per period":
    """)
    return

@app.cell
def _(model):
    ## The values as initial values - the default
    balance = model.stock('balance')
    balance.setup_vector(2, [10.0, 20.0])
    deposits = model.flow('deposits')
    deposits.setup_vector(2, [1.0, 2.0])
    balance[0].equation = deposits[0]
    balance[1].equation = deposits[1]
    return (balance,)

@app.cell
def _(model):
    ## The same values as the stock's own equation
    growth = model.stock('growth')
    growth.setup_vector(2, [10.0, 20.0], set_stack_equation=True)
    return (growth,)

@app.cell
def _(balance, growth, mo):
    with mo.capture_stdout() as captured_stack:
        print("set_stack_equation=False (initial values, plus a flow of 1.0 and 2.0):")
        print("  index 0: " + str([balance[0](_t) for _t in range(4)]))
        print("  index 1: " + str([balance[1](_t) for _t in range(4)]))
        print("set_stack_equation=True (the values are the stock's equation):")
        print("  index 0: " + str([growth[0](_t) for _t in range(4)]))
        print("  index 1: " + str([growth[1](_t) for _t in range(4)]))

    mo.plain_text(captured_stack.getvalue())
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Plotting arrayed Components
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Similar to one-dimensional SD DSL elements, we can also plot these elements.
    Lets have a look:
    """)
    return

@app.cell
def _(model):
    plotted_vector = model.converter('plotted_vector')
    plotted_vector.setup_named_vector({'value1': 6.0, 'value2': 7.0})
    plotted_vector.plot(format="axes")
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As can be seen, both elements of the Vector are plotted.

    If you want to plot the values of the Matrix, you need to specify the first index.
    """)
    return

@app.cell
def _(model):
    plotted_matrix = model.converter('plotted_matrix')
    plotted_matrix.setup_named_matrix({
        'value1': {'value11': 6.0, 'value12': 7.0},
        'value2': {'value21': 8.0, 'value22': 9.0},
    })
    plotted_matrix['value1'].plot(format="axes")
    return

if __name__ == "__main__":
    app.run()
