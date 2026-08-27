# Front matter the .py format cannot carry; injected on export.
# description: How to use Python and notebooks to rapidly build interactive stories based on System Dynamics simulations.
# keywords: system dynamics, systemdynamics, xmile, bptk, bptk-py, python, business simulation, stella
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Writing Computational Essays")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Writing Computational Essays Based On Simulation Models

    ### How to use Python and notebooks to rapidly build interactive stories based on System Dynamics simulations

    *If you want to use the insights gained from simulation models to transform your enterprise, just having the model and the insights alone are often not enough – you need to develop a good story that persuades your stakeholders to make decisions and take action.*

    *Our BPTK_PY library allows you to convert System Dynamics models into Python code and run them in a notebook, which is a wonderful place for writing interactive, data-driven papers and reports.*

    Many years ago we published a blog post titled _Telling Stories with System Dynamics Models_ which introduced our approach to telling interactive stories based on simulation models built using System Dynamics.

    Writing such interactive stories is quite challenging, even if your simulation model is already fairly complete, because you need to craft the storyline while testing different scenarios with the simulation model.

    We realised early on that what we needed a "interactive writing environment" that would help us to prototype a complex story line while still building the model:

    * Build an initial simulation model using a visual modeling tool.
    * Start writing a story around the model using the interactive writing environment.
    * Use the new questions and insights that arise during the writing process to drive experiments with the simulation model – this may lead to changes in both the model and the storyline.

    In 2014 we started writing such "computational essays" using [Wolfram Research'](http://www.wolfram.com) Mathematica®.

    Mathematica is a wonderful and very powerful tool to support this process – it is a complete environment that supports writing, computation, presentation and very sophisticated interactive dashboards.

    Mathematica does not contain native support for System Dynamics, but we crafted a small library that allows us to import System Dynamics models based on the XMILE standard and to run them in Mathematica.

    But since 2014 a lot has happened in the world of computational modelling ... Python has become the premiere programming language for data science and its use has thus become even more ubiquitous, and with it the notebook as a working environment - first [Jupyter](http://www.jupyter.org), and more recently [marimo](https://marimo.io), which is what this documentation is written in.

    Both Mathematica and Python notebooks are fantastic environments for creating computational essays and "story-driven simulations":

    * Working with Mathematica and the Wolfram Language is incredibly productive thanks to the symbolic nature of the language and the way it integrates into the highly sophisticated Mathematica notebook environment.
    * Python notebooks still lack the sophistication of Mathematica notebooks. But what sets the Python ecosystem apart is that it is open source (and thus free to use for everyone), highly extensible and very widely used in the data science/computational modeling community - it is thus much easier to find books, training materials and skilled resources.

    >For a more in-depth comparison of Jupyter and Mathematica see Paul Romer's very interesting [blog post](https://paulromer.net/jupyter-mathematica-and-the-future-of-the-research-paper/) on this topic. Also be sure to read the [Atlantic Article](https://www.theatlantic.com/science/archive/2018/04/the-scientific-paper-is-obsolete/556676/) referenced by Paul Romer.

    Because Python and its notebooks are free to use, we decided to port our Business Prototyping Toolkit to Python and also provide it free of charge - which means you can now create simulation models using System Dynamics and let them run in Python.

    Our approach is very powerful and liberating, because it turns our models into computable objects – we can now use our simulation models in new ways, quite independently of the modeling environment in which we create the model.

    Some "everyday" examples of such uses are:

    * Writing up a report (or paper) based on a System Dynamics model in a notebook, plotting all related graphs right there.
    * Creating and managing a comprehensive set of scenarios pertaining to that model.
    * Creating an interactive dashboard for a model.
    * Sharing models, dashboards and reports with people who do not have access to the original model environment.
    * Comparing multiple versions of a model to each other.

    We provide examples for all these points later in this document.

    More advanced examples for using models as computable objects are:

    * creating interactive games (see our version of the [Beergame](https://beergame.transentis.com) and the computational essay that goes with it. We built the model underlying the game using System Dynamics and transpiled the model into Javascript using our Javascript transpiler),
    * performing monte-carlo sensitivity analysis of a model on multiple machines in parallel, using state-of-the art, scalable parallel processing engines such as [Apache Spark](http://spark.apache.org)
    * training machine learning algorithms using System Dynamics models.
    * combining system dynamics models with other computational model techniques, such as agent based modeling.

    BPTK-Py is open source under the [MIT license](https://en.wikipedia.org/wiki/MIT_License), so you are free to use it in your own modeling projects. The notebook you are reading and the System Dynamics model behind it live in the [BPTK-Py repository](https://github.com/transentis/bptk_py) next to this page; the [installation instructions](../../usage/installation.md) say how to run them yourself.

    To demonstrate our computational essay approach using our BPTK PY framework we will use a very simple System Dynamics model. The System Dynamics model itself was built using the dynamic modeling and simulation software Stella® from [iseesystems](http://www.iseesystems.com).

    Stella saves models using the [XMILE format](https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=xmile), which is an open XML protocol for sharing interoperable system dynamics models and simulations. The XMILE standard is governed by the OASIS standards consortium - our framework currently only supports XMILE, we may create a compiler for other formats (such as Vensim® by [Ventana Systems](http://www.vensim.com)) in the future ([send us an email](mailto:support@transentis.com) if you are interested in this).

    To illustrate how our framework works, this post uses the model from our [Step-By-Step Introduction To System Dynamics](https://www.transentis.com/step-by-step-tutorials/introduction-to-system-dynamics/).

    We've included the stock and flow diagram of the entire model below – you don't need to understand how the model works to follow this post, but knowing the stock and flow structure will be useful.

    ![Simple Project Management Model](./sfd_simple_project_management.svg)

    The following sections illustrate various aspects of our framework and of how to use it.

    * [Importing the BPTK_Py Framework](#importing-the-framework)
    * [Setting up Scenarios and Scenario Managers](#setting-up-scenarios-and-scenario-managers)
    * [Plotting Scenario Results](#plotting-scenario-results)
    * [Accessing The Underlying System Dynamics Model](#accessing-the-underlying-system-dynamics-model)
    * [Accessing Model Information](#accessing-model-information)
    * [Checking and Comparing Models](#checking-and-comparing-models)

    ### Importing The Framework

    The Business Prototyping Toolkit for Python comes with a model transpiler, which automatically converts SD-models created with [Stella](http://www.iseesystems.com) into Python Code, a model simulator which lets you run those models in a Python environment (such as a notebook), a simple format for defining scenarios, and some methods to plot simulation results - these methods form the BPTK API.

    For most users this will be enough initially: you create the model using Stella and experiment with it by defining scenarios and plotting graphs in a notebook. Whenever you change the model in Stella, it is automatically transpiled to Python in a background process - so you can work on your model in Stella and write your computational essay in the notebook in parallel.

    You only need very limited Python skills to do this - the following sections show all the code that is needed to get up and running, and the [installation instructions](../../usage/installation.md) cover the setup. We have found that even modelers who are new to notebooks and Python can get productive with the toolkit within a few hours.

    More advanced users can use the full power of Python to access and manipulate the underlying simulation model and simulation results.

    >New to notebooks? Every code block on this page can be run and changed: hover over it and press the play button, or edit it first and then press play. Cells that depend on what you changed re-run by themselves. The first run takes a moment, because the Python environment is being set up in your browser.
    """)
    return


@app.cell
def _():
    #| echo: false
    ## BPTK Package
    from BPTK_Py.bptk import bptk 

    bptk = bptk()
    # '%matplotlib inline' command supported automatically in marimo
    import matplotlib.pyplot as plt
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['savefig.facecolor'] = 'white'
    return (bptk,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Setting up Scenarios and Scenario Managers
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Scenarios are just particular settings for the constants and graphical functions in your model and scenario managers are a simple way of grouping scenarios.

    You can create scenarios directly in Python, but the easiest way to maintain them is to keep them in separate files – you can define as many scenario managers and scenarios in a file as you would like and use as many files as you would like. Each scenario manager references the model it pertains to. So you can run multiple simulation models in one notebook.

    All the scenario definition files are kept in the ``scenarios/`` folder. The BPTK_Py framework will automatically scan this folder and load the scenarios – including the underlying simulation models – into memory.

    The following code lists all available scenario managers and scenarios:
    """)
    return


@app.cell
def _(bptk, mo):
    # marimo renders a cell's last expression, not its stdout - so the listing has to be
    # captured to reach the page rather than the browser console.
    with mo.capture_stdout() as managers_and_scenarios:
        print("Available Scenario Managers and Scenarios:")
        managers = bptk.scenario_manager_factory.get_scenario_managers(
            scenario_managers_to_filter=[]
        )
        for key, manager in managers.items():
            print("")
            print("*** {} ***".format(key))
            for name in manager.get_scenario_names():
                print("\t {}".format(name))

    mo.plain_text(managers_and_scenarios.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As the filename suggests, scenarios are defined using the [JSON format](http://www.json.org):

    ```json
    {
      "smSimpleProjectManagement": {
        "source": "simulation_models/sd_simple_project.itmx",
        "model": "simulation_models/sd_simple_project",
        "scenarios": {
          "scenario100": {
            "constants": {
              "deadline": 100,
              "effortPerTask": 1,
              "initialOpenTasks": 100,
              "initialStaff": 1
            }
          }
        }
      }
    }
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The outer bracket  defines the scenario manager. Next to containing a number of scenarios, the scenario manager also defines which model the scenarios apply to (the `source` field and also the `model` file which contains the model's transpiled Python code.

    Each scenario gets a name (`scenario100` in this example) and a list of constants which define the scenario settings.

    We can also take a look at how the scenario is stored in our Python Scenario Manager:
    """)
    return


@app.cell
def _(bptk):
    bptk.scenario_manager_factory.get_scenario("smSimpleProjectManagement","scenario100").dictionary
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The only difference in `scenario80` is that we have set the number of initial open tasks to 80 instead of 100.
    """)
    return


@app.cell
def _(bptk):
    bptk.scenario_manager_factory.get_scenario("smSimpleProjectManagement","scenario80").dictionary
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Plotting Scenario Results
    #### Example 1: Multiple Equations for one scenario
    Let's assume that we would like to plot multiple equations for the same scenario.

    All plotting is done using the ``bptk.plot_cenarios`` method. We just need to pass the name of the scenario ('scenario100') and the list of equations ('openTasks' and 'closedTasks').
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSimpleProjectManagement"],
        scenarios=["scenario100"], 
        equations=['openTasks','closedTasks'],
        title="Tasks remaining vs. Tasks closed",
        freq="D",
        start_date="1/1/2018",
        x_label="Time",
        y_label="Tasks", format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As you can see we can easly change the name of the diagram, the axes labels and the time scale. A legend showing the names of the plotted equations is displayed automatically. The colors for the plots are set in a configuration file - you can learn more about how to do this in the advanced documentation contained in our tutorial.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Renaming the series
    The equation names (such as `openTasks`) are often not the kind of names you want to show to the reader – in this case for instance we would much rather use the phrase `Open Tasks`.

    Fortunately we can use the ``series_name`` parameter to rename them.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSimpleProjectManagement"],
        scenarios=["scenario100"], 
        equations=['openTasks','closedTasks'],
        title="Renaming Equations",
         freq="D",
        start_date="1/1/2018",
        x_label="Time",
        y_label="Tasks",
        series_names={"openTasks" : "Open Tasks","closedTasks" : "Closed Tasks"}, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Example 2: Plot one equation for multiple scenarios
    Now let us change the perspective. In the above example we assumed one scenario for which we simulate multiple equations. Now we simulate **one equation for multiple scenarios**. This is useful whenever we want to compare the behaviour of the same model element between different scenarios.

    To achieve this, we supply just one equation and a list of scenarios to the `plot_scenarios` method.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSimpleProjectManagement"],
        scenarios=["scenario80","scenario100","scenario120"],
        equations=["openTasks"],
        title="One Equation for Multiple Scenarios",
         freq="D",
        start_date="1/1/2018",
        x_label="Time",
        y_label="Tasks",
        series_names={
            "smSimpleProjectManagement_scenario80_openTasks":"80 initial open tasks",
            "smSimpleProjectManagement_scenario100_openTasks":"100 initial open tasks",
            "smSimpleProjectManagement_scenario120_openTasks":"120 initial open tasks"
        }, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSimpleProjectManagement"],
        scenarios="scenario80,scenario100,scenario120",
        equations="productivity",
        title="One Equation with Multiple Scenarios",
         freq="D",
        start_date="1/1/2018",
        x_label="Time",
        y_label="Producitivty %",
        series_names={
            "smSimpleProjectManagement_scenario80_productivity":"80 initial open tasks",
            "smSimpleProjectManagement_scenario100_productivity":"100 initial open tasks",
            "smSimpleProjectManagement_scenario120_productivity":"120 initial open tasks"
        }, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### What if I want another kind of graph?

    The default output format for our plots shows each plot with a shaded area. This can easly be changed using the``kind`` parameter. Currently we also support the `line` and `stacked` setting.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSimpleProjectManagement"],
        scenarios="scenario80,scenario100,scenario120",
        equations="openTasks",
        kind="line",
        title="One Equation for Multiple Scenarios",
         freq="D",
        start_date="1/1/2018",
        x_label="Time",
        y_label="Tasks",
        series_names={
            "smSimpleProjectManagement_scenario80_openTasks":"80 initial open tasks",
            "smSimpleProjectManagement_scenario100_openTasks":"100 initial open tasks",
            "smSimpleProjectManagement_scenario120_openTasks":"120 initial open tasks"}, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### What if I need the underlying data?

    Sometimes you may not be interested in plotting a graph but would rather use the underlying data directly. This is easy – you can use use the `return_df=True` setting to return a dataframe containing all of the data in the scenario. The dataframe is provided as a [Pandas](http://pandas.pydata.org/) dataframe.
    """)
    return


@app.cell
def _(bptk):
    data=bptk.plot_scenarios(
            scenario_managers=["smSimpleProjectManagement"],
            scenarios=["scenario80"],
             freq="D",
            start_date="1/1/2018",
            equations=["openTasks","closedTasks","completionRate","remainingTime","schedulePressure","productivity"],
            return_df=True
    )
    return (data,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The dataframe is a table with a row for each day and a column for each of the scenarios. Using the `pandas.DataFrame.head` function we can show the first five rows of the dataframe:
    """)
    return


@app.cell
def _(data):
    data.head()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Once you have the dataframe, you can use the full power of `Python` and the `pandas` library to access the data, e.g. the `iloc`indexer to access a particular row.
    """)
    return


@app.cell
def _(data):
    data.iloc[4]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Accessing The Underlying System Dynamics Model

    The underlying System Dynamics model is automatically converted from the XMILE format into Python code – currently our transpiler only supports conversion of models in XMILE format, but we are planning to create a compiler for models in other formats.

    We keep both the Stella/XMILE models and the compiled models in the `/MODELS` directory.

    The actual equations underlying the simulation are stored in a dictonary of Python lambda functions within the class, e.g. here are the equations for closed tasks, open tasks and the completion rate:

    ```

    'closedTasks': lambda t : 0 if  t  <=  self.starttime  else self.memoize('closedTasks',t-self.dt)
                +  self.dt  * ( self.memoize('completionRate',t-self.dt) ),

    'openTasks': lambda t : self.memoize('initialOpenTasks', t) if  t  <=  self.starttime  else
                    self.memoize('openTasks',t-self.dt) +
                    self.dt  * ( -1 * ( self.memoize('completionRate',t-self.dt) ) ),

    'staff': lambda t : self.memoize('initialStaff', t) if  t  <=  self.starttime
            else self.memoize('staff',t-self.dt)
            +  self.dt  * 0,

    'completionRate': lambda t : max( 0, min( self.memoize('openTasks', t), self.memoize('staff', t) *
                    self.memoize('productivity', t) / self.memoize('effortPerTask', t) ) ),

    ```

    Because of the recursive nature of System Dynamics equations we use memoization to remember previous values – this makes the equations more cumbersome to read (and write should you want to create your own), but it dramatically speeds up calculations.

    You can easily access (and change) these lambda functions if you want to, they are stored in a dictionary within the model, which itself is associated with the scenario. Assocating the model with the scenario is essential because it ensure that the scenario settings are automatically applied to the model.
    """)
    return


@app.cell
def _(bptk):
    bptk.scenario_manager_factory.get_scenario("smSimpleProjectManagement","scenario80").model.equations
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can run these equations and access individual values:
    """)
    return


@app.cell
def _(bptk):
    bptk.scenario_manager_factory.get_scenario("smSimpleProjectManagement","scenario100").model.equations["closedTasks"](10)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    If you want to build complete models directly in Python, we recommend using the domain-specific language for SD, which we created especially for this purpose. This DSL is also part of BPTK-Py, and the [System Dynamics section](../../sd-dsl/sddsl.md) covers it.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Accessing Model Information
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Having the model in a python class is useful for other purposes too – for instance you can access the list of stocks, flows and converters to check which elements are in your model:
    """)
    return


@app.cell
def _(bptk):
    bptk.scenario_manager_factory.get_scenarios()["smSimpleProjectManagement_scenario100"].model.stocks
    return


@app.cell
def _(bptk):
    bptk.scenario_manager_factory.get_scenarios()["smSimpleProjectManagement_scenario100"].model.constants
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Of course we can then pretty-print this as HTML:
    """)
    return


@app.cell
def _(bptk, mo):
    # marimo has no `IPython.display`; `mo.md` renders the same markup, and a markdown
    # list is less work than assembling HTML by hand.
    stocks = bptk.scenario_manager_factory.get_scenario(
        "smSimpleProjectManagement", "scenario100"
    ).model.stocks

    mo.md("\n".join(f"* {stock}" for stock in stocks))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can also easily output the settings for the constants in the model (for any of the defined scenarios)
    """)
    return


@app.cell
def _(bptk, mo):
    # The constants of two scenarios side by side. Both listings in one cell, because a
    # cell renders one value: printing into a captured buffer keeps them together.
    def constants_of(scenario_name):
        scenario = bptk.scenario_manager_factory.get_scenario(
            "smSimpleProjectManagement", scenario_name
        )
        for constant in scenario.model.constants:
            print(f"  {constant}: {scenario.model.equations[constant](0)}")

    with mo.capture_stdout() as constants:
        print("scenario100")
        constants_of("scenario100")
        print("")
        print("scenario80")
        constants_of("scenario80")

    mo.plain_text(constants.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Checking and Comparing Models

    We can also easily compare two different versions of a model to each other - for instance let's assume we have two versions of our project management model, which say contain different settings for the graphical function we use to model the effect of schedule pressure on productivity and also the number of inital open tasks (as defined in the underlying model, not in the scenarios).

    Let's compare the results between the models:
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(scenario_managers="smSimpleProjectManagement,smSimpleProjectManagementV0",
        scenarios="scenario80",
        equations='openTasks',
        title="Compare Two Models",
        series_names={"smSimpleProjectManagement_scenario80_openTasks":"Current Model","smSimpleProjectManagementV0_scenario80_openTasks":"Model v0"}, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can also create some code that automatically lists all of the model elements that have changed between the two models:
    """)
    return


@app.cell
def _(bptk, mo):
    current = bptk.scenario_manager_factory.get_scenario(
        "smSimpleProjectManagement", "base"
    ).model
    v0 = bptk.scenario_manager_factory.get_scenario(
        "smSimpleProjectManagementV0", "base"
    ).model

    with mo.capture_stdout() as differences:
        for constant_name in current.constants:
            if constant_name not in v0.equations:
                continue
            hier = current.equations[constant_name](1)
            dort = v0.equations[constant_name](1)
            if hier != dort:
                print(f"{constant_name}, current model: {hier}, model v0: {dort}")

    mo.plain_text(differences.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Note that this last function isn't part of the BPTK framework, but it uses a number of methods provided by the framework this shows the real power of making models computable: because you can manipulate models using code, you can easily create your own functions to use your models in any way you want.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Conclusion
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This page detailed our approach to building interactive stories based on simulation models using Python, notebooks and the BPTK-Py framework. Here are the important points you should remember:

    * If you want to use the insights gained from simulation models to have an impact in the real world, just having the model and the insights is often not enough – you need to develop a good story that persuades your stakeholders to make decisions and take action.
    * Python notebooks provide a great environment for rapidly building such interactive stories that rely on data and on simulations. Using the BPTK_PY framework, creating such documents is actually quite easy. You can concentrate on the story and let the framework do the heavy lifting.
    * Building complex simulations using System Dynamics is best done using visual modeling environments such as Stella. Thanks to the XMILE standard and our BPTK PY framework, we can import System Dynamics models created with Stella straight into Python and run them there.
    * Once you have finished the interactive story you can publish it to a wide audience by sharing the notebook - or by rendering it into a site like this one. All of it is free.

    To see interactive stories and games written using this approach, take a look at our blog posts on [Prototyping Business Models and Market Strategies](../../model_library/customer_acquisition/customer_acquisition.md), on [Growth Strategies in Professional Service Firms](../../model_library/make_your_psf_grow/sddsl/make_your_psf_grow_intro.md) or the [Beergame](../../model_library/beergame/beergame.md).
    """)
    return


if __name__ == "__main__":
    app.run()
