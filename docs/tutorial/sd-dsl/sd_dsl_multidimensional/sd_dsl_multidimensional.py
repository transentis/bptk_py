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
    This document illustrates how vector- or matrix-valued SD Models can be defined.

    We start with some boilerplate to get a BPTK project up and running:
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model
    from BPTK_Py.bptk import bptk

    testbptk = bptk()
    model = Model(starttime=0.0, stoptime=15.0, dt=1.0, name="TestModel")
    return model, testbptk


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
    vector1 = model.converter('vector1')
    vector1.setup_vector(2, [2.0, 3.0])
    # Create a vector of length 2 with different values
    # Create a vector of length 2 with identical values
    vector1.setup_vector(2, 3.0)
    return


@app.cell
def _(model):
    ## Defining a named Vector (with string-valued indices)
    # Define a sd dsl element
    vector2 = model.converter('vector2')
    # Create a named vector of length 2 using string-valued indices
    vector2.setup_named_vector({'value1': 4.0, 'value2': 5.0})
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

    For matrices, we can proceed completely similar.
    """)
    return


@app.cell
def _(model):
    ## Defining a Matrix (with numerical indices)
    # Define a sd dsl element
    matrix1 = model.converter('matrix1')
    # Create a matrix of size 2x2 with different values
    matrix1.setup_matrix([2, 2], [[2.0, 3.0], [4.0, 5.0]])
    return


@app.cell
def _(model):
    ## Defining a named Matrix (with string-valued indices)
    # Define a sd dsl element
    matrix2 = model.converter('matrix2')
    # Create a named vector of lenght 2 using string-valued indices
    matrix2.setup_named_matrix({'value1': {'value11': 2.0, 'value12': 3.0}, 'value2': {'value21': 4.0, 'value22': 5.0}})
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
    """)
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
    The standard Operations (+, -, *, %) can be used for arrayed Components.
    Moreover some array-specific Operations are provided.
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
    It is possible to use the standard Operations (+, -, *, %) for:

    | Operand 1 | Operand 2 |
    |-|-|
    | Arrayed Element | Arrayed Element |
    | Arrayed Element | Float/Integer |
    | Float/Integer | Arrayed Element |

    ⚠️ If both operands are arrayed elements, they must have the same numerical/string-valued indices.

    That means it is **not** possible to have operand 1 = vector with numerical indices and operand 2 = vector with string-valued indicies, even if they have the same size.

    It is also **not** possible to have operand 1 = vector and operand 2 = matrix or vice versa.

    Other standard Operations (\*\*, //, %, ...) are **not** supported yet.

    Standard Operations are always performed element-wise.
    Lets have a look at some examples:
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
    vectorAdd1 = model.converter('vectorAdd1')
    vectorAdd1.setup_vector(2, [1.1, 2.2])
    vectorAdd2 = model.converter('vectorAdd2')
    vectorAdd2.setup_vector(2, [3.1, 4.2])
    addResult = model.converter('addResult')
    addResult.equation = vectorAdd1 + vectorAdd2
    return addResult, vectorAdd2


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
def _(addResult, mo, vectorAdd1, vectorAdd2):
    addResult.equation = vectorAdd1 + vectorAdd2
    with mo.capture_stdout() as captured:
        print("[ " + str(addResult[0](0)) + " , " + str(addResult[1](0)) + " ]")

    mo.plain_text(captured.getvalue())
    return




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
def _(addResult, mo, vectorAdd2):
    addResult.equation = vectorAdd2 + 1.0
    with mo.capture_stdout() as captured_1:
        print("[ " + str(addResult[0](0)) + " , " + str(addResult[1](0)) + " ]")

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
    matrixMinus1 = model.converter('matrixMinus1')
    matrixMinus1.setup_matrix([2, 2], [[1.1, 2.2], [3.3, 4.4]])
    matrixMinus2 = model.converter('matrixMinus2')
    matrixMinus2.setup_matrix([2, 2], [[5.5, 7.7], [3.3, 14.4]])
    minusResult = model.converter('minusResult')
    minusResult.equation = matrixMinus1 - matrixMinus2
    return matrixMinus2, minusResult


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
def _(matrixMinus1, matrixMinus2, minusResult, mo):
    minusResult.equation = matrixMinus1 - matrixMinus2
    with mo.capture_stdout() as captured_2:
        print("[ " + "[" + str(minusResult[0][0](1)) + " , " + str(minusResult[0][1](1)) + "]")
        print("  " + "[" + str(minusResult[1][0](1)) + " , " + str(minusResult[1][1](1)) + "]" + " ]")

    mo.plain_text(captured_2.getvalue())
    return




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
def _(matrixMinus2, minusResult, mo):
    minusResult.equation = matrixMinus2 - 1.0
    with mo.capture_stdout() as captured_3:
        print("[ " + "[" + str(minusResult[0][0](1)) + " , " + str(minusResult[0][1](1)) + "]")
        print("  " + "[" + str(minusResult[1][0](1)) + " , " + str(minusResult[1][1](1)) + "]" + " ]")

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
    vectorTimes1 = model.converter('vectorTimes1')
    vectorTimes1.setup_named_vector({'value1': 4.0, 'value2': 5.0})
    vectorTimes2 = model.converter('vectorTimes2')
    vectorTimes2.setup_named_vector({'value1': 6.0, 'value2': 7.0})
    timesResult = model.converter('timesResult')
    timesResult.equation = vectorTimes1 * vectorTimes2
    return timesResult, vectorTimes2


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    4.0\\
    5.0
    \end{pmatrix}
    \odot
    \begin{pmatrix}
    6.0\\
    7.0
    \end{pmatrix}
    =
    \begin{pmatrix}
    24.0\\
    35.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(mo, timesResult, vectorTimes1, vectorTimes2):
    timesResult.equation = vectorTimes1 * vectorTimes2
    with mo.capture_stdout() as captured_4:
        print("[ " + str(timesResult["value1"](0)) + " , " + str(timesResult["value2"](0)) + " ]")

    mo.plain_text(captured_4.getvalue())
    return




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    6.0\\
    7.0
    \end{pmatrix}
    \cdot
    3.0
    =
    \begin{pmatrix}
    18.0\\
    21.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(mo, timesResult, vectorTimes2):
    timesResult.equation = vectorTimes2 * 3.0
    with mo.capture_stdout() as captured_5:
        print("[ " + str(timesResult["value1"](0)) + " , " + str(timesResult["value2"](0)) + " ]")

    mo.plain_text(captured_5.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The case "- arrayed element" is a special case since it is interpreted as "(-1) $\cdot$ element":
    """)
    return


@app.cell
def _(model, vectorTimes2):
    #Multiplay named vector and numerical element
    timesResult_1 = model.converter('timesResult')
    timesResult_1.equation = -vectorTimes2
    return (timesResult_1,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    - \begin{pmatrix}
    6.0\\
    7.0
    \end{pmatrix}
    =
    \begin{pmatrix}
    -6.0\\
    -7.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(mo, timesResult_1, vectorTimes2):
    timesResult_1.equation = -vectorTimes2
    with mo.capture_stdout() as captured_6:
        print('[ ' + str(timesResult_1['value1'](0)) + ' , ' + str(timesResult_1['value2'](0)) + ' ]')

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
    matrixDivide1 = model.converter('matrixDivide1')
    matrixDivide1.setup_matrix([2, 2], [[2.0, 4.0], [8.0, 16.0]])
    matrixDivide2 = model.converter('matrixDivide2')
    matrixDivide2.setup_matrix([2, 2], [[2.0, 1.0], [0.5, 0.25]])
    divideResult = model.converter('divideResult')
    divideResult.equation = matrixDivide1 / matrixDivide2
    return divideResult, matrixDivide2


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
def _(divideResult, matrixDivide1, matrixDivide2, mo):
    divideResult.equation = matrixDivide1 / matrixDivide2
    with mo.capture_stdout() as captured_7:
        print("[ " + "[" + str(divideResult[0][0](1)) + " , " + str(divideResult[0][1](1)) + "]")
        print("  " + "[" + str(divideResult[1][0](1)) + " , " + str(divideResult[1][1](1)) + "]" + " ]")

    mo.plain_text(captured_7.getvalue())
    return




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
def _(divideResult, matrixDivide2, mo):
    divideResult.equation = matrixDivide2 / 5.0
    with mo.capture_stdout() as captured_8:
        print("[ " + "[" + str(divideResult[0][0](1)) + " , " + str(divideResult[0][1](1)) + "]")
        print("  " + "[" + str(divideResult[1][0](1)) + " , " + str(divideResult[1][1](1)) + "]" + " ]")

    mo.plain_text(captured_8.getvalue())
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
    vectorSum = model.converter('vectorSum')
    vectorSum.setup_named_vector({'value1': 1.0, 'value2': 2.0, 'value3': 3.0})
    sumResult = model.converter('sumResult')
    sumResult.equation = vectorSum.arr_sum()
    return (sumResult,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{sum}
    \begin{pmatrix}
    1.0 \\
    2.0\\
    3.0
    \end{pmatrix}
    =
    1.0 + 2.0 + 3.0 = 6.0
    \end{equation*}
    """)
    return


@app.cell
def _(mo, sumResult, vectorSum):
    sumResult.equation = vectorSum.arr_sum()
    with mo.capture_stdout() as captured_9:
        print(sumResult(1))

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
    matrixProd = model.converter('matrixProd')
    matrixProd.setup_matrix([2, 3], [[2.0, 3.0, 4.0], [5.0, 6.0, 7.0]])
    prodResult = model.converter('prodResult')
    prodResult.equation = matrixProd.arr_prod()
    return (prodResult,)


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
def _(matrixProd, mo, prodResult):
    prodResult.equation = matrixProd.arr_prod()
    with mo.capture_stdout() as captured_10:
        print(prodResult(1))

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
    vectorRank = model.converter('vectorRank')
    vectorRank.setup_vector(5, [-2.0, -0.1, 3.1, 5.2, 11.1])
    rankResult = model.converter('rankResult')
    rankResult.equation = vectorRank.arr_rank(1)
    return rankResult, vectorRank


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
def _(mo, rankResult, vectorRank):
    rankResult.equation = vectorRank.arr_rank(1)
    with mo.capture_stdout() as captured_11:
        print(rankResult(1))

    mo.plain_text(captured_11.getvalue())
    return




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
def _(mo, rankResult, vectorRank):
    rankResult.equation = vectorRank.arr_rank(4)
    with mo.capture_stdout() as captured_12:
        print(rankResult(1))

    mo.plain_text(captured_12.getvalue())
    return




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
def _(mo, rankResult, vectorRank):
    rankResult.equation = vectorRank.arr_rank(-1)
    with mo.capture_stdout() as captured_13:
        print(rankResult(1))

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
    matrixMean = model.converter('matrixMean')
    matrixMean.setup_named_matrix({'value1': {'value11': 2.0, 'value12': 4.0}, 'value2': {'value21': 6.0, 'value22': 8.0}, 'value3': {'value31': 10.0, 'value32': 12.0}})
    meanResult = model.converter('meanResult')
    meanResult.equation = matrixMean.arr_mean()
    return (meanResult,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \text{mean}
    \begin{pmatrix}
    2.0 & 4.0\\
    6.0 & 8.0\\
    10.0 & 12.0
    \end{pmatrix}
    =
    \frac{2.0 + 4.0 + 6.0 + 8.0 + 10.0 +12.0}{6} = 7.0
    \end{equation*}
    """)
    return


@app.cell
def _(matrixMean, meanResult, mo):
    meanResult.equation = matrixMean.arr_mean()
    with mo.capture_stdout() as captured_14:
        print(meanResult(1))

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
    vectorMedian1 = model.converter('vectorMedian1')
    vectorMedian1.setup_vector(5, [-2.0, -0.1, 3.1, 5.2, 11.1])
    vectorMedian2 = model.converter('vectorMedian2')
    vectorMedian2.setup_vector(4, [-2.0, -0.1, 3.1, 5.2])
    medianResult = model.converter('medianResult')
    medianResult.equation = vectorMedian1.arr_median()
    return medianResult, vectorMedian2


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
def _(medianResult, mo, vectorMedian1):
    medianResult.equation = vectorMedian1.arr_median()
    with mo.capture_stdout() as captured_15:
        print(medianResult(1))

    mo.plain_text(captured_15.getvalue())
    return




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
def _(medianResult, mo, vectorMedian2):
    medianResult.equation = vectorMedian2.arr_median()
    with mo.capture_stdout() as captured_16:
        print(medianResult(1))

    mo.plain_text(captured_16.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Array Standdarddeviation
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
    matrixStddev = model.converter('matrixStddev')
    matrixStddev.setup_matrix([2, 2], [[1.0, 3.0], [3.0, 1.0]])
    stddevResult = model.converter('stddevResult')
    stddevResult.equation = matrixStddev.arr_stddev()
    return (stddevResult,)


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
def _(matrixStddev, mo, stddevResult):
    stddevResult.equation = matrixStddev.arr_stddev()
    with mo.capture_stdout() as captured_17:
        print(stddevResult(1))

    mo.plain_text(captured_17.getvalue())
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
    vectorSize = model.converter('vectorSize')
    vectorSize.setup_vector(6, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    matrixSize1 = model.converter('matrixSize2')
    #Calculate the size of a not-named matrix
    matrixSize1.setup_matrix([2, 3], [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]])
    matrixSize2 = model.converter('matrixSize3')
    matrixSize2.setup_matrix([4, 3], [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]])
    sizeResult = model.converter('sizeResult')
    sizeResult.equation = vectorSize.arr_size()
    return matrixSize1, matrixSize2, sizeResult


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
def _(mo, sizeResult, vectorSize):
    sizeResult.equation = vectorSize.arr_size()
    with mo.capture_stdout() as captured_18:
        print(sizeResult(1))

    mo.plain_text(captured_18.getvalue())
    return




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
def _(matrixSize1, mo, sizeResult):
    sizeResult.equation = matrixSize1.arr_size()
    with mo.capture_stdout() as captured_19:
        print(sizeResult(1))

    mo.plain_text(captured_19.getvalue())
    return




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
def _(matrixSize2, mo, sizeResult):
    sizeResult.equation = matrixSize2.arr_size()
    with mo.capture_stdout() as captured_20:
        print(sizeResult(1))

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

    ⚠️ **The Dot function is currently supported for not-named arrays only!**

    Lets have a look at some examples:
    """)
    return


@app.cell
def _(model):
    #Calculate vector * constant & constant * vector
    constant = model.converter('constant')
    constant.equation = 2.0
    vectorDot1 = model.converter('vectorDot1')
    vectorDot1.setup_vector(3, [1.0, 2.0, 3.0])
    vectorDot2 = model.converter('vectorDot2')
    vectorDot2.setup_vector(3, [4.0, 5.0, 6.0])
    dotResult1 = model.converter('dotResult1')
    dotResult1.equation = vectorDot1.dot(constant)
    return constant, dotResult1, vectorDot1, vectorDot2


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    2.0 \cdot \begin{pmatrix} 1.0 \\ 2.0 \\ 3.0 \end{pmatrix}
    =
    \begin{pmatrix} 2.0 \\ 4.0 \\ 6.0 \end{pmatrix}\end{equation*}
    """)
    return


@app.cell
def _(constant, dotResult1, mo, vectorDot1):
    dotResult1.equation = vectorDot1.dot(constant)
    with mo.capture_stdout() as captured_21:
        print("[" + str(dotResult1[0](1)) + " , " + str(dotResult1[1](1)) + " , " + str(dotResult1[2](1)) + "]")

    mo.plain_text(captured_21.getvalue())
    return




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix} 4.0 \\ 5.0 \\ 6.0 \end{pmatrix} \cdot 2.0
    =
    \begin{pmatrix} 8.0 \\ 10.0 \\ 12.0 \end{pmatrix}\end{equation*}
    """)
    return


