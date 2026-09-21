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
    This document is the **reference** for arrays in the SD DSL: how to give an element
    a shape, which operators work on it, what each one returns, and what is deliberately
    not supported. Every section runs its own small example, so you can read it as a
    catalogue and copy from it.

    For arrays in a model that does something, the Model Library has two worked examples:
    a [workforce aging chain](../../model_library/multidimensional/workforce_aging_chain.html)
    over a vector of seniority levels, and a
    [regional product portfolio](../../model_library/multidimensional/regional_product_portfolio.html)
    built on a matrix of products across regions.

    We start with some boilerplate to get a BPTK project up and running:
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk

    arrays_bptk = bptk()
    model = Model(starttime=0.0, stoptime=15.0, dt=1.0, name="Arrays")
    return model, arrays_bptk, sd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This is already enough to define arrayed components.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## How to define arrayed components
    """)
    return


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
    # Create a named vector of lenght 2 using string-valued indices
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
    ### What `set_stack_equation` does
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
    ## Math-Operations for arrayed Components
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Arrays are not a special case in the SD DSL: **every operator and function that
    takes an operand works on an arrayed element**, element by element. That covers the
    four arithmetic operations, powers and modulo, the math functions, comparisons and
    conditionals, `max` and `min`, the table and time functions, and the stateful
    `smooth`, `trend` and `delay`.

    On top of that there are the **array-specific** operations, which are the ones that
    do something an element-wise operator cannot: they aggregate a whole array into a
    single value, or multiply arrays in the linear-algebra sense.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Standard Operations
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The arithmetic operations $+$, $-$, $*$, $/$ as well as $**$ (power) and $\%$
    (modulo) accept any of these operand pairings:

    | Operand 1 | Operand 2 |
    |-|-|
    | Arrayed Element | Arrayed Element |
    | Arrayed Element | Scalar Element |
    | Scalar Element | Arrayed Element |
    | Arrayed Element | Float/Integer |
    | Float/Integer | Arrayed Element |

    **Scalar Element** and **Float/Integer** are not the same thing. A scalar element is
    a model element without a shape - a constant, converter, stock or flow - so it has an
    equation of its own and its value can change over the course of a simulation, and
    changing it changes every index that reads it. A Float or Integer is a plain Python
    number written into the equation, fixed for the whole run. Both are allowed on either
    side of the operator; `v * 2.0` and `v * some_constant` differ only in whether the
    factor can still move.

    ⚠️ If both operands are arrayed elements, they must have the same numerical or
    string-valued indices.

    That means it is **not** possible to have operand 1 = vector with numerical indices
    and operand 2 = vector with string-valued indices, even if they have the same size.

    It is also **not** possible to have operand 1 = vector and operand 2 = matrix or
    vice versa - there is no broadcasting. A mismatch raises an exception when the
    equation is assigned rather than guessing what was meant: mixing a vector and a
    matrix gives *Attempted invalid array addition*, two vectors of different length
    *Cannot perform binary operation on arrays with different sizes*, and a numerical
    against a named vector *Cannot perform binary operation on arrays with different
    indices*.

    Every one of these operations is performed element-wise: index by index, never
    across indices. Let's have a look at some examples:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Addition ($+$)
    """)
    return


@app.cell
def _(model):
    #Add not-named vectors
    add_left = model.converter('add_left')
    add_left.setup_vector(2, [1.1, 2.2])
    add_right = model.converter('add_right')
    add_right.setup_vector(2, [3.1, 4.2])
    add_result = model.converter('add_result')
    add_result.equation = add_left + add_right
    return add_result, add_right


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    1.1 \\
    2.2
    \end{pmatrix}
    +
    \begin{pmatrix}
    3.1 \\
    4.2
    \end{pmatrix}
    =
    \begin{pmatrix}
    4.2 \\
    6.4
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(add_result, mo):
    with mo.capture_stdout() as captured:
        print("[ " + str(add_result[0](0)) + " , " + str(add_result[1](0)) + " ]")

    mo.plain_text(captured.getvalue())
    return


