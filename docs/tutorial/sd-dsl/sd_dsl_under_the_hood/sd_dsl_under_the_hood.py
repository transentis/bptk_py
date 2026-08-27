# Front matter the .py format cannot carry; injected on export.
# description: Introduction to the python library for system dynamics, that is part of the BPTK-Py business simulation framework.
# keywords: system dynamics, systemdynamics, sd dsl, bptk, bptk-py, python, metaprogramming, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="SD DSL - Under The Hood")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # SD DSL: Under The Hood
    **Creating A Domain Specific Language For System Dynamics Simulations**
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Part of the BPTK Framework is the *System Dynamics Domain Specific Language (SD DSL)*. Using the SD DSL, you can easily build System Dynamics Mmodels directly in Python using an intuitive Syntax.

    This notebook takes a look under the hood of the SD DSL and explains how it creates the underlying equations that are needed to run a simulation.

    This should give you a better understanding of System Dynamics, of the SD DSL and of Python metaprogramming techniques.

    The following diagram contains the three key System Dynamics language elements:

    * Stocks
    * Flows
    * Converters

    ![Simple System Dynamics Model](sfd_simple_model.svg)

    At any given time $t$, a stock is equal to the value of the stock at time $t-1$ plus the sum of all inflows, minus the sum of all outflow at time $t-1$ are simply the sum of the flows that flow into and out of them, over time.

    Flows and converters are simply functions of their inputs.

    The general mathematical equations for the stocks above are:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    stock(t)=stock(t-1)+\sum_{inflows}inflow(t-1)-\sum_{outflows}outflow(t-1)
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    flow(t) = function(input_1,...,input_n)
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    converter(t) = function(input_1,...,input_n)
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The concrete equations for the model in the diagram above are:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    stock(t)=stock(t-1)+\sum_{inflows}inflow(t-1)
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    flow(t) = stock(t)*rate(t)
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    rate(t) = 0.1
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    \begin{equation*}
    stock(0) = 1
    \end{equation*}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The SD DSL allows us to write SD models in Python using a simple syntax:

    ```python
    stock = model.stock("stock")
    flow = model.flow("flow")
    rate = model.converter("rate")
    stock.initial_value = 1
    rate.equation=0.1
    flow.equation=stock*rate
    stock.equation=flow
    ```

    But under the hood, the SD DSL needs to build the equations listed above to ensure that we can simulate the model.

    Let's take a look at how this is done, step by step.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Write Python Code For The Equations Above
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The SD DSL uses lambda functions lambda functions to implement the equation if the System Dynamics model.
    """)
    return


@app.cell
def _():
    import pandas as pd
    import matplotlib
    # One cell rather than three: the three equations refer to each other, and
    # marimo refuses a cycle between cells. Jupyter got away with it
    # because every cell shared one namespace and ran top to bottom.
    stock = lambda t: stock(t-1) + flow(t-1) if t>0 else 1
    flow = lambda t: stock(t) * rate(t)
    rate = lambda t: 0.1
    stock(10)
    return pd, stock


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Plot The Resulting Equation
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Plot the stock equation for 20 timesteps, e.g. using a pandas dataframe.
    """)
    return


@app.cell
def _(pd, stock):
    df = pd.DataFrame((stock(t)) for t in range(0,20) )
    df.plot(kind="line")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: Keep Equations in A Dictionary
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Assume we want to keep equations in a "model" and add new ones dynamically:  create a dictioanry of equations that are accessed by equation names as strings, e.g. `equation["stock"](5)`
    """)
    return


@app.cell
def _():
    equations={}
    equations["stock"] = lambda t: equations["stock"](t-1) + equations["flow"](t-1) if t>0 else 1
    equations["flow"] = lambda t: equations["stock"](t) * equations["rate"](t)
    equations["rate"] = lambda t: 0.1
    equations["stock"](10)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Use Memoization To Improve Performance
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In order to calculate the value of a stock at a given time $t$, you need to know all preceding values. The way the model is encoded at the moment, this means that we first calculate the value at time $t = 1$, then to calculate the value at time $t = 2$ we need to calcualte the values at time $t=1$ and then at time $t =2$ and so on ... this means that even models with only few timesteps can take a very long time to evaluate.

    The way around this of course is to remember the value of each equation at each time step, so that you don't have to recurse through all timesteps at every timestep.

    We do this using a technique called _memoization_.
    """)
    return