@app.cell
def _(constant, dotResult1, mo, vectorDot2):
    dotResult1.equation = constant.dot(vectorDot2)
    with mo.capture_stdout() as captured_22:
        print("[" + str(dotResult1[0](1)) + " , " + str(dotResult1[1](1)) + " , " + str(dotResult1[2](1)) + "]")

    mo.plain_text(captured_22.getvalue())
    return


@app.cell
def _(model):
    #Calculate matrix * constant & constant * matrix
    constant_1 = model.converter('constant')
    constant_1.equation = 2.0
    matrixDot1 = model.converter('matrixDot1')
    matrixDot1.setup_matrix([3, 2], [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    matrixDot2 = model.converter('matrixDot2')
    matrixDot2.setup_matrix([2, 3], [[-1.0, -2.0, -3.0], [-4.0, -5.0, -6.0]])
    dotResult2 = model.converter('dotResult2')
    dotResult2.equation = matrixDot1.dot(constant_1)
    return constant_1, dotResult2, matrixDot1, matrixDot2


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
def _(constant_1, dotResult2, matrixDot1, mo):
    dotResult2.equation = matrixDot1.dot(constant_1)
    with mo.capture_stdout() as captured_23:
        print("[ " + "[" + str(dotResult2[0][0](1)) + " , " + str(dotResult2[0][1](1)) + "]")
        print("  " + "[" + str(dotResult2[1][0](1)) + " , " + str(dotResult2[1][1](1)) + "]")
        print("  " + "[" + str(dotResult2[2][0](1)) + " , " + str(dotResult2[2][1](1)) + "]" + " ]")

    mo.plain_text(captured_23.getvalue())
    return




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    2.0 \cdot
    \begin{pmatrix}
    -1.0 & -2.0 & -3.0 \\
    -4.0 & -5.0 & -6.0 \\
    \end{pmatrix}
    =
    \begin{pmatrix}
    -2.0 & -4.0 & -6.0 \\
    -8.0 & -10.0 & -12.0 \\
    \end{pmatrix}\end{equation*}
    """)
    return


@app.cell
def _(constant_1, dotResult2, matrixDot2, mo):
    dotResult2.equation = constant_1.dot(matrixDot2)
    with mo.capture_stdout() as captured_24:
        print("[ " + "["    + str(dotResult2[0][0](1)) + " , " + str(dotResult2[0][1](1)) + " , " 
                            + str(dotResult2[0][2](1)) + "]")
        print("  " + "["    + str(dotResult2[1][0](1)) + " , " + str(dotResult2[1][1](1)) + " , " 
                            + str(dotResult2[1][2](1)) + "]" + " ]")

    mo.plain_text(captured_24.getvalue())
    return


@app.cell
def _(model, vectorDot1, vectorDot2):
    #Calculate vector * vector
    dotResult3 = model.converter('dotResult3')
    dotResult3.equation = vectorDot1.dot(vectorDot2)
    return (dotResult3,)


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
def _(dotResult3, mo, vectorDot1, vectorDot2):
    dotResult3.equation = vectorDot1.dot(vectorDot2)
    with mo.capture_stdout() as captured_25:
        print(dotResult3(1)) #1*4 + 2*5 + 3*6 = 32

    mo.plain_text(captured_25.getvalue())
    return


@app.cell
def _(matrixDot1, model, vectorDot1):
    #Calculate vector * matrix & matrix * vector
    dotResult4 = model.converter('dotResult4')
    dotResult4.equation = vectorDot1.dot(matrixDot1)
    return (dotResult4,)


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
def _(dotResult4, matrixDot1, mo, vectorDot1):
    dotResult4.equation = vectorDot1.dot(matrixDot1)
    with mo.capture_stdout() as captured_26:
        print("[" + str(dotResult4[0](1)) + " , " + str(dotResult4[1](1))  + "]")

    mo.plain_text(captured_26.getvalue())
    return




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{pmatrix}
    -1.0 & -2.0 & -3.0 \\
    -4.0 & -5.0 & -6.0 \\
    \end{pmatrix}
    \cdot
    \begin{pmatrix}
    4.0 \\
    5.0 \\
    6.0 \\
    \end{pmatrix}
    =
    \begin{pmatrix}
    -1.0 \cdot 4.0 + (-2.0) \cdot 5.0 + (-3.0) \cdot 6.0 \\
    -4.0 \cdot 4.0 + (-5.0) \cdot 5.0 + (-6.0) \cdot 6.0 \\
    \end{pmatrix}
    =
    \begin{pmatrix}
    -32.0 \\
    -77.0
    \end{pmatrix}
    \end{equation*}
    """)
    return


@app.cell
def _(dotResult4, matrixDot2, mo, vectorDot2):
    dotResult4.equation = matrixDot2.dot(vectorDot2)
    with mo.capture_stdout() as captured_27:
        print("[" + str(dotResult4[0](1)) + " , " + str(dotResult4[1](1)) + "]")

    mo.plain_text(captured_27.getvalue())
    return


@app.cell
def _(model):
    #Calculate matrix * matrix
    matrixDot3 = model.converter('matrixDot3')
    matrixDot3.setup_matrix([2, 2], [[1.0, 2.0], [3.0, 4.0]])
    matrixDot4 = model.converter('matrixDot4')
    matrixDot4.setup_matrix([2, 2], [[-1.0, -2.0], [-4.0, -5.0]])
    dotResult5 = model.converter('dotResult5')
    dotResult5.equation = matrixDot3.dot(matrixDot4)
    return (dotResult5,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    \begin{aligned}
    \begin{pmatrix}
    1.0 & 2.0 \\
    3.0 & 4.0 \\
    \end{pmatrix}
    \cdot
    \begin{pmatrix}
    -1.0 & -2.0 \\
    -4.0 & -5.0 \\
    \end{pmatrix}
    &=
    \begin{pmatrix}
    1.0 \cdot (-1.0) + 2.0 \cdot (-4.0) & 1.0 \cdot (-2.0) + 2.0 \cdot (-5.0) \\
    3.0 \cdot (-1.0) + 4.0 \cdot (-4.0) & 3.0 \cdot (-2.0) + 4.0 \cdot (-5.0) \\
    5.0 \cdot (-1.0) + 6.0 \cdot (-4.0) & 5.0 \cdot (-2.0) + 6.0 \cdot (-5.0) \\
    \end{pmatrix}\\
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
def _(dotResult5, matrixDot3, matrixDot4, mo):
    dotResult5.equation = matrixDot3.dot(matrixDot4)
    with mo.capture_stdout() as captured_28:
        print("[ " + "["    + str(dotResult5[0][0](1)) + " , " + str(dotResult5[0][1](1)) + "]")
        print("  " + "["    + str(dotResult5[1][0](1)) + " , " + str(dotResult5[1][1](1)) + "]" + " ]")

    mo.plain_text(captured_28.getvalue())
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
    vector3 = model.converter('vector3')
    vector3.setup_named_vector({'value1': 6.0, 'value2': 7.0})
    vector3.plot(format="axes")
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
    matrix3 = model.converter('matrix3')
    matrix3.setup_named_matrix({'value1': {'value11': 6.0, 'value12': 7.0}, 'value2': {'value21': 8.0, 'value22': 9.0}})
    matrix3['value1'].plot(format="axes")
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
def _(model, testbptk):
    testbptk.register_model(model)
    scenario_manager = {'sm': {'model': model, 'base_constants': {'interestRate[bank]': 0.02, 'interestRate[depot]': 0.1, 'depositRate[bank]': 200, 'depositRate[depot]': 100, 'accountInitialValues[bank]': 1000.0, 'accountInitialValues[depot]': 500.0}}}
    testbptk.register_scenario_manager(scenario_manager)
    testbptk.register_scenarios(scenario_manager='sm', scenarios={'base': {}, 'scenarioHighDepotInterestRate': {'constants': {'interestRate[depot]': 0.2}}, 'scenarioHighDepotDepositRate': {'constants': {'depositRate[depot]': 250.0}}, 'scenarioHighDepotInitialValue': {'constants': {'accountInitialValues[depot]': 750.0}}})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And plot the results:
    """)
    return


@app.cell
def _(testbptk):
    testbptk.plot_scenarios(scenarios=['base'], scenario_managers='sm', equations=['account[bank]', 'account[depot]', 'totalValue'], series_names={}, format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As always we can compare different scenarios with each other by plotting them simultaneously:
    """)
    return


@app.cell
def _(testbptk):
    testbptk.plot_scenarios(scenarios=['base', 'scenarioHighDepotInterestRate', 'scenarioHighDepotDepositRate', 'scenarioHighDepotInitialValue'], scenario_managers='sm', equations=['totalValue'], series_names={}, format="axes")
    return


if __name__ == "__main__":
    app.run()
