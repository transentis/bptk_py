***************
The BPTK Class
***************

The ``bptk`` class provides high level functions that let you interact with your simulation models and scenarios.

You will typically start the framework by instantiating the ``bptk`` class within a Jupyer notebook, as follows: ::

 import BPTK_PY
 bptk=bptk()

This automatically starts a background process that scans your ``scenario`` directory and imports all scenarios.

The ``bptk`` class has the following methods::

 def plot_scenarios(
           self,
           scenarios,
           scenario_managers,
           agents=[],
           agent_states=[],
           agent_properties=[],
           agent_property_types=[],
           equations=[],
           kind=config.configuration["kind"],
           alpha=config.configuration["alpha"],
           stacked=config.configuration["stacked"],
           freq="D",
           start_date="",
           title="",
           visualize_from_period=0,
           visualize_to_period=0,
           x_label="",
           y_label="",
           series_names={},
           strategy=False,
           progressBar=False,
           return_df=False)

Generic method for plotting scenarios for System Dynamics as well as agent-based models (ABM).

Arguments:

* scenarios: names of scenarios to plot
* equations:  names of equations to plot (System Dynamics, SD)
* agents: List of agents to plot (Agent based modelling)
* agent_states: List of agent states to plot, REQUIRES "AGENTS" param
* scenario_managers: names of scenario managers to plot
* kind: type of graph to plot ("line" or "area")
* alpha:  transparency 0 < x <= 1
* stacked: if yes, use stacked (only with kind="bar")
* freq: frequency of time series
* start_date: start date for time series
* title: title of plot
* visualize_from_period: visualize from specific period onwards
* visualize_to_period; visualize until a specific period
* x_label: label for x axis
* y_label: label for y axis
* series_names: names of series to rename to, using a dict: {equation_name : rename_to}
* strategy: set True if you want to use the scenarios' strategies
* progressBar: set True if you want to show a progress bar (useful for ABM simulations)
* return_df: set True if you want to receive a dataFrame instead of the plot

The method returns nothing or a Pandas dataframe with simulation results if return_df=True


