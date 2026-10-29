# Front matter the .py format cannot carry; injected on export.
# description: The array functions of the SD DSL - sum, product, rank, mean, median, standard deviation, maximum, minimum, size and dot, along one dimension or over the whole, and interpolate
# keywords: system dynamics, systemdynamics, sd dsl, arrays, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Array Functions")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Array Functions
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
    ## Array Sum
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
    ## Array Product
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Calculates the element-wise product of an array. A product is Stella's `PROD`; the XMILE standard has none.
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
    ## Array Largest
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
    rank_result.equation = rank_vector.arr_largest(1)
    return rank_result, rank_vector

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{largest}
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
    rank_result_fourth.equation = rank_vector.arr_largest(4)
    return (rank_result_fourth,)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{largest}
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
    rank_result_lowest.equation = rank_vector.arr_largest(-1)
    return (rank_result_lowest,)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{largest}
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
    ## Array Mean
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
    ## Array Median
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
    ## Array Standard Deviation
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
    ## Array Maximum and Minimum
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
    ## Array Size
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
    ## Array Dot
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
      rows carry different labels can be computed with, but here there would be no single
      axis to sum over.
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
    \begin{aligned}
    \begin{pmatrix}
    1.0 & 2.0 & 3.0 \\
    \end{pmatrix}
    \cdot
    \begin{pmatrix}
    1.0 & 2.0 \\
    3.0 & 4.0 \\
    5.0 & 6.0 \\
    \end{pmatrix}
    & =
    \begin{pmatrix}
    1.0 \cdot 1.0 + 2.0 \cdot 3.0 + 3.0 \cdot 5.0 \\
    1.0 \cdot 2.0 + 2.0 \cdot 4.0 + 3.0 \cdot 6.0 \\
    \end{pmatrix} \\
    & =
    \begin{pmatrix}
    22.0 & 28.0
    \end{pmatrix}
    \end{aligned}
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
    ## Aggregating Along One Dimension

    Every aggregation takes an optional `over`. Without it, it takes every entry and returns one number. With it, it aggregates a matrix along one dimension and returns a vector: `over=1` one value per row, `over=0` one value per column - XMILE's `SUM(A[M, *])`:
    """)
    return

@app.cell
def _(model):
    sales = model.converter('sales')
    sales.setup_named_matrix({'boston': {'q1': 10.0, 'q2': 20.0}, 'nyc': {'q1': 30.0, 'q2': 40.0}})
    sales_per_city = model.converter('sales_per_city')
    sales_per_city.equation = sales.arr_sum(over=1)
    best_quarter = model.converter('best_quarter')
    best_quarter.equation = sales.arr_max(over=0)
    return best_quarter, sales, sales_per_city


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{aligned}
    \text{sales} & = \begin{pmatrix}
    \text{'boston'}: & \{\text{'q1'}: 10.0,\; \text{'q2'}: 20.0\} \\
    \text{'nyc'}: & \{\text{'q1'}: 30.0,\; \text{'q2'}: 40.0\}
    \end{pmatrix} \\[1ex]
    \text{sales.arr\_sum(over=1)} & = \begin{pmatrix} \text{'boston'}: & 30.0 \\ \text{'nyc'}: & 70.0 \end{pmatrix} \\[1ex]
    \text{sales.arr\_max(over=0)} & = \begin{pmatrix} \text{'q1'}: & 30.0 \\ \text{'q2'}: & 40.0 \end{pmatrix}
    \end{aligned}
    \end{equation*}
    """)
    return

@app.cell
def _(best_quarter, mo, sales_per_city):
    with mo.capture_stdout() as captured_over:
        print("sales_per_city:", [sales_per_city[city](1) for city in ('boston', 'nyc')])
        print("best_quarter:  ", [best_quarter[quarter](1) for quarter in ('q1', 'q2')])

    mo.plain_text(captured_over.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Aggregating Parts and Expressions

    An aggregation takes any array, not only an arrayed element: a part of one, or an expression. XMILE writes `SUM(sales[boston, *])` and `SUM(price * quantity)`:
    """)
    return

@app.cell
def _(model, sales):
    boston_total = model.converter('boston_total')
    boston_total.equation = sales['boston', :].arr_sum()
    weighted = model.converter('weighted')
    weighted.equation = (sales * 0.5).arr_sum()
    return boston_total, weighted


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{aligned}
    \text{sales['boston', :].arr\_sum()} & = 10.0 + 20.0 = 30.0 \\[1ex]
    \text{(sales * 0.5).arr\_sum()} & = 0.5 \cdot (10.0 + 20.0 + 30.0 + 40.0) = 50.0
    \end{aligned}
    \end{equation*}
    """)
    return