@app.cell
def _(add_right, model):
    #Add a number to every index
    add_result_scalar = model.converter('add_result_scalar')
    add_result_scalar.equation = add_right + 1.0
    return (add_result_scalar,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    3.1 \\
    4.2
    \end{pmatrix}
    +1.0
    =
    \begin{pmatrix}
    4.1 \\
    5.2
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(add_result_scalar, mo):
    with mo.capture_stdout() as captured_1:
        print("[ " + str(add_result_scalar[0](0)) + " , " + str(add_result_scalar[1](0)) + " ]")

    mo.plain_text(captured_1.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Subtraction ($-$)
    """)
    return


@app.cell
def _(model):
    #Subtract not-named matrices
    minus_left = model.converter('minus_left')
    minus_left.setup_matrix([2, 2], [[1.1, 2.2], [3.3, 4.4]])
    minus_right = model.converter('minus_right')
    minus_right.setup_matrix([2, 2], [[5.5, 7.7], [3.3, 14.4]])
    minus_result = model.converter('minus_result')
    minus_result.equation = minus_left - minus_right
    return minus_right, minus_result


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    1.1 & 2.2 \\
    3.3 & 4.4
    \end{pmatrix}
    -
    \begin{pmatrix}
    5.5 & 7.7 \\
    3.3 & 14.4
    \end{pmatrix}
    =
    \begin{pmatrix}
    -4.4 & -5.5\\
    0.0 & -10.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(minus_result, mo):
    with mo.capture_stdout() as captured_2:
        print("[ " + "[" + str(minus_result[0][0](1)) + " , " + str(minus_result[0][1](1)) + "]")
        print("  " + "[" + str(minus_result[1][0](1)) + " , " + str(minus_result[1][1](1)) + "]" + " ]")

    mo.plain_text(captured_2.getvalue())
    return


@app.cell
def _(minus_right, model):
    #Subtract a number from every cell
    minus_result_scalar = model.converter('minus_result_scalar')
    minus_result_scalar.equation = minus_right - 1.0
    return (minus_result_scalar,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    5.5 & 7.7 \\
    3.3 & 14.4
    \end{pmatrix}
    -1.0
    =
    \begin{pmatrix}
    4.5 & 6.7\\
    2.3 & 13.4
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(minus_result_scalar, mo):
    with mo.capture_stdout() as captured_3:
        print("[ " + "[" + str(minus_result_scalar[0][0](1)) + " , " + str(minus_result_scalar[0][1](1)) + "]")
        print("  " + "[" + str(minus_result_scalar[1][0](1)) + " , " + str(minus_result_scalar[1][1](1)) + "]" + " ]")

    mo.plain_text(captured_3.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Multiplication ($*$)
    """)
    return


@app.cell
def _(model):
    #Multiply named vectors
    times_left = model.converter('times_left')
    times_left.setup_named_vector({'value1': 4.0, 'value2': 5.0})
    times_right = model.converter('times_right')
    times_right.setup_named_vector({'value1': 6.0, 'value2': 7.0})
    times_result = model.converter('times_result')
    times_result.equation = times_left * times_right
    return times_result, times_right


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    \text{'value1'}: & 4.0 \\
    \text{'value2'}: & 5.0
    \end{pmatrix}
    \odot
    \begin{pmatrix}
    \text{'value1'}: & 6.0 \\
    \text{'value2'}: & 7.0
    \end{pmatrix}
    =
    \begin{pmatrix}
    \text{'value1'}: & 24.0 \\
    \text{'value2'}: & 35.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(mo, times_result):
    with mo.capture_stdout() as captured_4:
        print("[ " + str(times_result["value1"](0)) + " , " + str(times_result["value2"](0)) + " ]")

    mo.plain_text(captured_4.getvalue())
    return


@app.cell
def _(times_right, model):
    #Multiply every index by a number
    times_result_scalar = model.converter('times_result_scalar')
    times_result_scalar.equation = times_right * 3.0
    return (times_result_scalar,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    \text{'value1'}: & 6.0 \\
    \text{'value2'}: & 7.0
    \end{pmatrix}
    \cdot
    3.0
    =
    \begin{pmatrix}
    \text{'value1'}: & 18.0 \\
    \text{'value2'}: & 21.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(mo, times_result_scalar):
    with mo.capture_stdout() as captured_5:
        print("[ " + str(times_result_scalar["value1"](0)) + " , " + str(times_result_scalar["value2"](0)) + " ]")

    mo.plain_text(captured_5.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The case "- arrayed element" is a special case since it is interpreted as "(-1) $\cdot$ element":
    """)
    return


@app.cell
def _(model, times_right):
    #Negate a named vector
    times_result_negated = model.converter('times_result_negated')
    times_result_negated.equation = -times_right
    return (times_result_negated,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    - \begin{pmatrix}
    \text{'value1'}: & 6.0 \\
    \text{'value2'}: & 7.0
    \end{pmatrix}
    =
    \begin{pmatrix}
    \text{'value1'}: & -6.0 \\
    \text{'value2'}: & -7.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(mo, times_result_negated):
    with mo.capture_stdout() as captured_6:
        print('[ ' + str(times_result_negated['value1'](0)) + ' , ' + str(times_result_negated['value2'](0)) + ' ]')

    mo.plain_text(captured_6.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Division ($/$)
    """)
    return


@app.cell
def _(model):
    #Divide not-named matrices
    divide_left = model.converter('divide_left')
    divide_left.setup_matrix([2, 2], [[2.0, 4.0], [8.0, 16.0]])
    divide_right = model.converter('divide_right')
    divide_right.setup_matrix([2, 2], [[2.0, 1.0], [0.5, 0.25]])
    divide_result = model.converter('divide_result')
    divide_result.equation = divide_left / divide_right
    return divide_result, divide_right


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    2.0 & 4.0\\
    8.0 & 16.0
    \end{pmatrix}
    \oslash
    \begin{pmatrix}
    2.0 & 1.0\\
    0.5 & 0.25
    \end{pmatrix}
    =
    \begin{pmatrix}
    1.0 & 4.0\\
    16.0 & 64.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(divide_result, mo):
    with mo.capture_stdout() as captured_7:
        print("[ " + "[" + str(divide_result[0][0](1)) + " , " + str(divide_result[0][1](1)) + "]")
        print("  " + "[" + str(divide_result[1][0](1)) + " , " + str(divide_result[1][1](1)) + "]" + " ]")

    mo.plain_text(captured_7.getvalue())
    return


@app.cell
def _(divide_right, model):
    #Divide every cell by a number
    divide_result_scalar = model.converter('divide_result_scalar')
    divide_result_scalar.equation = divide_right / 5.0
    return (divide_result_scalar,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    2.0 & 1.0\\
    0.5 & 0.25
    \end{pmatrix}
    /
    \text{ } 5.0
    =
    \begin{pmatrix}
    0.4 & 0.2\\
    0.1 & 0.05
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(divide_result_scalar, mo):
    with mo.capture_stdout() as captured_8:
        print("[ " + "[" + str(divide_result_scalar[0][0](1)) + " , " + str(divide_result_scalar[0][1](1)) + "]")
        print("  " + "[" + str(divide_result_scalar[1][0](1)) + " , " + str(divide_result_scalar[1][1](1)) + "]" + " ]")

    mo.plain_text(captured_8.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Power ($**$) and Modulo ($\%$)

    This section and the ones that follow all use the same little named vector, so the
    results are easy to compare.
    """)
    return


@app.cell
def _(model):
    demo_vector = model.converter('demo_vector')
    demo_vector.setup_named_vector({'small': 4.0, 'large': 9.0})
    return (demo_vector,)


@app.cell
def _(demo_vector, model):
    squared = model.converter('squared')
    squared.equation = demo_vector ** 2.0

    remainder = model.converter('remainder')
    remainder.equation = demo_vector % 5.0
    return remainder, squared


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    \text{'small'}: & 4.0 \\
    \text{'large'}: & 9.0
    \end{pmatrix}
    ^{2}
    =
    \begin{pmatrix}
    \text{'small'}: & 16.0 \\
    \text{'large'}: & 81.0
    \end{pmatrix}
    \end{equation*}

    \begin{equation*}
    \begin{pmatrix}
    \text{'small'}: & 4.0 \\
    \text{'large'}: & 9.0
    \end{pmatrix}
    \bmod 5
    =
    \begin{pmatrix}
    \text{'small'}: & 4.0 \\
    \text{'large'}: & 4.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(mo, remainder, squared):
    with mo.capture_stdout() as captured_power:
        print("v ** 2: [ " + str(squared['small'](0)) + " , " + str(squared['large'](0)) + " ]")
        print("v % 5:   [ " + str(remainder['small'](0)) + " , " + str(remainder['large'](0)) + " ]")

    mo.plain_text(captured_power.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Math Functions

    Every function in `sd_functions` that takes a value works on an array and returns an
    array of the same shape: `sqrt`, `exp`, `ln`, `log10`, `sin`, `cos`, `tan`, `arcsin`,
    `arccos`, `arctan`, `floor`, `ceil`, `round`, `abs`, `sinwave`, `coswave`.
    """)
    return


@app.cell
def _(demo_vector, model, sd):
    roots = model.converter('roots')
    roots.equation = sd.sqrt(demo_vector)

    scaled_logarithm = model.converter('scaled_logarithm')
    scaled_logarithm.equation = sd.ln(demo_vector) * 2.0
    return roots, scaled_logarithm


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \sqrt{
    \begin{pmatrix}
    \text{'small'}: & 4.0 \\
    \text{'large'}: & 9.0
    \end{pmatrix}
    }
    =
    \begin{pmatrix}
    \text{'small'}: & 2.0 \\
    \text{'large'}: & 3.0
    \end{pmatrix}
    \end{equation*}

    \begin{equation*}
    2 \cdot \ln
    \begin{pmatrix}
    \text{'small'}: & 4.0 \\
    \text{'large'}: & 9.0
    \end{pmatrix}
    =
    \begin{pmatrix}
    \text{'small'}: & 2.7726 \\
    \text{'large'}: & 4.3944
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(mo, roots, scaled_logarithm):
    with mo.capture_stdout() as captured_functions:
        print("sqrt(v):   [ " + str(roots['small'](0)) + " , " + str(roots['large'](0)) + " ]")
        print("2 * ln(v): [ " + str(round(scaled_logarithm['small'](0), 4)) + " , "
              + str(round(scaled_logarithm['large'](0), 4)) + " ]")

    mo.plain_text(captured_functions.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Comparisons, `If`, `And`, `Or`, `Not`

    A comparison over an array gives one boolean **per index**, and `If` then chooses per
    index as well. The condition, the `then` branch and the `else` branch may each be
    arrayed or scalar in any combination, as long as the arrayed ones agree on shape.
    """)
    return


@app.cell
def _(demo_vector, model, sd):
    threshold = model.constant('threshold')
    threshold.equation = 6.0

    large_enough = model.converter('large_enough')
    large_enough.equation = sd.If(demo_vector > threshold, demo_vector, 0.0)

    within_range = model.converter('within_range')
    within_range.equation = sd.And(demo_vector > 3.0, demo_vector < 6.0)
    return large_enough, threshold, within_range


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \mathrm{If}\left(
    \begin{pmatrix}
    \text{'small'}: & 4.0 \\
    \text{'large'}: & 9.0
    \end{pmatrix}
    > 6,
    \begin{pmatrix}
    \text{'small'}: & 4.0 \\
    \text{'large'}: & 9.0
    \end{pmatrix}
    , 0
    \right)
    =
    \begin{pmatrix}
    \text{'small'}: & 0.0 \\
    \text{'large'}: & 9.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(large_enough, mo, within_range):
    with mo.capture_stdout() as captured_conditional:
        print("If(v > 6, v, 0):     [ " + str(large_enough['small'](0)) + " , "
              + str(large_enough['large'](0)) + " ]")
        print("And(v > 3, v < 6):   [ " + str(within_range['small'](0)) + " , "
              + str(within_range['large'](0)) + " ]")

    mo.plain_text(captured_conditional.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### `max` and `min`

    `sd.max` and `sd.min` compare **two** operands, element by element. Not to be
    confused with `arr_max` and `arr_min` further down, which take the largest or the
    smallest value *within one array*.
    """)
    return


@app.cell
def _(demo_vector, model, sd):
    floored = model.converter('floored')
    floored.equation = sd.max(demo_vector, 6.0)
    return (floored,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \max\left(
    \begin{pmatrix}
    \text{'small'}: & 4.0 \\
    \text{'large'}: & 9.0
    \end{pmatrix}
    , 6
    \right)
    =
    \begin{pmatrix}
    \text{'small'}: & 6.0 \\
    \text{'large'}: & 9.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(floored, mo):
    with mo.capture_stdout() as captured_minmax:
        print("max(v, 6): [ " + str(floored['small'](0)) + " , " + str(floored['large'](0)) + " ]")

    mo.plain_text(captured_minmax.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### `smooth`, `trend` and `delay`

    The stateful functions work over arrays as well, and **each index carries its own
    history**: smoothing a vector is not one smoothed value copied across the indices,
    it is one smoothing chain per index. Below, both indices start at the initial value
    1.0 and each converges towards its own input - the recurrence
    $s_{t+1} = s_t + \frac{dt}{\tau}(x - s_t)$ runs once per index:
    """)
    return


@app.cell
def _(demo_vector, model, sd):
    smoothed = model.converter('smoothed')
    smoothed.equation = sd.smooth(model, demo_vector, 3.0, 1.0)
    return (smoothed,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \mathrm{smooth}\left(
    \begin{pmatrix}
    \text{'small'}: & 4.0 \\
    \text{'large'}: & 9.0
    \end{pmatrix}
    , \tau = 3, s_0 = 1
    \right)
    \Bigr|_{t=4}
    =
    \begin{pmatrix}
    \text{'small'}: & 3.4074 \\
    \text{'large'}: & 7.4198
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(mo, smoothed):
    with mo.capture_stdout() as captured_stateful:
        for _t in (0, 1, 4, 10):
            print("t=" + str(_t).rjust(2) + ": [ "
                  + str(round(smoothed['small'](_t), 4)) + " , "
                  + str(round(smoothed['large'](_t), 4)) + " ]")

    mo.plain_text(captured_stateful.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Array-specific Operations
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Array Sum
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Calculates the element-wise sum of an array.
    """)
    return


@app.cell
def _(model):
    #Calculate the element-wise sum of a named-vector
    sum_vector = model.converter('sum_vector')
    sum_vector.setup_named_vector({'value1': 1.0, 'value2': 2.0, 'value3': 3.0})
    sum_result = model.converter('sum_result')
    sum_result.equation = sum_vector.arr_sum()
    return (sum_result,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{sum}
    \begin{pmatrix}
    \text{'value1'}: & 1.0 \\
    \text{'value2'}: & 2.0 \\
    \text{'value3'}: & 3.0
    \end{pmatrix}
    =
    1.0 + 2.0 + 3.0 = 6.0
    \end{equation*}
    """)
    return


@app.cell
def _(mo, sum_result):
    with mo.capture_stdout() as captured_9:
        print(sum_result(1))

    mo.plain_text(captured_9.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Array Product
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Calculates the element-wise product of an array.
    """)
    return


@app.cell
def _(model):
    #Calculate the element-wise product of a not-named-matrix
    prod_matrix = model.converter('prod_matrix')
    prod_matrix.setup_matrix([2, 3], [[2.0, 3.0, 4.0], [5.0, 6.0, 7.0]])
    prod_result = model.converter('prod_result')
    prod_result.equation = prod_matrix.arr_prod()
    return (prod_result,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{prod}
    \begin{pmatrix}
    2.0 & 3.0 & 4.0 \\
    5.0 & 6.0 & 7.0
    \end{pmatrix}
    =
    2.0 \cdot 3.0 \cdot 4.0 \cdot 5.0 \cdot 6.0 \cdot 7.0 = 5040.0
    \end{equation*}
    """)
    return


@app.cell
def _(mo, prod_result):
    with mo.capture_stdout() as captured_10:
        print(prod_result(1))

    mo.plain_text(captured_10.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Array Rank
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Calculates the $n$-th highest element of an array. $n$ is given by a parameter.

    For $n=-1$ the lowest element of the array will be returned.
    """)
    return


@app.cell
def _(model):
    #Calculate the highest elements of a not-named vector
    rank_vector = model.converter('rank_vector')
    rank_vector.setup_vector(5, [-2.0, -0.1, 3.1, 5.2, 11.1])
    rank_result = model.converter('rank_result')
    rank_result.equation = rank_vector.arr_rank(1)
    return rank_result, rank_vector


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{rank}
    \left(
    \begin{pmatrix}
    -2.0\\
    -0.1\\
    3.1\\
    5.2\\
    11.1
    \end{pmatrix}
    ,
    1
    \right)
    =
    11.1
    \end{equation*}
    """)
    return


@app.cell
def _(mo, rank_result):
    with mo.capture_stdout() as captured_11:
        print(rank_result(1))

    mo.plain_text(captured_11.getvalue())
    return


@app.cell
def _(model, rank_vector):
    #The fourth-highest element
    rank_result_fourth = model.converter('rank_result_fourth')
    rank_result_fourth.equation = rank_vector.arr_rank(4)
    return (rank_result_fourth,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{rank}
    \left(
    \begin{pmatrix}
    -2.0\\
    -0.1\\
    3.1\\
    5.2\\
    11.1
    \end{pmatrix}
    ,
    4
    \right)
    =
    -0.1
    \end{equation*}
    """)
    return


@app.cell
def _(mo, rank_result_fourth):
    with mo.capture_stdout() as captured_12:
        print(rank_result_fourth(1))

    mo.plain_text(captured_12.getvalue())
    return


@app.cell
def _(model, rank_vector):
    #The lowest element
    rank_result_lowest = model.converter('rank_result_lowest')
    rank_result_lowest.equation = rank_vector.arr_rank(-1)
    return (rank_result_lowest,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{rank}
    \left(
    \begin{pmatrix}
    -2.0\\
    -0.1\\
    3.1\\
    5.2\\
    11.1
    \end{pmatrix}
    ,
    -1
    \right)
    =
    -2.0
    \end{equation*}
    """)
    return


@app.cell
def _(mo, rank_result_lowest):
    with mo.capture_stdout() as captured_13:
        print(rank_result_lowest(1))

    mo.plain_text(captured_13.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Array Mean
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Calculates the element-wise mean of an array.
    """)
    return


@app.cell
def _(model):
    #Calculate the element-wise mean of a named matrix
    mean_matrix = model.converter('mean_matrix')
    mean_matrix.setup_named_matrix({
        'value1': {'value11': 2.0, 'value12': 4.0},
        'value2': {'value21': 6.0, 'value22': 8.0},
        'value3': {'value31': 10.0, 'value32': 12.0},
    })
    mean_result = model.converter('mean_result')
    mean_result.equation = mean_matrix.arr_mean()
    return (mean_result,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{aligned}
    &\text{mean}
    \begin{pmatrix}
    \text{'value1'}: & \{\text{'value11'}: 2.0,\; \text{'value12'}: 4.0\} \\
    \text{'value2'}: & \{\text{'value21'}: 6.0,\; \text{'value22'}: 8.0\} \\
    \text{'value3'}: & \{\text{'value31'}: 10.0,\; \text{'value32'}: 12.0\}
    \end{pmatrix} \\[2pt]
    &=
    \frac{2.0 + 4.0 + 6.0 + 8.0 + 10.0 + 12.0}{6} = 7.0
    \end{aligned}
    \end{equation*}
    """)
    return


@app.cell
def _(mean_result, mo):
    with mo.capture_stdout() as captured_14:
        print(mean_result(1))

    mo.plain_text(captured_14.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Array Median
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Calculates the element-wise median of an array.
    """)
    return


@app.cell
def _(model):
    #Calculate the median of a not-named vector
    median_odd = model.converter('median_odd')
    median_odd.setup_vector(5, [-2.0, -0.1, 3.1, 5.2, 11.1])
    median_even = model.converter('median_even')
    median_even.setup_vector(4, [-2.0, -0.1, 3.1, 5.2])
    median_result = model.converter('median_result')
    median_result.equation = median_odd.arr_median()
    return median_result, median_even


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{median}
    \begin{pmatrix}
    -2.0\\
    -0.1\\
    3.1\\
    5.2\\
    11.1
    \end{pmatrix}
    =
    3.1
    \end{equation*}
    """)
    return


@app.cell
def _(median_result, mo):
    with mo.capture_stdout() as captured_15:
        print(median_result(1))

    mo.plain_text(captured_15.getvalue())
    return


@app.cell
def _(median_even, model):
    #The median of an even number of elements
    median_result_even = model.converter('median_result_even')
    median_result_even.equation = median_even.arr_median()
    return (median_result_even,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{median}
    \begin{pmatrix}
    -2.0\\
    -0.1\\
    3.1\\
    5.2\\
    \end{pmatrix}
    =
    \frac{-0.1+3.1}{2}=1.5
    \end{equation*}
    """)
    return


@app.cell
def _(median_result_even, mo):
    with mo.capture_stdout() as captured_16:
        print(median_result_even(1))

    mo.plain_text(captured_16.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Array Standard Deviation
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Calculates the element-wise standard deviation of an array.
    """)
    return


@app.cell
def _(model):
    #Calculate the standard deviation of a not-named matrix
    stddev_matrix = model.converter('stddev_matrix')
    stddev_matrix.setup_matrix([2, 2], [[1.0, 3.0], [3.0, 1.0]])
    stddev_result = model.converter('stddev_result')
    stddev_result.equation = stddev_matrix.arr_stddev()
    return (stddev_result,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \sigma
    \begin{pmatrix}
    1.0 & 3.0\\
    3.0 & 1.0
    \end{pmatrix}
    = \sqrt{
    \frac{1}{4}
    \cdot
    \left(
    (1-2)^2
    +
    (3-2)^2
    +
    (3-2)^2
    +
    (1-2)^2
    \right)
    }
    =
    1
    \end{equation*}
    """)
    return


@app.cell
def _(mo, stddev_result):
    with mo.capture_stdout() as captured_17:
        print(stddev_result(1))

    mo.plain_text(captured_17.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Array Maximum and Minimum
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `arr_max` returns the largest value of an array, `arr_min` the smallest - over every
    element of a vector or every cell of a matrix.

    Both take no arguments, and both return a single value however arrayed the input is.
    On an element with no sub-elements they return 0.0, as the other aggregations do.
    """)
    return


@app.cell
def _(model):
    extremes_matrix = model.converter('extremes_matrix')
    extremes_matrix.setup_matrix([2, 2], [[3.0, 8.0], [1.0, 5.0]])

    largest = model.converter('largest')
    largest.equation = extremes_matrix.arr_max()

    smallest = model.converter('smallest')
    smallest.equation = extremes_matrix.arr_min()
    return extremes_matrix, largest, smallest


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \mathrm{arr\_max}
    \begin{pmatrix}
    3.0 & 8.0 \\
    1.0 & 5.0
    \end{pmatrix}
    = 8.0
    \qquad
    \mathrm{arr\_min}
    \begin{pmatrix}
    3.0 & 8.0 \\
    1.0 & 5.0
    \end{pmatrix}
    = 1.0
    \end{equation*}
    """)
    return


@app.cell
def _(largest, mo, smallest):
    with mo.capture_stdout() as captured_extremes:
        print("arr_max: " + str(largest(1)))
        print("arr_min: " + str(smallest(1)))

    mo.plain_text(captured_extremes.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Array Size
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Calculates the size of an array.

    For a vector, the length will be returned.
    For a matrix, the size of the highest level will be returned (for example 2 for a $2 \times 3$ matrix).
    """)
    return


@app.cell
def _(model):
    #Calculate the size of a not-named vector
    size_vector = model.converter('size_vector')
    size_vector.setup_vector(6, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    #Calculate the size of a not-named matrix
    size_matrix_one = model.converter('size_matrix_one')
    size_matrix_one.setup_matrix([2, 3], [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]])
    size_matrix_two = model.converter('size_matrix_two')
    size_matrix_two.setup_matrix([4, 3], [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]])
    size_result = model.converter('size_result')
    size_result.equation = size_vector.arr_size()
    return size_matrix_one, size_matrix_two, size_result


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{len}
    \begin{pmatrix}
    1.0\\
    1.0\\
    1.0\\
    1.0\\
    1.0\\
    1.0\\
    \end{pmatrix}
    =
    6
    \end{equation*}
    """)
    return


@app.cell
def _(mo, size_result):
    with mo.capture_stdout() as captured_18:
        print(size_result(1))

    mo.plain_text(captured_18.getvalue())
    return


@app.cell
def _(model, size_matrix_one):
    #Calculate the size of a not-named matrix
    size_result_matrix_one = model.converter('size_result_matrix_one')
    size_result_matrix_one.equation = size_matrix_one.arr_size()
    return (size_result_matrix_one,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{len}
    \begin{pmatrix}
    1.0 & 1.0 & 1.0\\
    1.0 & 1.0 & 1.0
    \end{pmatrix}
    =
    2
    \end{equation*}
    """)
    return


@app.cell
def _(mo, size_result_matrix_one):
    with mo.capture_stdout() as captured_19:
        print(size_result_matrix_one(1))

    mo.plain_text(captured_19.getvalue())
    return


@app.cell
def _(model, size_matrix_two):
    #Calculate the size of a larger not-named matrix
    size_result_matrix_two = model.converter('size_result_matrix_two')
    size_result_matrix_two.equation = size_matrix_two.arr_size()
    return (size_result_matrix_two,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{len}
    \begin{pmatrix}
    1.0 & 1.0 & 1.0\\
    1.0 & 1.0 & 1.0\\
    1.0 & 1.0 & 1.0\\
    1.0 & 1.0 & 1.0
    \end{pmatrix}
    =
    4
    \end{equation*}
    """)
    return


@app.cell
def _(mo, size_result_matrix_two):
    with mo.capture_stdout() as captured_20:
        print(size_result_matrix_two(1))

    mo.plain_text(captured_20.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Array Dot
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The Dot function provides the classical vector/matrix-multiplication logic. That means, the following can be calculated:

    | Factor 1 | Factor 2 | Result |
    |-|-|-|
    | Vector of size $m$ | Constant | Vector of size $m$ |
    | Constant | Vector of size $m$ | Vector of size $m$ |
    | Matrix of size $m \times n$ | Constant  | Matrix of size $m \times n$ |
    | Constant | Matrix of size $m \times n$  | Matrix of size $m \times n$ |
    | Vector of size $m$ | Vector of size $m$  | Value (Scalar Product) |
    | Vector of size $m$ | Matrix of size $m \times n$ | Vector of size $n$ |
    | Matrix of size $m \times n$ | Vector of size $n$ | Vector of size $m$ |
    | Matrix of size $m \times n$ | Matrix of size $n \times p$ | Matrix of size $m \times p$ |

    ❗ Using the Dot function for an array and a constant yields the same result as using the $*$-Operator for the array and the value of the constant.

    If the dimensions of the arrays to which the dot function is applied do not allow for a valid array multiplication, an exception is thrown.

    **Named arrays follow the same table, with labels in place of sizes.** The axis that is
    summed over has to carry the same labels on both sides - the labels of a vector against
    the rows of a matrix, the columns of the left matrix against the rows of the right one.
    The axes that survive keep their own labels: rows come from the left operand, columns
    from the right. A vector times a matrix is therefore labelled by the matrix's columns,
    because its rows are exactly what the sum consumed.

    Three things follow from that:

    * The operands are paired **by label, not by position**, so the two may list their
      labels in a different order.
    * A named matrix has to carry **the same column labels in every row**. A matrix whose
      rows carry different labels is legal everywhere else, but here there would be no
      single axis to sum over.
    * A named array **cannot be multiplied with an unnamed one** - there is nothing for the
      labels to line up against.

    The examples below show each shape once. Where a product has two directions, one of
    them is named and the other is not.
    """)
    return


@app.cell
def _(model):
    #Calculate vector * constant & constant * vector
    constant = model.converter('constant')
    constant.equation = 2.0
    dot_vector_left = model.converter('dot_vector_left')
    dot_vector_left.setup_vector(3, [1.0, 2.0, 3.0])
    dot_vector_right = model.converter('dot_vector_right')
    dot_vector_right.setup_vector(3, [4.0, 5.0, 6.0])
    dot_result_one = model.converter('dot_result_one')
    dot_result_one.equation = dot_vector_left.dot(constant)
    return constant, dot_result_one, dot_vector_left, dot_vector_right


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix} 1.0 \\ 2.0 \\ 3.0 \end{pmatrix} \cdot 2.0
    =
    \begin{pmatrix} 2.0 \\ 4.0 \\ 6.0 \end{pmatrix}\end{equation*}
    """)
    return


@app.cell
def _(dot_result_one, mo):
    with mo.capture_stdout() as captured_21:
        print("[" + str(dot_result_one[0](1)) + " , " + str(dot_result_one[1](1)) + " , " + str(dot_result_one[2](1)) + "]")

    mo.plain_text(captured_21.getvalue())
    return


@app.cell
def _(constant, model):
    #Calculate constant * vector, this time with a named vector
    dot_named_vector = model.converter('dot_named_vector')
    dot_named_vector.setup_named_vector({'a': 4.0, 'b': 5.0, 'c': 6.0})
    dot_result_constant_vector = model.converter('dot_result_constant_vector')
    dot_result_constant_vector.equation = constant.dot(dot_named_vector)
    return dot_named_vector, dot_result_constant_vector


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The other direction, and with a **named** vector. A constant multiplies every cell, so
    there is no axis to line up and the labels come through untouched:

    \begin{equation*}
    2.0 \cdot
    \begin{pmatrix}
    \text{'a'}: & 4.0 \\
    \text{'b'}: & 5.0 \\
    \text{'c'}: & 6.0
    \end{pmatrix}
    =
    \begin{pmatrix}
    \text{'a'}: & 8.0 \\
    \text{'b'}: & 10.0 \\
    \text{'c'}: & 12.0
    \end{pmatrix}\end{equation*}
    """)
    return


@app.cell
def _(dot_result_constant_vector, mo):
    with mo.capture_stdout() as captured_22:
        print("{a: " + str(dot_result_constant_vector['a'](1))
              + " , b: " + str(dot_result_constant_vector['b'](1))
              + " , c: " + str(dot_result_constant_vector['c'](1)) + "}")

    mo.plain_text(captured_22.getvalue())
    return


@app.cell
def _(model):
    #Calculate matrix * constant & constant * matrix
    constant_1 = model.converter('constant_matrix_factor')
    constant_1.equation = 2.0
    dot_matrix_one = model.converter('dot_matrix_one')
    dot_matrix_one.setup_matrix([3, 2], [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    dot_matrix_two = model.converter('dot_matrix_two')
    dot_matrix_two.setup_matrix([2, 3], [[-1.0, -2.0, -3.0], [-4.0, -5.0, -6.0]])
    dot_result_two = model.converter('dot_result_two')
    dot_result_two.equation = dot_matrix_one.dot(constant_1)
    return constant_1, dot_result_two, dot_matrix_one, dot_matrix_two


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    1.0 & 2.0 \\
    3.0 & 4.0 \\
    5.0 & 6.0
    \end{pmatrix} \cdot 2.0
    =
    \begin{pmatrix}
    2.0 & 4.0 \\
    6.0 & 8.0 \\
    10.0 & 12.0
    \end{pmatrix}\end{equation*}
    """)
    return


@app.cell
def _(dot_result_two, mo):
    with mo.capture_stdout() as captured_23:
        print("[ " + "[" + str(dot_result_two[0][0](1)) + " , " + str(dot_result_two[0][1](1)) + "]")
        print("  " + "[" + str(dot_result_two[1][0](1)) + " , " + str(dot_result_two[1][1](1)) + "]")
        print("  " + "[" + str(dot_result_two[2][0](1)) + " , " + str(dot_result_two[2][1](1)) + "]" + " ]")

    mo.plain_text(captured_23.getvalue())
    return


@app.cell
def _(constant_1, model):
    #Calculate constant * matrix, this time with a named matrix
    dot_named_costs = model.converter('dot_named_costs')
    dot_named_costs.setup_named_matrix({
        'north': {'a': -1.0, 'b': -2.0, 'c': -3.0},
        'south': {'a': -4.0, 'b': -5.0, 'c': -6.0},
    })
    dot_result_constant_matrix = model.converter('dot_result_constant_matrix')
    dot_result_constant_matrix.equation = constant_1.dot(dot_named_costs)
    return dot_named_costs, dot_result_constant_matrix


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    A **named** matrix this time, with rows `north` and `south` and columns `a`, `b` and
    `c`. As with the vector, a constant leaves the labels alone:

    \begin{equation*}
    \begin{aligned}
    &2.0 \cdot
    \begin{pmatrix}
    \text{'north'}: & \{\text{'a'}: -1.0,\; \text{'b'}: -2.0,\; \text{'c'}: -3.0\} \\
    \text{'south'}: & \{\text{'a'}: -4.0,\; \text{'b'}: -5.0,\; \text{'c'}: -6.0\}
    \end{pmatrix} \\[2pt]
    &=
    \begin{pmatrix}
    \text{'north'}: & \{\text{'a'}: -2.0,\; \text{'b'}: -4.0,\; \text{'c'}: -6.0\} \\
    \text{'south'}: & \{\text{'a'}: -8.0,\; \text{'b'}: -10.0,\; \text{'c'}: -12.0\}
    \end{pmatrix}
    \end{aligned}
    \end{equation*}
    """)
    return


@app.cell
def _(dot_result_constant_matrix, mo):
    with mo.capture_stdout() as captured_24:
        for _row in ('north', 'south'):
            print(_row + ": {a: " + str(dot_result_constant_matrix[_row]['a'](1))
                  + " , b: " + str(dot_result_constant_matrix[_row]['b'](1))
                  + " , c: " + str(dot_result_constant_matrix[_row]['c'](1)) + "}")

    mo.plain_text(captured_24.getvalue())
    return


@app.cell
def _(model, dot_vector_left, dot_vector_right):
    #Calculate vector * vector
    dot_result_three = model.converter('dot_result_three')
    dot_result_three.equation = dot_vector_left.dot(dot_vector_right)
    return (dot_result_three,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \left\langle
    \begin{pmatrix} 1.0 \\ 2.0 \\ 3.0 \end{pmatrix},
    \begin{pmatrix} 4.0 \\ 5.0 \\ 6.0 \end{pmatrix}
    \right\rangle
    =
    1.0 \cdot 4.0 + 2.0 \cdot 5.0 + 3.0 \cdot 6.0
    =
    32.0
    \end{equation*}
    """)
    return