@app.cell
def _(equations, mo):
    # marimo has no `%timeit`, so the measurement is written out. Every extra
    # timestep doubles the work: the stock recurses into itself and into the
    # flow, and the flow recurses back into the stock.
    import time

    def elapsed(call):
        started = time.perf_counter()
        call()
        return (time.perf_counter() - started) * 1000

    mo.md(
        "\n".join(
            ["| t | time to evaluate `stock(t)` |", "|---|---|"]
            + [
                f"| {t} | {elapsed(lambda: equations['stock'](t)):.1f} ms |"
                for t in (10, 15, 20)
            ]
        )
    )
    return (elapsed,)


@app.cell
def _():
    equations_1 = {}
    memo={}
    return equations_1, memo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The memoization function stores the value of each equation at each timestep. When asking for the value of an equation at a given time, it first checks if the value has already been calculated. If yes, it returns that value. If no, it calculates the value, stores it and then returns it.
    """)
    return


@app.cell
def _(equations_1, memo):
    def memoize(equation, time):
        try:
            mymemo = memo[equation]
        except:
            memo[equation] = {}
            mymemo = memo[equation]  # In case the equation does not exist in memo
        if time in mymemo.keys():
            return mymemo[time]
        else:
            result = equations_1[equation](time)
            mymemo[time] = result
        return result
    equations_1['stock'] = lambda t: memoize('stock', t - 1) + memoize('flow', t - 1) if t > 0 else 1
    equations_1['flow'] = lambda t: memoize('stock', t) * memoize('rate', t)
    equations_1['rate'] = lambda t: 0.1
    equations_1['stock'](5)
    return


@app.cell
def _(elapsed, equations_1, memo, mo):
    # The same measurement against the memoized version. The memo is cleared
    # before each row, so every number is an honest from-scratch run - and they
    # grow with t instead of doubling with it.
    def from_scratch(t):
        memo.clear()
        return elapsed(lambda: equations_1["stock"](t))

    mo.md(
        "\n".join(
            ["| t | time to evaluate `stock(t)`, memoized |", "|---|---|"]
            + [f"| {t} | {from_scratch(t):.1f} ms |" for t in (20, 50, 100)]
        )
    )
    return


@app.cell
def _(equations_1):
    equations_1['stock'](50)
    return


@app.cell
def _(equations_1, pd):
    df_1 = pd.DataFrame((equations_1['stock'](t) for t in range(0, 50)))
    df_1.plot(kind='line')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5: Compile Equations From Strings
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now that we know what equations we want, we need a find a way of generating them directly. We do this by first generating the code in string form and then compiling that string into code using the `eval`function.
    """)
    return


@app.cell
def _(equations_1):
    equations_1['stock'] = eval("lambda t: memoize('stock',t-1) + memoize('flow',t-1) if t>0 else 1")
    equations_1['stock'](5)
    return


@app.cell
def _(equations_1):
    equations_1['stock']
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 6: Encapsulate The Basic Functionality In Classes
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now that we have all the building blocks for our SD DSL, we would like to encapsulate them in classes that allow us to build a model at runtime.

    We want to be able to build a model using objects at runtime, the underlying equations should be generated for us.

    * Create classes for the model (that will hold the model elements and equations) and for the elements themselves.
    * New elements are created using the model as a factory (e.g. `another_stock = model.stock("name of another stock")`)
    * Elements know which model they belong to
    * The equations for each element are defined using an equation method on the elements (e.g. `stock.equation=flow`)
    * The memoization function should be part of the model class
    * Each element should have a term function `element.term` that generate a string representation of itself (e.g `model.memoize("stock",t)`)
    * Remember that stocks have an initial value
    """)
    return


@app.cell
def _():
    class Model:
        def __init__(self):
            self._stocks = {}
            self._flows = {}
            self._converters = {}
            self._memo={}
        
        def stock(self, name):
            if name not in self._stocks:
                self._stocks[name] = Stock(self, name)
            return self._stocks[name]
    
        def flow(self, name):
            if name not in self._flows:
                self._flows[name] = Flow(self, name)
            return self._flows[name]
    
        def converter(self, name):
            if name not in self._converters:
                self._converters[name] = Converter(self, name)
            return self._converters[name]
    
        def memoize(self,equation, arg):
        
            try:
                mymemo = self._memo[equation]
            except:
                # In case the equation does not exist in memo
                self._memo[equation] = {}
                mymemo = self._memo[equation]
            if arg in mymemo.keys():
                return mymemo[arg]
            else:
                result = self._equations[equation](arg)
                mymemo[arg] = result

            return result
    class Element:
        def __init__(self, model, name):
            self._model = model
            self._name = name
            self._equation = None
    
        @property
        def equation(self):
            return self._equation
    
        @equation.setter
        def equation(self, equation):
            self._equation = equation
        
        def term(self,time="t"):
            return "model.memoize('{}',{})".format(self._name, time)

    class Stock(Element):
    
        def __init__(self,model, name):
            super().__init__(model, name)
            self._initial_value = 0
        
        @property
        def initial_value(self):
            return self._initial_value
    
        @initial_value.setter
        def initial_value(self, value):
            self._initial_value=value

    
    class Flow(Element): 
        pass
    
    class Converter(Element):
        pass
    model = Model()
    stock_1 = model.stock('stock')
    stock_1.term()
    return model, stock_1


@app.cell
def _(model, stock_1):
    stock_1.initial_value = 1
    rate_1 = model.converter('rate')
    rate_1.term()
    return (rate_1,)


@app.cell
def _(model):
    flow_1 = model.flow('flow')
    flow_1.term()
    return (flow_1,)


@app.cell
def _(flow_1, stock_1):
    stock_1.equation = flow_1
    stock_1._equation
    return


@app.cell
def _(rate_1):
    rate_1.equation = 10
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 7: Auto-Generate The Equations
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Extend the framework to auto-generate the underlying lambda-equations and add them to the model. For the first version assume we just have a stock and a constant flow.

    Override the call operator to evalue the element at a particular timestep (e.g. `stock(10)`)

    Create a plot function that evaluates an element in the range 0 to 100.
    """)
    return


