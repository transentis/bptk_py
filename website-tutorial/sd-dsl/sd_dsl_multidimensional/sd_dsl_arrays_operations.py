# Front matter the .py format cannot carry; injected on export.
# description: Which operators and functions work on arrayed SD DSL elements, and what each one returns
# keywords: system dynamics, systemdynamics, sd dsl, arrays, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Operations on Arrayed Components")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Operations on Arrayed Components
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
    ## Standard Operations
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
    ### Addition ($+$)
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
    ### Subtraction ($-$)
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
    ### Multiplication ($*$)
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
    ### Division ($/$)
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
    ### Power ($**$) and Modulo ($\%$)

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
    ### Math Functions

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
    ### Comparisons, `If`, `And`, `Or`, `Not`

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
    ### `max` and `min`

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
    ### `smooth`, `trend` and `delay`

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

if __name__ == "__main__":
    app.run()