@app.cell
def _(dot_result_three, mo):
    with mo.capture_stdout() as captured_25:
        print(dot_result_three(1)) #1*4 + 2*5 + 3*6 = 32

    mo.plain_text(captured_25.getvalue())
    return


@app.cell
def _(dot_named_vector, model):
    #Calculate vector * vector with labels
    dot_named_scrambled = model.converter('dot_named_scrambled')
    dot_named_scrambled.setup_named_vector({'c': 3.0, 'b': 2.0, 'a': 1.0})
    dot_result_named_vectors = model.converter('dot_result_named_vectors')
    dot_result_named_vectors.equation = dot_named_vector.dot(dot_named_scrambled)
    return dot_named_scrambled, dot_result_named_vectors


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The same scalar product with **named** vectors. The right operand lists its labels in
    the opposite order, which changes nothing: `a` meets `a`, `b` meets `b`, `c` meets `c`.

    \begin{equation*}
    \begin{aligned}
    \left\langle
    \begin{pmatrix}
    \text{'a'}: & 4.0 \\
    \text{'b'}: & 5.0 \\
    \text{'c'}: & 6.0
    \end{pmatrix},
    \begin{pmatrix}
    \text{'c'}: & 3.0 \\
    \text{'b'}: & 2.0 \\
    \text{'a'}: & 1.0
    \end{pmatrix}
    \right\rangle
    &=
    4.0 \cdot 1.0 + 5.0 \cdot 2.0 + 6.0 \cdot 3.0 \\[2pt]
    &=
    32.0
    \end{aligned}
    \end{equation*}
    """)
    return


@app.cell
def _(dot_result_named_vectors, mo):
    with mo.capture_stdout() as captured_named_vectors:
        print(dot_result_named_vectors(1)) #4*1 + 5*2 + 6*3 = 32

    mo.plain_text(captured_named_vectors.getvalue())
    return


@app.cell
def _(dot_matrix_one, model, dot_vector_left):
    #Calculate vector * matrix & matrix * vector
    dot_result_four = model.converter('dot_result_four')
    dot_result_four.equation = dot_vector_left.dot(dot_matrix_one)
    return (dot_result_four,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    1.0 & 2.0 & 3.0 \\
    \end{pmatrix}
    \cdot
    \begin{pmatrix}
    1.0 & 2.0 \\
    3.0 & 4.0 \\
    5.0 & 6.0 \\
    \end{pmatrix}
    =
    \begin{pmatrix}
    1.0 \cdot 1.0 + 2.0 \cdot 3.0 + 3.0 \cdot 5.0 \\
    1.0 \cdot 2.0 + 2.0 \cdot 4.0 + 3.0 \cdot 6.0 \\
    \end{pmatrix}
    =
    \begin{pmatrix}
    22.0 & 28.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(dot_result_four, mo):
    with mo.capture_stdout() as captured_26:
        print("[" + str(dot_result_four[0](1)) + " , " + str(dot_result_four[1](1))  + "]")

    mo.plain_text(captured_26.getvalue())
    return


@app.cell
def _(dot_named_scrambled, model):
    #Calculate vector * matrix with labels
    dot_named_price = model.converter('dot_named_price')
    dot_named_price.setup_named_matrix({
        'a': {'online': 1.0, 'retail': 2.0},
        'b': {'online': 3.0, 'retail': 4.0},
        'c': {'online': 5.0, 'retail': 6.0},
    })
    dot_result_named_vector_matrix = model.converter('dot_result_named_vector_matrix')
    dot_result_named_vector_matrix.equation = dot_named_scrambled.dot(dot_named_price)
    return dot_named_price, dot_result_named_vector_matrix


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The same product with labels. The vector is labelled by product and so are the rows of
    the matrix - that is the axis the sum runs over, and it disappears. What is left are the
    matrix's columns, so the result is labelled `online` and `retail`:

    \begin{equation*}
    \begin{aligned}
    &\begin{pmatrix}
    \text{'a'}: & 1.0 \\
    \text{'b'}: & 2.0 \\
    \text{'c'}: & 3.0
    \end{pmatrix}
    \cdot
    \begin{pmatrix}
    \text{'a'}: & \{\text{'online'}: 1.0,\; \text{'retail'}: 2.0\} \\
    \text{'b'}: & \{\text{'online'}: 3.0,\; \text{'retail'}: 4.0\} \\
    \text{'c'}: & \{\text{'online'}: 5.0,\; \text{'retail'}: 6.0\}
    \end{pmatrix} \\[2pt]
    &=
    \begin{pmatrix}
    \text{'online'}: & 1.0 \cdot 1.0 + 2.0 \cdot 3.0 + 3.0 \cdot 5.0 \\
    \text{'retail'}: & 1.0 \cdot 2.0 + 2.0 \cdot 4.0 + 3.0 \cdot 6.0
    \end{pmatrix} \\[2pt]
    &=
    \begin{pmatrix}
    \text{'online'}: & 22.0 \\
    \text{'retail'}: & 28.0
    \end{pmatrix}
    \end{aligned}
    \end{equation*}
    """)
    return