@app.cell
def _(pd):
    class Model_1:

        def __init__(self):
            self._stocks = {}
            self._flows = {}
            self._converters = {}
            self._memo = {}
            self._equations = {}

        def stock(self, name):
            if name not in self._stocks:
                self._stocks[name] = Stock_1(self, name)
            return self._stocks[name]

        def flow(self, name):
            if name not in self._flows:
                self._flows[name] = Flow_1(self, name)
            return self._flows[name]

        def converter(self, name):
            if name not in self._converters:
                self._converters[name] = Converter_1(self, name)
            return self._converters[name]

        def memoize(self, equation, arg):
            try:
                mymemo = self._memo[equation]
            except:
                self._memo[equation] = {}  # In case the equation does not exist in memo
                mymemo = self._memo[equation]
            if arg in mymemo.keys():
                return mymemo[arg]
            else:
                result = self._equations[equation](arg)
                mymemo[arg] = result
            return result
    class Element_1:

        def __init__(self, model, name):
            self._model = model
            self._name = name
            self._equation = None
            self._function_string = ''

        @property
        def equation(self):
            return self._equation

        @equation.setter
        def equation(self, equation):
            self._equation = equation
            self._function_string = 'lambda model, t: {}'.format(equation)
            self.generate_function()

        def generate_function(self):
            """
            Generate the function using the function_string value and eval()
            :return: None
            """
            fn = eval(self._function_string)
            self._model._equations[self._name] = lambda t: fn(self._model, t)
            self._model._memo[self._name] = {}

        def term(self, time='t'):
            return "model.memoize('{}',{})".format(self._name, time)

        def plot(self):
            df = pd.DataFrame((self(t) for t in range(0, 100)))
            return df.plot(kind='line')

        def __call__(self, *args, **kwargs):
            return self._model._equations[self._name](args[0])

        def __str__(self):
            return self.term()
    class Stock_1(Element_1):
        type = 'Stock'

        def __init__(self, model, name):
            super().__init__(model, name)
            self._initial_value = 0

        @property
        def initial_value(self):
            return self._initial_value

        @initial_value.setter
        def initial_value(self, value):
            self._initial_value = value

        @property
        def equation(self):
            return self._equation

        @equation.setter
        def equation(self, equation):
            self._equation = equation
            self._function_string = 'lambda model, t : ( ('
            self._function_string = self._function_string + str(self._initial_value)
            self._function_string = self._function_string + ") if (t <= 0) else (model.memoize('{}',t-1)) ".format(self._name)
            if self._equation is not None:
                self._function_string = self._function_string + '+ ('
                self._function_string = self._function_string + self._equation.term('t-1')
                self._function_string = self._function_string + ') )'
            else:
                self._function_string = self._function_string + ')'
            self.generate_function()

    class Flow_1(Element_1):
        type = 'Flow'

    class Converter_1(Element_1):
        type = 'Converter'
    model_1 = Model_1()
    stock_2 = model_1.stock('stock')
    stock_2.term()
    return model_1, stock_2