@app.cell
def _(boston_total, mo, weighted):
    with mo.capture_stdout() as captured_parts:
        print("boston_total:", boston_total(1))
        print("weighted:    ", weighted(1))

    mo.plain_text(captured_parts.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Array Rank

    `array.arr_rank(r, tiebreak=None)` is XMILE's `RANK`: the **position** of the `r`-th smallest entry of a vector, counting from 1 as XMILE and Stella do - not the entry itself, which is what `arr_largest` returns. Entries of equal value are ordered by `tiebreak`, a vector of the same size, and then by position. A matrix is ranked by a row or a column, as in `sales[:, 'q1'].arr_rank(1)`; an `r` outside the vector gives NaN.
    """)
    return

@app.cell
def _(model, sd):
    bids = model.converter('bids')
    bids.setup_vector(4, [6.0, 2.0, 8.0, 5.0])
    second_lowest = model.converter('second_lowest')
    second_lowest.equation = bids.arr_rank(2)
    return bids, second_lowest


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{rank}\left(\begin{pmatrix} 6.0 & 2.0 & 8.0 & 5.0 \end{pmatrix}, 2\right) = 4
    \end{equation*}

    The second smallest bid, 5.0, stands at position 4. To read it from the vector, whose labels count from 0, subtract 1.
    """)
    return

@app.cell
def _(mo, second_lowest):
    with mo.capture_stdout() as captured_rank:
        print(second_lowest(1))

    mo.plain_text(captured_rank.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Array Interpolate

    `array.arr_interpolate(w1, w2)` is Stella's `INTERPOLATE`: a value between the entries of an array, with one weight per dimension. A weight of 0 is the first entry of its dimension, 1 the last, and between them the value is interpolated linearly - for a matrix first along the columns, then along the rows. Weights outside 0 to 1 are held at the ends.
    """)
    return

@app.cell
def _(model, sd):
    grid = model.converter('grid')
    grid.setup_matrix([2, 3], [[0.0, 2.0, 4.0], [8.0, 6.0, 5.0]])
    between = model.converter('between')
    between.equation = grid.arr_interpolate(0.75, 0.25)
    return (between,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{interpolate}\left(\begin{pmatrix} 0.0 & 2.0 & 4.0 \\ 8.0 & 6.0 & 5.0 \end{pmatrix}, 0.75, 0.25\right) = 5.5
    \end{equation*}

    A quarter of the way along the columns the rows read 1.0 and 7.0; three quarters of the way from the first row to the second gives 5.5.
    """)
    return

@app.cell
def _(between, mo):
    with mo.capture_stdout() as captured_interpolate:
        print(between(1))

    mo.plain_text(captured_interpolate.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Array Percentile

    `array.arr_percentile(percentile, lower=None, weights=None)` is Stella's `PERCENTILE`: the value below which `percentile` percent of the entries lie, over every entry of a vector or a matrix. `percentile` and `lower` lie between 0 and 100; anything else gives NaN and an `[ERROR]`.

    - **Without weights** the entries are sorted and the rank is `percentile * (n - 1) / 100`. A whole rank gives the entry there; a rank between two entries gives the **mean of the two**, not a value interpolated between them. So the result is a staircase: for four entries every percentile strictly between 0 and 33.3 gives the mean of the two smallest.
    - **With weights** - an array of the same size, each entry counted as often as its weight says - the rule is a different one: each entry stands at the middle of its share of the total weight, two neighbours meet at their mean on the border between their shares, and in between the value is interpolated in a straight line. Below the first middle and above the last the result is the smallest and the largest entry. With every weight 1 this is therefore not the same as no weights.
    - **`lower`** takes the value at that percentile off the result, so `arr_percentile(75.0, 25.0)` is the spread between the two. A `lower` of 0 takes nothing off: Stella writes 0 there when it needs the place for the weights.

    Both rules are Stella's own. They differ from the usual definitions, such as numpy's, and from each other - which is why they are spelled out here.
    """)
    return

@app.cell
def _(bids, model):
    lots = model.converter('lots')
    lots.setup_vector(4, [1.0, 1.0, 1.0, 3.0])
    middle_bid = model.converter('middle_bid')
    middle_bid.equation = bids.arr_percentile(50.0)
    weighted_bid = model.converter('weighted_bid')
    weighted_bid.equation = bids.arr_percentile(50.0, weights=lots)
    bid_spread = model.converter('bid_spread')
    bid_spread.equation = bids.arr_percentile(75.0, 25.0)
    return bid_spread, middle_bid, weighted_bid


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{aligned}
    b &= \begin{pmatrix} 6.0 & 2.0 & 8.0 & 5.0 \end{pmatrix} \\
    w &= \begin{pmatrix} 1 & 1 & 1 & 3 \end{pmatrix} \\
    \text{percentile}(b, 50) &= 5.5 \\
    \text{percentile}(b, 50, w) &= 5.1\overline{6} \\
    \text{percentile}(b, 75) - \text{percentile}(b, 25) &= 3.5
    \end{aligned}
    \end{equation*}

    Sorted, the bids are 2, 5, 6 and 8. The median rank is 1.5, between 5 and 6, so the result is their mean, 5.5. With three lots on the bid of 5, that bid holds half of the weight, its middle sits at 41.7 percent, and the border to the bid of 6 at 66.7 percent, where the value is 5.5; 50 percent lies a third of the way between them. The spread is 7.0 - 3.5: the 75th percentile, at rank 2.25, is the mean of 6 and 8, the 25th the mean of 2 and 5.
    """)
    return

@app.cell
def _(bid_spread, middle_bid, mo, weighted_bid):
    with mo.capture_stdout() as captured_percentile:
        print(middle_bid(1), weighted_bid(1), bid_spread(1))

    mo.plain_text(captured_percentile.getvalue())
    return


if __name__ == "__main__":
    app.run()
