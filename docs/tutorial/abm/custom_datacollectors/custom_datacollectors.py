# Front matter the .py format cannot carry; injected on export.
# description: In-depth explanation of agent-based modeling
# keywords: agent-based modeling, abm, bptk, python
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Choose Data Collector")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Custom Data Collectors
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    For agent-based models BPTK-Py has a standard data collector which collects the statistics (average, minumum, etc.) for all properties of all __agent types__. Collecting statistics for each agent individually will lead to a huge amount of data. However, if you want to explore this case or other cases which the standard data collector does not cover, you can also implement your own data collector. In this notebook, we explain how to proceed. Therefore we implement a new data collector class which collects the properties of each agent individually.

    We first create a new class and choose a name for it: `AgentDataCollector`. Then we implement the necessary methods and constructors. However, we don't want to create a whole new class but use the already existing methods of the standard data collector and extend it for our purposes. This saves a lot of work. The new data collector requires the following methods:

    - A method which collects the data of each agent
    - A method which represents the collected data in a dataframe (this is necessary for the plot method)
    - A method which plots the data because the standard visualization class of BPTK-Py cannot handle the new data collector

    _The data collector `AgentDataCollector` already ships with BPTK-Py — see [AgentDataCollector](../../api/api_agentdatacollector.md) for its API. This page explains how it is built, so you can write one of your own._
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Create data collector class
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Create a class and name it `AgentDataCollector`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Import libraries
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As explained before, we want to derive the new data collector class from the standard class. Therefore we have to import the standard data collector.

    ```python
    from BPTK_Py import DataCollector
    ```

    For plotting the data, we also require pandas and a BPTK-Py config library. The config library is necessary to obtain the same plot design as the standard plot from BPTK-Py.

    ```python
    import pandas as pd
    import BPTK_Py.config as config
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Of course, you can add as many libraries as you want. In depends on what you need for your collector.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Derive standard class
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This how you derive the standard data collector:

    ```python
    class AgentDataCollector(DataCollector):
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Implement methods
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As I explained before, we can either extend the class or replace methods. Since we want to overwrite the collecting method we have to replace `def collect_agent_statistic(self, time, agents)`. Now you can implement the logic of your own data collector. To save the statistics, you can use the attribute `self.agent_statistics` which is an empty dictionary.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    After collecting all the data we have to bring them into an usable structure to be able to plot the statistics later. I chose to transform the dictionary into multiple dataframes. For each agent there exists one dataframe with its statistics. When we have the statistics in a dataframe we can exploit the functionalities of the library pandas.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The data is prepared and we can now plot them by using the visualization methods of pandas. To obtain the same design as the plot of BPTK-Py you need change the following parameters of the plot method. For the parameter `title` you can set any title name. The [Configuration](../../concepts/configuration/configuration.md) chapter explains what each of these settings does.

    ```python
    df.plot(kind=config.configuration["kind"],
                                      alpha=config.configuration["alpha"],
                                      stacked=config.configuration["stacked"],
                                      figsize=config.configuration["figsize"],
                                      title=title,
                                      color=config.configuration["colors"],
                                      lw=config.configuration["linewidth"])
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5. Set our new data collector in simulation model
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The previous steps explained how to implement a data collector. Now, we have to set the new data collector in our model class. To show you each step, we use our model SPMAgentDataCollector.py which is in `./simulation_models/spm`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    1. You go to the simulation model and open the Python file.
    2. Import the new data collector: `from BPTK_Py import AgentDataCollector`.
    3. Add `self.data_collector=AgentDataCollector()` in `instantiate_model(self)`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6. Run simulation model with new data collector
    """)
    return


@app.cell
def _():
    # Start BPTK and automatically read the scenarios found in the scenarios folder
    # this also loads all the Python classes referenced in the scenarios, so we are immediately ready 
    # to run scenarios and plot results.

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
    plt.rcParams['savefig.facecolor'] = 'white'
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In this step, we run the simulation model with a specific scenario. All statistics of each agent are collected by the data collector.
    """)
    return


@app.cell
def _(bptk):
    model = bptk.scenario_manager_factory.get_scenario("ABMsmSimpleProjectManagementAgentDataCollector","scenario80").model
    model.run()
    return (model,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now you can plot the stats of one or more specific agents. In our case we want to compare two tasks and see how much effort remains for them.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The following bullet points describe the parameters of the plot method:

    - agent_ids: choose the stats of the agents you want plot
    - properties: choose properties you want to plot
    - title: choose title of the plot
    - agent_type: choose the agent type
    """)
    return


@app.cell
def _(model):
    model.data_collector.plot_agent_stats(agent_ids=[2,3],properties=['remaining_effort'],title="Scenario80",agent_type="task")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Output the stats in a dataframe
    """)
    return


@app.cell
def _(model):
    model.data_collector.get_agent_stats()['task'][2]
    return


@app.cell
def _(model):
    model.data_collector.get_agent_stats()['task'][3]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    If you want to get all stats of each agent you call `model.data_collector.get_agent_stats()`
    """)
    return


if __name__ == "__main__":
    app.run()