@app.cell
def _(model_1, stock_2):
    stock_2.initial_value = 1
    flow_2 = model_1.flow('flow')
    flow_2.term()
    return (flow_2,)


@app.cell
def _(flow_2, stock_2):
    flow_2.equation = 1
    stock_2.equation = flow_2
    stock_2._equation
    return


@app.cell
def _(model_1):
    model_1._equations
    return


@app.cell
def _(flow_2):
    flow_2(10)
    return


@app.cell
def _(stock_2):
    stock_2(10)
    return


@app.cell
def _(stock_2):
    stock_2.plot()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 8: Extend the Equation Syntax Using Operators

    In order to re-create our initial model, we need to formulate an equation such as `flow.equation = stock*rate`.

    Override the `__mul__` methods of the Element and create a multiplication operator to deal with this.
    """)
    return


@app.cell
def _(pd):
    class Model_2:

        def __init__(self):
            self._stocks = {}
            self._flows = {}
            self._converters = {}
            self._memo = {}
            self._equations = {}

        def stock(self, name):
            if name not in self._stocks:
                self._stocks[name] = Stock_2(self, name)
            return self._stocks[name]

        def flow(self, name):
            if name not in self._flows:
                self._flows[name] = Flow_2(self, name)
            return self._flows[name]

        def converter(self, name):
            if name not in self._converters:
                self._converters[name] = Converter_2(self, name)
            return self._converters[name]

        def memoize(self, equation, arg):
            try:
                mymemo = self._memo[equation]
            except:
                self._memo[equation] = {}  # In case the equation does not exist in memo
                mymemo = self._memo[equation]
            if arg in mymemo.keys():
                return mymemo[arg]
            else:
                result = self._equations[equation](arg)
                mymemo[arg] = result
            return result
    class MultiplicationOperator():

        def __init__(self, element_1, element_2):
            self._element_1 = element_1
            self._element_2 = element_2
        
        def term(self, time="t"):
            return "(" + self._element_1.term(time) + ") * (" + self._element_2.term(time) + ")"
    
        def __str__(self):
            return self.term()

    class Element_2:

        def __init__(self, model, name):
            self._model = model
            self._name = name
            self._equation = None
            self._function_string = ''

        @property
        def equation(self):
            return self._equation

        @equation.setter
        def equation(self, equation):
            self._equation = equation
            self._function_string = 'lambda model, t: {}'.format(equation)
            self.generate_function()

        def generate_function(self):
            """
            Generate the function using the function_string value and eval()
            :return: None
            """
            fn = eval(self._function_string)
            self._model._equations[self._name] = lambda t: fn(self._model, t)
            self._model._memo[self._name] = {}

        def term(self, time='t'):
            return "model.memoize('{}',{})".format(self._name, time)

        def plot(self):
            df = pd.DataFrame((self(t) for t in range(0, 100)))
            return df.plot(kind='line')

        def __call__(self, *args, **kwargs):
            return self._model._equations[self._name](args[0])

        def __mul__(self, other):
            return MultiplicationOperator(self, other)

        def __str__(self):
            return self.term()
    class Stock_2(Element_2):
        type = 'Stock'

        def __init__(self, model, name):
            super().__init__(model, name)
            self._initial_value = 0

        @property
        def initial_value(self):
            return self._initial_value

        @initial_value.setter
        def initial_value(self, value):
            self._initial_value = value

        @property
        def equation(self):
            return self._equation

        @equation.setter
        def equation(self, equation):
            self._equation = equation
            self._function_string = 'lambda model, t : ( ('
            self._function_string = self._function_string + str(self._initial_value)
            self._function_string = self._function_string + ") if (t <= 0) else (model.memoize('{}',t-1)) ".format(self._name)
            if self._equation is not None:
                self._function_string = self._function_string + '+ ('
                self._function_string = self._function_string + self._equation.term('t-1')
                self._function_string = self._function_string + ') )'
            else:
                self._function_string = self._function_string + ')'
            self.generate_function()

    class Flow_2(Element_2):
        type = 'Flow'

    class Converter_2(Element_2):
        type = 'Converter'
    model_2 = Model_2()
    stock_3 = model_2.stock('stock')
    flow_3 = model_2.flow('flow')
    rate_2 = model_2.converter('rate')
    rate_2.equation = 0.1
    stock_3.initial_value = 1
    stock_3.equation = flow_3
    flow_3.equation = stock_3 * rate_2
    stock_3(3)
    return (stock_3,)


@app.cell
def _(stock_3):
    stock_3.plot()
    return


if __name__ == "__main__":
    app.run()
