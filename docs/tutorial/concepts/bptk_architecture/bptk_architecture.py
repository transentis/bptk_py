# Front matter the .py format cannot carry; injected on export.
# description: Explains the architecture of the BPTK-Py business simulation framework, as it applies to Agent-based modeling and System Dynamics.
# keywords: agent-based modeling, abm, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Architecture")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # The Architecture Of The BPTK_PY Framework

    This document explains the overall architecture of the BPTK framework.

    ## BPTK Building Blocks

    The BPTK framework was designed to meet a number of objectives:

    * Provide the modeler and analyst working in a notebook environment with an easy to use API, bearing in mind that such analysts may not be expert Python developers.
    * Provide the ability to run simulations standalone (i.e. outside of a notebook environment)
    * Focus on modeling and simulation and reuse libraries such as [Pandas](http://pandas.pydata.org) and [Matplotlib](http://www.matplotlib.org) for manipulating and plotting simulation results.

    Currently the framework has five conceptual building blocks:

    * *ABM and SD Modeling.* A component that allows you to build and run simulations in Python, using an Agent-based modeling approach, a System Dynamics modelling approach or both ("hybrid models"). This component contains a number of classes that you will need to build such models - please read the notebooks on [agent-based modeling](../../abm/agent_based_modeling/agent_based_modeling.md) and [System Dynamics modeling](../../sd-dsl/simple_python_library_sd_dsl/simple_python_library_sd_dsl.md) to learn more about these classes.
    * *SD Transpiler.* A component that (automatically) translates System Dynamic models conforming to the XMILE standard into Python code.
    * *Scenario Management.* A component that lets you define and manage simulation scenarios in a uniform manner. A scenario is a model and a set of initial values for the simulation parameters. Scenarios are a powerful tool, because they enable you to easily compare the results of running the same simulation with different parameters to each other, which is something you have to do frequently when working with simulations.
    * *Visualisation.* A component that visualises the results produced by simulations, in the form of plots or dashboards.
    * *BPTK API.* A high level API that lets you interact with the other components using a simple and uniform API. In particular, this component allows you to run scenarios and plot scenario results from both models created in Python or translated from XMILE in a uniform manner.

    To use the framework, the modeler needs to build simulation models, either directly Python (AB/SD Model) or in XMILE (using an XMILE compatible SD modeling tool, such as isee systems Stella). A model created in Python is essentially a subclass of the AB and SD Modeling component, while the XMILE models are transpiled into such a subclass by the SD Transpiler component.

    How does the framework know which models to compile? This is what the scenario config files are for - the modeler uses these to define scenario parameters and to identify the model that is relevant for a particular scenario. The model is then either the name of a Python class or the name of an XMILE model.

    The diagram below shows these building blocks and their dependencies.

    ![BPTK Components](BPTK_Components.png)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## How The Components Work Together At Runtime

    Now let's see what happens at runtime, assuming that we are in a notebook.

    First of all we initialize the framework by creating a ``bptk`` object. This automatically causes the framework to read all scenario config files from the ``scenarios`` directory. The location of this directory can be configured in the framework's config file.

    This page has one such file beside it, and it is worth opening before reading on:
    [`scenarios/spm.json`](./scenarios/spm.json). It names the
    [XMILE model](./simulation_models/sd_simple_project.itmx) to transpile, the constants
    every scenario starts from, and the four scenarios that differ from those constants —
    which is exactly what the code below finds.
    """)
    return


@app.cell
def _():
    ## BPTK Package
    from BPTK_Py.bptk import bptk 

    bptk = bptk()
    return (bptk,)


@app.cell
def _():
    #| echo: false
    # '%matplotlib inline' command supported automatically in marimo
    import matplotlib.pyplot as plt
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['savefig.facecolor'] = 'white'
    return (plt,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Depending on whether a scenario relates to a Python model or an XMILE model, the scenario will either be a correctly configured instance of the Python model or it will contain all the equations transpiled from the XMILE model.

    At this stage, all scenario managers, scenarios and models have been instantiated and configured according to the scenario definitions, but the simulations have not run yet.

    You can easily test the transpiler by deleting the transpiled Python classes from the scenario manager directory - the scenario manager notices this and automatically re-transpiles the model. This behaviour is particularly useful when building XMILE models and testing scenarios in a notebook in parallel. As soon as you change the XMILE model, the model is re-transpiled into Python. Now all you need to do is reset the model in the notebook and the Python class is then automatically reloaded.

    The following piece of code lists all the scenarios that have been loaded:
    """)
    return


