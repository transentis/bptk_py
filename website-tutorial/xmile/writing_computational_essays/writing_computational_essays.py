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

    *If you want to use the insights gained from simulation models to transform your enterprise, just having the model and the insights alone is often not enough – you need to develop a good story that persuades your stakeholders to make decisions and take action.*

    *Our BPTK_PY library allows you to convert System Dynamics models into Python code and run them in a notebook, which is a wonderful place for writing interactive, data-driven papers and reports.*

    Many years ago we published a blog post titled _Telling Stories with System Dynamics Models_ which introduced our approach to telling interactive stories based on simulation models built using System Dynamics.

    Writing such interactive stories is quite challenging, even if your simulation model is already fairly complete, because you need to craft the storyline while testing different scenarios with the simulation model.

    We realised early on that what we needed was an "interactive writing environment" that would help us to prototype a complex story line while still building the model:

    * Build an initial simulation model using a visual modeling tool.
    * Start writing a story around the model using the interactive writing environment.
    * Use the new questions and insights that arise during the writing process to drive experiments with the simulation model – this may lead to changes in both the model and the storyline.

    In 2014 we started writing such "computational essays" using [Wolfram Research's](http://www.wolfram.com) Mathematica®.

    Mathematica is a wonderful and very powerful tool to support this process – it is a complete environment that supports writing, computation, presentation and very sophisticated interactive dashboards.

    Mathematica does not contain native support for System Dynamics, but we crafted a small library that allows us to import System Dynamics models based on the XMILE standard and to run them in Mathematica.

    But since 2014 a lot has happened in the world of computational modelling ... Python has become the premier programming language for data science and its use has thus become even more ubiquitous, and with it the notebook as a working environment - first [Jupyter](http://www.jupyter.org), and more recently [marimo](https://marimo.io), which is what this documentation is written in.

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
    * performing Monte Carlo sensitivity analysis of a model on multiple machines in parallel, using state-of-the-art, scalable parallel processing engines such as [Apache Spark](http://spark.apache.org)
    * training machine learning algorithms using System Dynamics models.
    * combining system dynamics models with other computational model techniques, such as agent-based modeling.

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

    The Business Prototyping Toolkit for Python comes with a model transpiler, which automatically converts SD-models created with [Stella](http://www.iseesystems.com) into SD DSL code, a model simulator which lets you run those models in a Python environment (such as a notebook), a simple format for defining scenarios, and some methods to plot simulation results - these methods form the BPTK API.

    For most users this will be enough initially: you create the model using Stella and experiment with it by defining scenarios and plotting graphs in a notebook. Whenever you change the model in Stella, it is transpiled again in the background, as [XMILE Step by Step](../xmile_step_by_step/xmile_step_by_step.md) explains - so you can work on your model in Stella and write your computational essay in the notebook in parallel.

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

    Here they are kept in files in the ``scenarios/`` folder, which BPTK-Py reads when it starts - [Scenarios In Depth](../../concepts/scenarios/scenarios.md) describes the format.

    The following code lists all available scenario managers and scenarios:
    """)
    return


@app.cell
def _(bptk, mo):
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
    The scenarios of this page differ in the number of initial open tasks - 80, 100 and 120.

    ### Plotting Scenario Results
    #### Example 1: Multiple Equations for one scenario
    Let's assume that we would like to plot multiple equations for the same scenario.

    All plotting is done using the ``bptk.plot_scenarios`` method. We just need to pass the name of the scenario ('scenario100') and the list of equations ('openTasks' and 'closedTasks').
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
        y_label="Tasks",
        series_names={"openTasks" : "Open Tasks","closedTasks" : "Closed Tasks"}, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The title, the axis labels, the time scale and the names of the series are all arguments of the same call; [Advanced Plotting Features](../../concepts/advanced_plotting_features/advanced_plotting_features.md) shows them and the other kinds of graph, and [Configuration](../../concepts/configuration/configuration.md#configure-graphic-settings) the colours.

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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    To work with the numbers rather than a plot, pass `return_df=True` and you get a pandas dataframe - see [Accessing Raw Simulation Results](../../concepts/accessing_raw_simulation_results/accessing_raw_simulation_results.md).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Accessing The Underlying System Dynamics Model

    The underlying System Dynamics model is automatically converted from the XMILE format into SD DSL code. Both the Stella/XMILE model and the compiled model are kept in the `simulation_models` directory.

    The compiled model is written in the SD DSL: a `Model` that first defines every element and then sets the initial values and equations, both grouped by kind. Here are the closed tasks, the open tasks and the completion rate from the second part:

    ```
    # Stocks
    closedTasks.initial_value = 0.0
    closedTasks.inflows = [completionRate]
    openTasks.initial_value = initialOpenTasks
    openTasks.outflows = [completionRate]

    # Flows
    completionRate.equation = sd.max(0.0, sd.min(openTasks, ((staff * productivity) / effortPerTask)))
    ```

    Because of the recursive nature of System Dynamics equations, the Python engine uses memoization to remember previous values – it dramatically speeds up calculations.

    When the model runs, each equation becomes a Python function of the time `t`. You can easily access (and change) these functions if you want to, they are stored in a dictionary within the model, which itself is associated with the scenario. Associating the model with the scenario is essential because it ensures that the scenario settings are automatically applied to the model.
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
    Having the model in a Python class is useful for other purposes too – for instance you can access the list of stocks, flows and converters to check which elements are in your model:
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
    # The constants of two scenarios side by side.
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

    We can also easily compare two different versions of a model to each other - for instance let's assume we have two versions of our project management model, which say contain different settings for the graphical function we use to model the effect of schedule pressure on productivity and also the number of initial open tasks (as defined in the underlying model, not in the scenarios).

    Let's compare the results between the models:
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(scenario_managers="smSimpleProjectManagement,smSimpleProjectManagementV0",
        scenarios="scenario80",
        equations='openTasks',
        title="Compare Two Models",
        series_names={
            "smSimpleProjectManagement_scenario80_openTasks": "Current Model",
            "smSimpleProjectManagementV0_scenario80_openTasks": "Model v0",
        }, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can also create some code that automatically lists the constants whose values differ between the two models:
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
            current_value = current.equations[constant_name](1)
            v0_value = v0.equations[constant_name](1)
            if current_value != v0_value:
                print(f"{constant_name}, current model: {current_value}, model v0: {v0_value}")

    mo.plain_text(differences.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Note that this last function isn't part of the BPTK framework, but it uses a number of methods provided by the framework - this shows the real power of making models computable: because you can manipulate models using code, you can easily create your own functions to use your models in any way you want.
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
