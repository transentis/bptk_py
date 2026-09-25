# Front matter the .py format cannot carry; injected on export.
# description: BPTK API Documentation for the Module class
# keywords: system dynamics, bptk, bptk-py, python, business prototyping
#
# Reference documentation, and the rest of the API section is grey code throughout, so
# this page is too: the eleven cells are a worked example to read, not a model to run,
# and the two charts are worth more as pictures than as an 8 MB Pyodide download
#. The one page of this section that invites editing is the playground of
# `make_your_psf_grow`.
# interactive: false
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Module")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Module

    ## Module Constructor

    **Module(model, name, parent=None)**

    The Module class is used to structure SD DSL models into individual modules.

    Modules can be nested.

    If you create model elements such as stocks, flows and
    converters via the module, the elments are added to the model, but the element
    names are turned into fully qualified names of the form
    parent_module_name.module_name.name.

    The fully qualfied name is used as the equation
    name in the Model class and is needed when making calls to bptk.run_scenario or
    bptk.plot_scenario.

    Check the [Beergame](/model_library/beergame/beergame_sd_dsl.ipynb) or [Enterprise Digital Twin](/model_library/enterprise_digital_twin/enterprise_digital_twin.ipynb) models to see the module class in action.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Module.biflow

    **biflow(name)**

    Add a [Biflow](./api_biflow.md) to the underlying model. The name of the biflow will be a fully qualified name
    consisting of all nested module names plus the actual element name using dot
    notation, i.e. namespace.name
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Module.constant

    **constant(name)**

    Add a [Constant](./api_constant.md) to the model. The name of the constant will be a fully qualified name
    consisting of all nested module names plus the actual element name using dot
    notation, i.e. namespace.name
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Module.converter

    **converter(name)**

    Add a [Converter](./api_converter.md) to the model. The name of the converter will be a fully qualified name
    consisting of all nested module names plus the actual element name using dot
    notation, i.e. namespace.name
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Module.flow

    **flow(name)**

    Add a [Flow](./api_flow.md) to the model. The name of the flow will be a fully qualified name
    consisting of all nested module names plus the actual element name using dot
    notation, i.e. namespace.name
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Module.fqn

    **fqn(name)**

    Given a name this returns the fully qualified name, i.e. name prefixed
    by the module namespace.

    The namespace is defined by the names of all parent modules, e.g. parent_module_name.module_name

    * **Parameters**

        **name** – String
        The name that is to be converted into a fully qualified name.

    * **Return**

        Return the fully qualified name, i.e. namespace.name
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Module.initialize

    **initialize(module,...)**

    Override this method in concrete Module subclasses and use it to define the model using Stocks, Flows, Converters and Constants.

    Pass in any module dependencies as parameters.

    * **Parameters**

        **module** – Module subclass
        External module that contains model elements that are needed within the current module
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Module.stock

    **stock(name)**

    Add a [Stock](./api_stock.md) to the model. The name of the stock will be a fully qualified name consisting of all nested module names plus the actual element name using dot
    notation, i.e. namespace.name
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Usage

    Let's create a simple example model containing to modules _A_ and _B_ that depend on each other.
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model, Module

    return Model, Module


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Set up a model that runs over 10 timesteps:
    """)
    return


@app.cell
def _(Model):
    model = Model(starttime=1,stoptime=10,dt=1,name='model')
    return (model,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now create to module classes that define the actual model:
    """)
    return


@app.cell
def _(Module):
    class A(Module):

        def initialize(self,b):
            ## stocks

            stock = self.stock("stock")

            ## flows.

            flow = self.flow("flow")

            ## equations

            stock.initial_value = 0.0
            stock.equation = flow
        
            flow.equation = b.stock("stock")

    return (A,)


@app.cell
def _(Module):
    class B(Module):

        def initialize(self,a):

            ## stocks
            stock = self.stock("stock")

            ## flows.
            flow = self.flow("flow")

            ## equations
            stock.initial_value = 1.0
            stock.equation = flow
    
            flow.equation = a.stock("stock")

    return (B,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Initialize the modules:
    """)
    return


@app.cell
def _(A, B, model):
    a = A(model,"a")
    b = B(model,"b")

    a.initialize(b)
    b.initialize(a)
    return (a,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Plot the graph for the *a_module.a_stock* element:
    """)
    return


@app.cell
def _(model):
    model.stock("a.stock").plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Of course you can also access the model element directly via their respective modules:
    """)
    return


@app.cell
def _(a):
    a.stock("stock").plot(format="axes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In practice you will probably set up and scenario managers and then access the model elements via the [bptk](./api_bptk.md) class.
    """)
    return


@app.cell
def _():
    from BPTK_Py import bptk
    bptk = bptk()
    return (bptk,)


@app.cell
def _(bptk, model):
    bptk.register_scenario_manager(
        {
         "sm":
        {
            "model":model,
            "scenarios":
            {
                "base":{}    
            }
    
         }

        }
        )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["sm"],
        scenarios=["base"],
        equations=["a.stock","b.stock"], format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    During model development, it can be useful to list all model equations:
    """)
    return


@app.cell
def _(bptk, mo):
    # `list_equations` prints and returns nothing, and marimo sends a cell's stdout to
    # the console rather than into the page - so it has to be captured to be seen.
    with mo.capture_stdout() as equations:
        bptk.list_equations()

    mo.plain_text(equations.getvalue())
    return


if __name__ == "__main__":
    app.run()
