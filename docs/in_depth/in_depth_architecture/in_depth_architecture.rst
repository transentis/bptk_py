**************************************
The Architecture of The BPTK Framework
**************************************

This document explains the overall architecture of the BPTK framework.

Conceptually, there are five major building blocks:

* A component that allows you to build and run simulations in Python, using an Agent-based modeling approach, a System Dynamics modelling approach or both ("hybrid models").
* A component that (automatically) translates System Dynamic models conforming to the XMILE standard into Python code.
* A component that lets you define and manage simulation scenarios in a uniform manner.
* A component that visualises the results produced by simulations, in the form of plots or dashboards.
* A high level API that lets you interact with the other components using a simple and uniform API. In particular, this component allows you to run scenarios and plot scenario results from both models created in Python or translated from XMILE in a uniform manner.

Before explaining how to make more complex plots or work with the output data, we would like to show you the architecture of the plotting API. The goal of the design is to decouple actual objects that *do* things from the API object, i.e. ``bptk``.


Now let's see what happens at runtime, assuming that we are in a Jupyter notebook.

First of all we initialize the framework by creating a ``bptk`` object. This automatically causes the framework to read all scenario config files from the ``scenario`` directory. The location of this directory can be configured in the frameworks config file. ::

    # this is how you instantiate the bptk object
    from BPTK_Py.bptk import bptk

    bptk = bptk()

For each scenario manager in the config files, a scenario manager object is created, which again will contain a reference to all the scenarios defined in the config file.

Depending on whether a scenario relates to a Python model or an XMILE model, the scenario will either be a correctly configured instance of the Python model or it will contain all the equations transpiled from the XMILE model.

At this stage, all scenario managers, scenarios and models have been instantiated and configured according to the scenario definitions, but the have not run yet.

This is very useful, because it means you can easliy compare the results of running different configurations of the same model or different versions of the same model using the same configuration or even completely different models to each other.

You can take a look at all the scenarios that have been loaded using the following piece of code – this is particularly useful for debugging purposes. ::

    print()
    print("Available Scenario Managers and Scenarios:")
    print()
    managers = bptk.scenario_manager_factory.get_scenario_managers(scenario_managers_to_filter=[])

    for key, manager in managers.items():
        print("")
        print("*** {} ***".format(key))

        for name in manager.get_scenario_names():
            print("\t {}".format(name))

If you do this in a Jupyter notebook created within our `BPTK tutorial <http://www.transentis.com/business-prototyping-toolkit>`_, you should get a result similar to this one: ::

    Available Scenario Managers and Scenarios:


    *** smSimpleProjectManagementDslClass ***
         scenario100_strategy
         scenario100
         scenario80
         scenario120

    *** ABMsmSimpleProjectManagement ***
         scenario80
         scenario100
         scenario120
         scenario80DT1
         scenario100SM2D50
         scenario100SM2D90

    *** anotherSimpleProjectManagement ***
         scenario100
         scenario80
         scenario120

    *** smSimpleProjectManagement ***
         base
         scenario100
         scenario80
         scenario120
         scenario100WithPoints

    *** smInteractive ***
         scenario100

    *** smSimpleProjectManagementV0 ***
         base
         scenario100
         scenario80
         scenario120

    *** ABMsmBass ***
         scenarioBassBase

Sofar, none of the scenarios have been simulated yet. You could now run scenario by calling ``bptk.run_simulation()``, which runs the simulation and returns a dataset. But in most cases you probably want to visualise the results directly, in which case ``bptk.plot_scenario`` is the method to use.

Ler's choose one of the scenarios from the list above, e.g. the ```est`` from the ``scenarioMananger``. then you could plot this as follows ::

    bptk.plot_scenarios(
        scenario_managers=["smSimpleProjectManagement"],
        scenarios=["scenario120"],
        equations=['openTasks',"closedTasks"],
        title="Example Plot with Dates",
        x_label="Date",
        y_label="Open / Closed Tasks",
        start_date="1/11/2017",
        freq="D"
    )

This leads to the following result:

Let's what happens behind the scenes in order to produce that result:


As mentioned above, the ``bptk`` object doesn't contain much logic of its own, because we want to decouple the bptk API from the components that actually *do* things.

The visualizer decouples simulation and visualization by forwarding method calls for the simulation to a ``simulation_wrapper`` (step 3) and later create the plots from the result data (step 9).

The call in step 3 is actually forwarded via ``bptk`` but we decided to omit this for readability.

Hence, you may use the ``run_simulation`` call without having to go the extra mile via the visualizer.

However, we strongly encourage you to use the ``plot_scenarios`` method and obtain the resulting data using the ``return_df`` flag.

It comes with neat features like generating timeseries data from your simulation results.

The ``simulationWrapper`` handles the simulations for each scenario. At this stage, the scenarios are only given with their names.

Hence, the simulator has to get the actual data that the ``scenarioManagerFactory`` read from the JSON files (step 4).

On the right side we denoted the hierarchy of the ``scenarioManager`` and ``simulationScenario``.
The factory is at the top level and loads the JSON files and creates the scenario Managers.

The scenario Manager  instantiates the simulation models from the model files and makes sure to transpile the Stella Architect models into Python.

In a sense, it is the manager of the scenarioManagers, which group the actual scenarios. After looking up the scenarios, the factory returns these to the simulationWrapper (step 5).

Finally, the simulations start for each scenario using the model simulator and are returned to the simulationWrapper (steps 6 and 7).

The results are routed back to the Visualizer (step 8, keep in mind: Actually via bptk but omitted for readability).

Finally, the Visualizer generates the time series data, the plots and formats them (step 9).

The output goes back to ``bptk`` and the user gets to see a plot created with `Matplotlib <http://www.matplotlib.org>`_ - or a dataFrame if she used the ``return_df`` flag - step 10.

So even though the API of the bptk object is simple, there is actually quite a lot going on behind the scenes. Because of the decoupling of the modules, we can treat both ABM, native SD and transpiled SD models in a similar fashion and we can further componemts if necessary.