@app.cell
def _(dot_result_named_vector_matrix, mo):
    with mo.capture_stdout() as captured_named_vector_matrix:
        print("{online: " + str(dot_result_named_vector_matrix['online'](1))
              + " , retail: " + str(dot_result_named_vector_matrix['retail'](1)) + "}")

    mo.plain_text(captured_named_vector_matrix.getvalue())
    return


@app.cell
def _(dot_matrix_two, dot_vector_right, model):
    #Calculate matrix * vector
    dot_result_matrix_vector = model.converter('dot_result_matrix_vector')
    dot_result_matrix_vector.equation = dot_matrix_two.dot(dot_vector_right)
    return (dot_result_matrix_vector,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{aligned}
    &\begin{pmatrix}
    -1.0 & -2.0 & -3.0 \\
    -4.0 & -5.0 & -6.0 \\
    \end{pmatrix}
    \cdot
    \begin{pmatrix}
    4.0 \\
    5.0 \\
    6.0 \\
    \end{pmatrix} \\[2pt]
    &=
    \begin{pmatrix}
    -1.0 \cdot 4.0 + (-2.0) \cdot 5.0 + (-3.0) \cdot 6.0 \\
    -4.0 \cdot 4.0 + (-5.0) \cdot 5.0 + (-6.0) \cdot 6.0 \\
    \end{pmatrix} \\[2pt]
    &=
    \begin{pmatrix}
    -32.0 \\
    -77.0
    \end{pmatrix}
    \end{aligned}
    \end{equation*}
    """)
    return


@app.cell
def _(dot_result_matrix_vector, mo):
    with mo.capture_stdout() as captured_27:
        print("[" + str(dot_result_matrix_vector[0](1)) + " , " + str(dot_result_matrix_vector[1](1)) + "]")

    mo.plain_text(captured_27.getvalue())
    return


@app.cell
def _(dot_named_costs, dot_named_vector, model):
    #Calculate matrix * vector with labels
    dot_result_named_matrix_vector = model.converter('dot_result_named_matrix_vector')
    dot_result_named_matrix_vector.equation = dot_named_costs.dot(dot_named_vector)
    return (dot_result_named_matrix_vector,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And with labels - the same numbers, reusing the named matrix and the named vector from
    further up. Here the sum runs over the *columns* of the matrix, which carry the product
    labels, so what survives are its rows:

    \begin{equation*}
    \begin{aligned}
    &\begin{pmatrix}
    \text{'north'}: & \{\text{'a'}: -1.0,\; \text{'b'}: -2.0,\; \text{'c'}: -3.0\} \\
    \text{'south'}: & \{\text{'a'}: -4.0,\; \text{'b'}: -5.0,\; \text{'c'}: -6.0\}
    \end{pmatrix}
    \cdot
    \begin{pmatrix}
    \text{'a'}: & 4.0 \\
    \text{'b'}: & 5.0 \\
    \text{'c'}: & 6.0
    \end{pmatrix} \\[2pt]
    &=
    \begin{pmatrix}
    \text{'north'}: & -1.0 \cdot 4.0 + (-2.0) \cdot 5.0 + (-3.0) \cdot 6.0 \\
    \text{'south'}: & -4.0 \cdot 4.0 + (-5.0) \cdot 5.0 + (-6.0) \cdot 6.0
    \end{pmatrix} \\[2pt]
    &=
    \begin{pmatrix}
    \text{'north'}: & -32.0 \\
    \text{'south'}: & -77.0
    \end{pmatrix}
    \end{aligned}
    \end{equation*}
    """)
    return


