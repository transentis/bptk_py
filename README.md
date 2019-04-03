# Business Prototyping Toolkit for Python 

__System Dynamics and Agent-based Modeling in Python__

The Business Prototyping Toolkit for Python (BPTK_Py) provides you with a computational modeling framework that allows you to build and run simulation models using System Dynamics and/or agent-based modeling and manage simulation scenarios with ease. 
 
It gives you the power to quickly build simulation models in Python. If you use the framework with Jupyter Notebooks, you to create beautiful plots of the simulation results - or just run the simulation in Python and use the results however you wish.


The framework also includes our *sdcc parser*  for transpiling  System Dynamics models conforming to the XMILE standard into Python code. This means you can build models using your favorite XMILE environment (such as [iseesystems Stella]( http://www.iseesystems.com) and then experiment with them in [Juypter](http://www.jupyter.org).


## Main Features
* The BPTK_Py framework supports System Dynamics models in XMILE Format, native SD models, Agent-based models and hybrid SD-ABM-Models
* The objective of the framework is to provide the infrastructure for managing model settings and scenarios and for running and plotting simulation results, so that the modeller can concentrate on modelling.
* The framework automatically collect statistics on agents, their states and their properties, which makes plotting simulation results very easy.
* All plotting is done using [Matplotlib](http://www.matplotlib.org).
* Simulation results can also be returned as [Pandas dataframes](http://pandas.pydata.org).
* The framework uses some advanced Python metaprogramming techniques to ensure the amount of boilerplate code the modeler has to write is kept to a minimum.
* Model settings and scenarios are kept in JSON files. These settings are automatically loaded by the framework upon initialization, as are the model classes themselves. This makes interactive modeling, coding and testing very painless, especially if using the Jupyter notebook environment.

# Getting Help
The first place to go to for help and installation instructions is the [online documentation](http://bptk.transentis-labs.com).

You should also download the BPTK_Py tutorial, which contains the sample models and Jupyter notebooks referenced in the online documentation. You can download the tutorial from our [website](https://www.transentis.com/products/business-prototyping-toolkit/). 

BPTK_Py is developed and maintained by transentis Labs GmbH. 

For questions regarding installation, usage and other help please contact us at: [support@transentis.com](mailto:support@transentis.com).

## Changelog

### 0.8.0
* Fixed an annoying bug: We forgot to include the threads that watch the scenario JSON files into the ``bptk.destroy()`` method. Now it runs properly and once executed all monitors will stop monitoring.
* YAML Support! Now you can easily define your models using YAML notation. This is much simpler than JSON. 
* As a perk, you do not need the model implementation for AB models anymore. When using YAML notation, BPTK will create the necessary objects without requiring code. So now you can concentrate onyour agents without the need of registering agent factories!
* Choose Data collector class within the model file: The YAML file now supports the directive ``datacollector``. Here you can link to custom data collector classes. Try the included ones such as ``BPTK_Py.abm.CSVDAtaCollector``. Using custom data collectors reduces simulation time tremendously as ``BPTK-Py`` will not use its slow mechanism to create dataframes anymore.
* We also included a meta model creator feeding on parser results. You only need to implement the model parser and feed the model creator. The model creator then builds the actual simulation model. This way, you can add modelling languages easily!


### 0.7.0
* Added Delayed Events in Agent based modelling. Now each agent can send events that trigger in the future. Instantiate a ```DelayedEvent``` and set the ``trigger_in`` parameter with the number of periods to wait before trigger. The framework will make sure to trigger the event at the right time.
* Multithreading for scenario execution: Speeding up multi-scenario simulation siginificantly by using one thread per scenario
* Added ``agent_type`` as optional parameter for Agent. Now you do not need to add the agent type in the initialize method anymore if that is what you prefer
* Better handling of progress bar in ABM simulation using ``ipywidgets.Out`` to make bar disappear after executiob. Removed running scheduler as thread because this is not required here.
* ABM: If you still have scenario manager files but deleted the code, execution will not be stopped anymore but faulty scenario is skipped with an Error message. 


### 0.6.6
* Little improvements and bugfixes to data collectors. For Kinesis, you will be warned if ``boto`` (required for AWS access) is not installed as it is not a package dependency.

### 0.6.5
* We want to make data analysis easy for you. Hence, we added data collectors as standard for model output: ``CSVDataCollector`` outputs each agents' events to CSV, one file per agent. ``KinesisDataCollector`` outputs the agent statistics to Kinesis, an AWS service. For both, the data output is event-wise

### 0.6.4

* New methods model.begin_round and model.end_round. Model.act is now obsolete
* Added a bptk.train_simulation method which runs simulation in episodes to allow training
* Small changes to the scenario definition syntax (JSON) for agent-based models
* Renamed the progressBar attribute of bptk.plot_simulation to progress_bar

### 0.6.3  

* Bug fix to bptk.run_simulations: the parameter AgentPropertyTypes was not handled correctly


### 0.6.2 

* Bug fix:  all agents were receiving the same properties object on initialization. Fixed by using Python's copy module. Each agent now receives a deep copy. Changes on one agent's properties do not interfere with changes on other agents' properties anymore.

### 0.6.1

* Bug fix: valuate_function was renamed to evaluate_equation in 0.6.0 , but not everywhere

### 0.6.0

* New functionality: you can now define a function in Python and use it within an SD model.

### 0.5.3

* First Release of documentation for Readthedocs. Check it out at: http://bptk.transentis.com
* You can now run AB models with a custom data_collector without plotting using "run_simulations()". This allows you to create custom data collectors that do not emit data back to BPTK, e.g. a streaming data collector
* Fixed an issue regarding absolute and relative imports in the Model class
* Various improvements to ABM module

### 0.5.2

* Models now have their own act method, to allow updating of dynamic properties.
* Internal changes to event handling in agents
* Fixed a bug regarding lookup handling.

### 0.5.1

* Bugfix for ABM module

### 0.5

* Large improvements for the Agent Based Modeling component! Main changes:
* Agents can now have properties.
* Agent properties can be set via the JSON config file. Properties can be accessed using dot-notation, i.e. agent.property
* The necessary property get/set methods are added automatically using Python metaprogramming facilities - this keeps the code that needs to implemented by the modeler to a mimimum.The same is true of model properties - these can now also be accessed using dot-notation.
* Statistics for properties are automatically collected and can be plotted using the plot_scenarios method. Currently the following statistics are collected: total, min, max, mean.

### 0.4.1

* Bugfix in Model class: dt param was not properly instantiated

### 0.4.0

* Framework for Agent Based models
* Framework for defining System Dynamics models in code with less effort. No need for complex recursive calls anymore. Simply define your equations as easy as element.equation = element * anotherElement. Example in the tutorial!
* Simplify API: use comma-seperated values to specify scenarios/scenario managers or equations, no need for Python lists anymore!
* Many more internal improvements under the hood.

### 0.3.7

* PULSE functions can now be defined within Jupyter environment. Just use the new pulse_function_create(scenarios,scenario_managers) method and be surprised.
* Cleaner method for strategy simulation. Now running stepwise, not using a complex while loop anymore. Improves readability tremendously!
* Optimize imports using __init__.py properly.
* Correct handling of decimal dt values within simulator.

### 0.3.6.1

* Bugfix to reduce size of the package

### 0.3.6

* Now interpreting strategies that modify at '0' as constants values and overwrite the constants
* Use DT of simulation model

### 0.3.5.5

* Fixed a bug that prevented from plotting properly when giving multiple scenario managers where one of them did not store the given scenario name

### 0.3.5.4

* Monitoring of Scenario JSON files:
* Reload scenarios upon change (also works if Scenario manager spreads over multiple files)
* Find added scenarios
* Merge base values spread over multiple files

### 0.3.5.3

* horizontal lines in graphs to improve readability
* Improvements to readme file
* Small bug fixes