@app.cell
def _(bptk, mo):
    managers = bptk.scenario_manager_factory.get_scenario_managers()

    # marimo sends a cell's stdout to the console rather than to its output area;
    # captured and handed to `mo.plain_text` it comes back as one block.
    with mo.capture_stdout() as output:
        print("Available Scenario Managers and Scenarios:")
        for key, manager in managers.items():
            print("")
            print(key)
            for name in manager.get_scenario_names():
                print("    {}".format(name))

    mo.plain_text(output.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Back to our discussion of ``bptk.plot_scenarios``: so far the scenarios have been loaded but
    not simulated (which is good — there could be very many of them, and you rarely want to run
    them all at once).

    To run one, you can call ``bptk.run_scenarios`` with the appropriate parameters, which runs
    the given scenarios and returns a dataframe. In most cases you want to see the result
    directly, and then ``bptk.plot_scenarios`` is the method to use.

    **Try it.** The controls below are wired to a single `plot_scenarios` call: pick a different
    scenario, add or remove an equation, and the diagram is recomputed. Everything the rest of
    this page describes — the scenario manager, the cache, the visualisation component — runs on
    every change.
    """)
    return


@app.cell
def _(bptk, mo):
    # The UI elements have to live in a different cell from the one that reads their
    # `.value` - marimo requires that, and merging the two would silently remove the
    # interactivity.
    scenario_choice = mo.ui.dropdown(
        options=sorted(bptk.get_scenario_names(["smSimpleProjectManagement"])),
        value="scenario120",
        label="Scenario",
    )
    equation_choice = mo.ui.multiselect(
        options=[
            "openTasks", "closedTasks", "staff", "completionRate",
            "deadline", "remainingTime", "schedulePressure", "effortPerTask",
        ],
        value=["openTasks"],
        label="Equations",
    )
    return equation_choice, scenario_choice


@app.cell
def _(bptk, equation_choice, mo, plt, scenario_choice):
    # Every plot leaves its figure in matplotlib's registry, and this cell re-runs on
    # every control change - closing the previous run's figures keeps the browser's
    # heap bounded.
    plt.close("all")

    _axes = bptk.plot_scenarios(
        scenario_managers=["smSimpleProjectManagement"],
        scenarios=[scenario_choice.value],
        equations=equation_choice.value or ["openTasks"],
        title=f"{scenario_choice.value}",
        x_label="Time",
        y_label="Value",
        format="axes",
    )

    mo.vstack([mo.hstack([scenario_choice, equation_choice], justify="start"), _axes.figure])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    What happens behind the scenes in order to produce this result?

    As mentioned above, the ``bptk`` object doesn't contain much logic of its own, because we want to decouple the API from the components that actually *do* the heavy lifting.

    The BPTK API calls the scenario manager to run the scenario.

    The scenario manager checks its internal simulation cache to see whether the scenario has already been run - if so, it passes the dataframe containing the simulation results from the cache to the visualisation component, which creates the relevant plot.

    This caching behaviour is essential – it means you do not need to re-run the scenario to plot the results from another equations or agent, you just need to look up the result in the cache. Without the cache, you would have to run the simulation again for every plot, which could take quite some time depending on the size and complexity of the model.

    If there is no data in the cache, the scenario manager runs the scenario by calling its ``run`` method, and then passes the dataframe to the ``visualisation`` component.

    ## Summary

    Even though the API of the ``bptk`` object is simple, there is actually quite a lot going on behind the scenes. Because the components only communicate via well-defined interfaces, the scenario manager can treat both ABM, native SD and transpiled SD models in a similar fashion. The framework could also be easily extended to deal with other kinds of simulations.
    """)
    return


if __name__ == "__main__":
    app.run()