@app.cell
def _(dot_result_named_matrix_vector, mo):
    with mo.capture_stdout() as captured_named_matrix_vector:
        print("{north: " + str(dot_result_named_matrix_vector['north'](1))
              + " , south: " + str(dot_result_named_matrix_vector['south'](1)) + "}")

    mo.plain_text(captured_named_matrix_vector.getvalue())
    return


@app.cell
def _(model):
    #Calculate matrix * matrix
    dot_matrix_three = model.converter('dot_matrix_three')
    dot_matrix_three.setup_matrix([2, 2], [[1.0, 2.0], [3.0, 4.0]])
    dot_matrix_four = model.converter('dot_matrix_four')
    dot_matrix_four.setup_matrix([2, 2], [[-1.0, -2.0], [-4.0, -5.0]])
    dot_result_five = model.converter('dot_result_five')
    dot_result_five.equation = dot_matrix_three.dot(dot_matrix_four)
    return (dot_result_five,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{aligned}
    &\begin{pmatrix}
    1.0 & 2.0 \\
    3.0 & 4.0 \\
    \end{pmatrix}
    \cdot
    \begin{pmatrix}
    -1.0 & -2.0 \\
    -4.0 & -5.0 \\
    \end{pmatrix} \\[2pt]
    &=
    \begin{pmatrix}
    1.0 \cdot (-1.0) + 2.0 \cdot (-4.0) & 1.0 \cdot (-2.0) + 2.0 \cdot (-5.0) \\
    3.0 \cdot (-1.0) + 4.0 \cdot (-4.0) & 3.0 \cdot (-2.0) + 4.0 \cdot (-5.0) \\
    \end{pmatrix} \\[2pt]
    &=
    \begin{pmatrix}
    -9 & -12 \\
    -19 & -26\\
    \end{pmatrix}
    \end{aligned}
    \end{equation*}
    """)
    return


@app.cell
def _(dot_result_five, mo):
    with mo.capture_stdout() as captured_28:
        print("[ " + "["    + str(dot_result_five[0][0](1)) + " , " + str(dot_result_five[0][1](1)) + "]")
        print("  " + "["    + str(dot_result_five[1][0](1)) + " , " + str(dot_result_five[1][1](1)) + "]" + " ]")

    mo.plain_text(captured_28.getvalue())
    return


@app.cell
def _(model):
    #Calculate matrix * matrix with labels
    dot_named_shipments = model.converter('dot_named_shipments')
    dot_named_shipments.setup_named_matrix({
        'north': {'a': 1.0, 'b': 2.0},
        'south': {'a': 3.0, 'b': 4.0},
    })
    dot_named_margin = model.converter('dot_named_margin')
    dot_named_margin.setup_named_matrix({
        'a': {'online': -1.0, 'retail': -2.0},
        'b': {'online': -4.0, 'retail': -5.0},
    })
    dot_result_named_matrices = model.converter('dot_result_named_matrices')
    dot_result_named_matrices.equation = dot_named_shipments.dot(dot_named_margin)
    return dot_named_margin, dot_named_shipments, dot_result_named_matrices


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The same matrix product with labels. The left matrix runs from regions to products, the
    right one from products to channels - the products are what the two have in common and
    what the sum consumes. The result runs from regions to channels: its rows come from the
    left operand, its columns from the right.

    \begin{equation*}
    \begin{aligned}
    &\begin{pmatrix}
    \text{'north'}: & \{\text{'a'}: 1.0,\; \text{'b'}: 2.0\} \\
    \text{'south'}: & \{\text{'a'}: 3.0,\; \text{'b'}: 4.0\}
    \end{pmatrix}
    \cdot
    \begin{pmatrix}
    \text{'a'}: & \{\text{'online'}: -1.0,\; \text{'retail'}: -2.0\} \\
    \text{'b'}: & \{\text{'online'}: -4.0,\; \text{'retail'}: -5.0\}
    \end{pmatrix} \\[2pt]
    &=
    \begin{pmatrix}
    \text{'north'}: & \{\text{'online'}: 1.0 \cdot (-1.0) + 2.0 \cdot (-4.0), \\
    & \phantom{\{} \text{'retail'}: 1.0 \cdot (-2.0) + 2.0 \cdot (-5.0)\} \\[2pt]
    \text{'south'}: & \{\text{'online'}: 3.0 \cdot (-1.0) + 4.0 \cdot (-4.0), \\
    & \phantom{\{} \text{'retail'}: 3.0 \cdot (-2.0) + 4.0 \cdot (-5.0)\}
    \end{pmatrix} \\[2pt]
    &=
    \begin{pmatrix}
    \text{'north'}: & \{\text{'online'}: -9.0,\; \text{'retail'}: -12.0\} \\
    \text{'south'}: & \{\text{'online'}: -19.0,\; \text{'retail'}: -26.0\}
    \end{pmatrix}
    \end{aligned}
    \end{equation*}
    """)
    return


@app.cell
def _(dot_result_named_matrices, mo):
    with mo.capture_stdout() as captured_named_matrices:
        for _row in ('north', 'south'):
            print(_row + ": {online: " + str(dot_result_named_matrices[_row]['online'](1))
                  + " , retail: " + str(dot_result_named_matrices[_row]['retail'](1)) + "}")

    mo.plain_text(captured_named_matrices.getvalue())
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A simple Example
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Lets have a look on a concrete example, how a multidimensional SD Model can look like.

    Consider an investment depot with two accounts:

    - bank account
    - depot account

    Both accounts will have different deposit rates and different interest rates each year.
    We want to investigate the value development of the bank account, the depot account and the whole investment depot.

    Lets set up the model:
    """)
    return


@app.cell
def _(model):
    account = model.stock('account')
    account.setup_named_vector({'bank': 0.0, 'depot': 0.0})
    accountInitialValues = model.constant('accountInitialValues')
    #define the initial values of the accounts
    accountInitialValues.setup_named_vector({'bank': 1000.0, 'depot': 500.0})
    account['bank'].initial_value = accountInitialValues['bank']
    account['depot'].initial_value = accountInitialValues['depot']
    interestRate = model.constant('interestRate')
    interestRate.setup_named_vector({'bank': 0.02, 'depot': 0.1})
    depositRate = model.constant('depositRate')
    #define the interest rates
    depositRate.setup_named_vector({'bank': 200.0, 'depot': 100.0})
    deposit = model.flow('deposit')
    deposit.equation = depositRate * 1
    #define the deposit rates
    interest = model.flow('interest')
    interest.equation = account * interestRate
    account.equation = deposit + interest
    #define the flows
    totalValue = model.converter('totalValue')
    #set the equation for the stock value
    #finally define a converter for the total value of the account
    totalValue.equation = account.arr_sum()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As always we define a scenario manager and scenarios:
    """)
    return


@app.cell
def _(model, arrays_bptk):
    arrays_bptk.register_model(model)
    scenario_manager = {'sm': {
        'model': model,
        'base_constants': {
            'interestRate[bank]': 0.02,
            'interestRate[depot]': 0.1,
            'depositRate[bank]': 200,
            'depositRate[depot]': 100,
            'accountInitialValues[bank]': 1000.0,
            'accountInitialValues[depot]': 500.0,
        },
    }}
    arrays_bptk.register_scenario_manager(scenario_manager)
    arrays_bptk.register_scenarios(
        scenario_manager='sm',
        scenarios={
            'base': {},
            'scenarioHighDepotInterestRate': {'constants': {'interestRate[depot]': 0.2}},
            'scenarioHighDepotDepositRate': {'constants': {'depositRate[depot]': 250.0}},
            'scenarioHighDepotInitialValue': {'constants': {'accountInitialValues[depot]': 750.0}},
        },
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And plot the results:
    """)
    return


@app.cell
def _(arrays_bptk):
    arrays_bptk.plot_scenarios(
        scenarios=['base'],
        scenario_managers='sm',
        equations=['account[bank]', 'account[depot]', 'totalValue'],
        series_names={},
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As always we can compare different scenarios with each other by plotting them simultaneously:
    """)
    return


@app.cell
def _(arrays_bptk):
    arrays_bptk.plot_scenarios(
        scenarios=[
            'base',
            'scenarioHighDepotInterestRate',
            'scenarioHighDepotDepositRate',
            'scenarioHighDepotInitialValue',
        ],
        scenario_managers='sm',
        equations=['totalValue'],
        series_names={},
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
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
