# Business Prototyping Toolkit for Python 

__System Dynamics and Agent-based Modeling in Python__

The Business Prototyping Toolkit for Python (BPTK-Py) is a computational modeling framework that enables you to build simulation models using System Dynamics (SD) and/or agent-based modeling (ABM) and manage simulation scenarios with ease.

Next to providing the necessary SD and ABM language constructs to build models directly in Python, the framework also includes a compiler for transpiling  System Dynamics models conforming to the XMILE standard into Python code.

This means you can build models in a XMILE-compatible visual modeling environment (such as [Stella](http://www.iseesystems.com) or [iThink](http://www.iseesystems.com))) and then use them _independently_ in an Python environment.

The best way to get started with BPTK-Py is our tutorial, which contains a number of simulation models and Jupyter notebooks that illustrate how to use BPTK. You can clone or download the tutorial from our [git repository](https://github.com/transentis/bptk_py_tutorial/) on Github.

## Main Features

*   The objective of the framework is to let the modeller concentrate on building simulation models by providing a seamless interface for managing model settings and scenarios and for plotting simulation results.
*   The BPTK-Py framework supports System Dynamics models in XMILE Format, native SD models using a domain-specific language for System Dynamics (SD DSL) and native Agent-based models. You can also build hybrid SD-ABM-Models natively in Python.
*   All plotting is done using [Matplotlib](http://www.matplotlib.org).
*   Simulation results are returned as [Pandas dataframes](http://pandas.pydata.org) and thus can easily be used for analytics.
*   Model settings and scenarios are kept in JSON files. These settings are automatically loaded by the framework upon initialization, as are the model classes themselves. This makes interactive modeling, coding and testing very painless, especially if using the Jupyter notebook environment.

## Getting Help

BPTK-Py is developed and maintained by [transentis labs](http://www.transentis.com/business-prototyping-toolki/en/). 

The first place to go to for help and installation instructions is the [online documentation](http://bptk.transentis.com).

Our [Introduction to the Business Prototyping Toolkit](https://github.com/transentis/bptk_intro/blob/master/intro_to_bptk.ipynb) provides a "single notebook" overview of all the modeling techniques supported by BPTK. 

You should also study the BPTK-Py tutorial, which contains the sample models and Jupyter notebooks referenced in the online documentation. You can clone or download the tutorial from our [git repository](https://github.com/transentis/bptk_py_tutorial). 

We have also set up a [meetup group](https://www.transentis.com/business-prototyping-toolkit-meetup/en/) that gathers online monthly. This is a good place to see BPTK in action, ask questions and suggest new features.

For any questions you have regarding BPTK, please contact us at: [support@transentis.com](mailto:support@transentis.com).

## Changelog

### 1.2.1
* Improve documentation
* Bugfix for bptk.export_scenarios

### 1.2.0
*   Major tidy up of the bptk API, including a number of breaking changes. In particular the run_simulation method has been renamed to run_scenarios and reset_simulation_model was renamed to reset_scenario_cache. A number of rarely used methods have been removed.
*   Documentation improved and extended.
*   Internal refactoring.

### 1.1.27
*   Fix bug in XMILE compiler regrading parsing of names that start with a keyword

### 1.1.26

*   Fix bug in XMILE compiler that causes parsing of if/then/else structures to fail under some circumstances
*   Fix bug in XMILE pulse function that causes the function to misbehave in some circumstances
*   Fix bug in XMILE previous function that causes the function to misbehave in some circumstances

### 1.1.25
*   Improve error handling and fault tolerance on BptkServer

### 1.1.24
*   Update to BptkServer internals

### 1.1.23
*   Add a new experimental feature that allows REST APIs for simulation models to be set up easily.

### 1.1.22
*   SD DSL: Add python power operator (**) to all SD DSL operators
*   XMILE: Ensure SAFEDIV works in complex expressions

### 1.1.21
*   Improve handling of SAFEDIV in SD compiler

### 1.1.20
*   Fix for the SD compiler regarding dimension names usage

### 1.1.19
*   Little fix regarding the SD-Compiler

### 1.1.18
*   Improvement of SD compiler: Support for empty initial value of ``DELAY`` function. Support for dimension names as arguments for functions (e.g. ``SIZE(<dimension>)``)

### 1.1.17
*   Improvement of Extended Data Collector: Renamed to Agent Data Collector and code optimizations

### 1.1.16
*   Bugfix for the plotting component that solves compatibility issues with newer versions of matplotlib

### 1.1.15
*   New dataCollector for retrieving agent-wise data (Refer to [BPTK-Py Tutorial](https://github.com/transentis/bptk_py_tutorial) for more info)

### 1.1.14
*   Fixed a bug in the interactive scenario component that caused scenarios being plotted multiple times
*   Fixed a bug that caused the SD operator ``delay`` to not accept floating point values and fixed a bug that caused the same to be parsed incorrectly in some cases.

### 1.1.13
*   Fixed a bug in the XMILE Converter that prevented the SAFEDIV operator to be parsed correctly

### 1.1.12
*   SD-DSL: Fixed a bug that caused converter equations (subtraction and division) to be computed incorrectly.

### 1.1.11
*   SD-DSL: Added support for right-hand side addition and subtraction to support equations such as ``converter.equation = 1 - b``
*   Visualisation for SD-DSL elements now follows conventions to work properly with Matplotlib 3.3+ 

### 1.1.10
*   Visualisation using matplotlib now follows conventions to work properly with Matplotlib 3.3+ 

### 1.1.9
*   SD-DSL: System Dynamics element such as converters did not implement comparison operators (">", "<", ">=", "==", "!="). They have been added

### 1.1.8 
*   Another bugfix for series renaming. Simplified the code for renaming by using Pandas' standard method ``rename``

### 1.1.7
*   Bugfix for ``plot_scenarios``: The ``series_names`` replacer did not work properly for when only one scenario manager / scenario is given.

### 1.1.6
*   Bugfix for XMILE compiler: A little error in the parser prevented certain models being parsed correctly
*   Bugfix for ``plot_scenarios``: The new error messages showed up for Agent based models although the scenarios were present

### 1.1.5
*   The XMILE compiler is a great tool that handles model conversion from XMILE SD Models to Python. For compatibility and readability, we change the equation names to camelCasing upon conversion. This might be confusing for some users. That's why we decided to give you a new function call that lists all equations for System Dynamics Models. Simply run ``bptk.list_equations()`` (optionally add scenario manager(s) and scenario(s)) and get an overview over available model elements. More details [in our documentation](https://bptk.transentis.com/en/latest/docs/xmile/how-to/how_to_working_with_XMILE/how_to_working_with_XMILE.html).
*   Improved error messages. In previous versions, a long error trace was printed when an equation was not found. Now you get a neat error message output wiht hints as to why the plotting failed.
*   If an equation / scenario / scenario manager is not found, ``BPTK_Py`` gives hints on which similar equations / scenarios / scenario managers might be available for use.
*   Register XMILE models without having to follow the directory structure: ``BPTK_PY`` scans the ``scenarios`` folder upon startup to find new scenario managers and XMILE / ABM models. We developed a simpler way to add simulation models during runtime without having to add scenarios beforehand: ``bptk.register_model("<path_to_itmx_stmx>","<modelname>")``. You can then easily simulate the model just as you're used to.

### 1.1.4
XMILE equations make use of double-quote enclosed identifiers in case it actually looks like a function call. For example, ``100*"Identifier(enclosed)"`` is a valid equation where one element (stock/flow) is called ``Identifier(enclosed)``. However, we were not able to parse this, until now.
Update BPTK-Py using the new update mechanism: [documentation](https://bptk.transentis.com/en/latest/docs/usage/installation.html#keeping-bptk-py-up-to-date)

### 1.1.3
We figured that the update mechanisms via ``pip`` might be confusing sometimes, especially for non-programmers. This is 
why we decided to implement an update mechanism. Details are available in the [documentation](https://bptk.transentis.com/en/latest/docs/usage/installation.html#keeping-bptk-py-up-to-date)

### 1.1.2
*   Bugfix to (XMILE) SD Compiler: Added support for array expressions within function calls. We had trouble with equations that contain another expression within a function call. E.g. ``DELAY(arrayedElement[1,2]*5, 1, 1)`` was not supported.
*   Improvement to (XMILE) SD Compiler: Removed replacement of currency symbols (``€``, ``$`` etc.) and percentage signs with abbreviations. We had implemented this in earlier releases but figured it leads to confusion with modellers.

### 1.1.1 
*   The SD DSL now differentiates flows and biflows. Simply add a biflow using ```biflow = model.biflow(<name>)```.
*   The SD DSL now supports: RANDOM, IF, NOT, AND, OR, NAN, SQRT, ROUND and all trigonometric and statistical builtins you know from XMILE. Furthermore the operators support Comparison Operators (>, <, >=, <=, ==, !=) and the modulo operator (x % y). 
    *   RANDOM: ``converter.equation = sd.Random(<min>, <max>)`` draws a uniformly distributed float random number between <min> and <max>
    *   ROUND: ``converter.equation = sd.Round(sd.random(0,1),2))`` rounds a random number between 0 and 1 to a 2 digit float
    *   IF: ```converter.equation = sd.If( <condition>, <then> , <else> ) ``` corresponds to ```IF <condition> THEN <then> ELSE <else>```. Each term inside the IF clause can be a SD term again. Example for a valid If clause: ``equation = sd.If(sd.time()>10,sd.random(1,2), 100)`` 
    *   AND/OR: ```sd.Or(<left hand side>, <right hand side>)``` and ```sd.And(<left hand side>, <right hand side>)``` for multiple conditions
    *   NOT: Use ```sd.Not(<condition>)``` for "not" conditions, e.g:  ```sd.If(sd.Not(sd.time()>10), 1, 0 )``` 
    *   NAN / INF / PI: ``sd.nan()`` returns a NAN value, ``sd.Inf()`` gives you the infinity value, ```sd.pi()``` returns the number pi.
    *   SQRT: ``sd.sqrt(<value of function>)`` computes the square root
    *   SIN / TAN / COS: ``sd.sin(x) / sd.cos(x) / sd.tan(x)`` for sinus, cosinus or tangent of x (radians) and of course we also support ARCCOS, ARCSIN, ARCTAN with the same syntax
    *   SINWAVE / COSWAVE: ``sd.sinwave(amplitude,period)`` / ``sd.coswave(amplitude,period)`` to generate sine / cosine waves with given amplitude and period
    *   More documentation and how to use the __statistical (random numbers from various distributions) and trigonometric operators__ can be found in our [online documentation](https://bptk.transentis.com/en/latest/docs/sd-dsl/in-depth/in_depth_sd_dsl_functions/in_depth_sd_dsl_functions.html)
*   We fixed a bug that caused BPTK to crash when an XMILE model was updated while BPTK was monitoring it
*   We fixed SINWAVE in the XMILE transpiler and added support for COSWAVE

### 1.1.0
*   We are supporting all XMILE operators now. Note that random numbers with seed are **never** the same as when using Stella Architect's seed! This is due to different random number generators in Python and Stella. We neither support the min / max arguments for the random number operators. Refer to the [documentation](https://bptk.transentis.com/en/latest/docs/usage/limitations.html))
*   RUNCOUNT and SENSIRUNCOUNT are not supported and support is not planned.

### 1.0.2
*   Bugfix release: Better support for multidimensional arrays

### 1.0.1

*   Bugfix release: Fixed an issue with plot_lookup 

### 1.0.0

*   SD Compiler: Added new operators
    *   Arrays and Array Operators (MIN, MAX, SUM, MEAN, SELF, SIZE, PROD)
    *   Statistical operators (COMBINATIONS, BETA, BINOMIAL, FACTORIAL, GAMMA, GAMMALN, EXPRND, GEOMETRIC)
    *   Trigonometric operators (ARCSIN, ARCCOS, ARCTAN)
*   The ``plot_scenarios`` API now supports array calls such as ``stock[*]`` or ``stock[dim1,dim2]``
*   SD DSL: ABS, DT, PULSE, STARTTIME, STOPTIME

### 0.9.0
We removed the JavaScript SD Compiler and programmed a whole new transpiler that converts XMILE to Python __in Python__ to obtain large performance increases and stability when working with XMILE models. No longer you will need Node.js for transpiling models into Python.

*   With the new XMILE Transpiler, we also ship support for the following XMILE operators: SMTH1, TREND

### 0.8.9

*   Added new operators for the SD DSL along with in depth documentation that shows how to use the functions: DELAY, EXP, SMOOTH, STEP, TREND.
*   The SD DSL is now stricter, all constant values must be floats, ints are no longer accepted.
*   Added a new ``register_model`` method to bptk, to ensure quick setup of scenario managers and scenarios.
*   Internal optimizations and bug fixes.

### 0.8.8

*   Extended the `export` function, it now also exports data to allow comparison between scenarios

### 0.8.7

*   Fixed an error in requirements.txt

### 0.8.6
*   Added a new export method to the bptk class to simplify the export of simulation results.
*   Added some new methods to the bptk class to allow easy access to scenarios - accessing the scenarioManagerFactory is now no longer necessary.
*   Updated and simplified the documentation.

### 0.8.5
*   System Dynamics DSL: Extended the operator overrides, to ensure stocks can have more than two inflows or outflows.

### 0.8.4
*   Bug fix to bptk.add_scenario that occurred when adding a new scenario to an existing scenario manager

### 0.8.3

*   Little fix for requirements.txt

### 0.8.2
*   We are working on making BPTK-Py even more flexible. The Scheduler interface now has an attribute ``running``. You can modify this during runtime in order to cancel long-standing jobs. This may be useful for third-party applications that use BPTK-Py and need to be able to cancel jobs.
*   The YAML Model parser now supports custom Model files for ABM simulations!

### 0.8.1
*   Bugfix for agent: Property type can also be of type "Agent".

### 0.8.0
*   Fixed an annoying bug: We forgot to include the threads that watch the scenario JSON files into the ``bptk.destroy()`` method. Now it runs properly and once executed all monitors will stop monitoring.
*   YAML Support! Now you can easily define your models using YAML notation. This is much simpler than JSON. 
*   As a perk, you do not need the model implementation for AB models anymore. When using YAML notation, BPTK will create the necessary objects without requiring code. So now you can concentrate onyour agents without the need of registering agent factories!
*   Choose Data collector class within the model file: The YAML file now supports the directive ``datacollector``. Here you can link to custom data collector classes. Try the included ones such as ``BPTK_Py.abm.CSVDAtaCollector``. Using custom data collectors reduces simulation time tremendously as ``BPTK-Py`` will not use its slow mechanism to create dataframes anymore.
*   We also included a meta model creator feeding on parser results. You only need to implement the model parser and feed the model creator. The model creator then builds the actual simulation model. This way, you can add modelling languages easily!


### 0.7.0
*   Added Delayed Events in Agent based modelling. Now each agent can send events that trigger in the future. Instantiate a ```DelayedEvent``` and set the ``trigger_in`` parameter with the number of periods to wait before trigger. The framework will make sure to trigger the event at the right time.
*   Multithreading for scenario execution: Speeding up multi-scenario simulation siginificantly by using one thread per scenario
*   Added ``agent_type`` as optional parameter for Agent. Now you do not need to add the agent type in the initialize method anymore if that is what you prefer
*   Better handling of progress bar in ABM simulation using ``ipywidgets.Out`` to make bar disappear after executiob. Removed running scheduler as thread because this is not required here.
*   ABM: If you still have scenario manager files but deleted the code, execution will not be stopped anymore but faulty scenario is skipped with an Error message. 


### 0.6.6
*   Little improvements and bugfixes to data collectors. For Kinesis, you will be warned if ``boto`` (required for AWS access) is not installed as it is not a package dependency.

### 0.6.5
*   We want to make data analysis easy for you. Hence, we added data collectors as standard for model output: ``CSVDataCollector`` outputs each agents' events to CSV, one file per agent. ``KinesisDataCollector`` outputs the agent statistics to Kinesis, an AWS service. For both, the data output is event-wise

### 0.6.4

*   New methods model.begin_round and model.end_round. Model.act is now obsolete
*   Added a bptk.train_simulation method which runs simulation in episodes to allow training
*   Small changes to the scenario definition syntax (JSON) for agent-based models
*   Renamed the progressBar attribute of bptk.plot_simulation to progress_bar

### 0.6.3  

*   Bug fix to bptk.run_simulations: the parameter AgentPropertyTypes was not handled correctly


### 0.6.2 

*   Bug fix: all agents were receiving the same properties object on initialization. Fixed by using Python's copy module. Each agent now receives a deep copy. Changes on one agent's properties do not interfere with changes on other agents' properties anymore.

### 0.6.1

*   Bug fix: valuate_function was renamed to evaluate_equation in 0.6.0 , but not everywhere

### 0.6.0

*   New functionality: you can now define a function in Python and use it within an SD model.

### 0.5.3

*   First Release of documentation for Readthedocs. Check it out at: http://bptk.transentis.com
*   You can now run AB models with a custom data_collector without plotting using "run_simulations()". This allows you to create custom data collectors that do not emit data back to BPTK, e.g. a streaming data collector
*   Fixed an issue regarding absolute and relative imports in the Model class
*   Various improvements to ABM module

### 0.5.2

*   Models now have their own act method, to allow updating of dynamic properties.
*   Internal changes to event handling in agents
*   Fixed a bug regarding lookup handling.

### 0.5.1

*   Bugfix for ABM module

### 0.5

*   Large improvements for the Agent Based Modeling component! Main changes:
*   Agents can now have properties.
*   Agent properties can be set via the JSON config file. Properties can be accessed using dot-notation, i.e. agent.property
*   The necessary property get/set methods are added automatically using Python metaprogramming facilities - this keeps the code that needs to implemented by the modeler to a mimimum.The same is true of model properties - these can now also be accessed using dot-notation.
*   Statistics for properties are automatically collected and can be plotted using the plot_scenarios method. Currently the following statistics are collected: total, min, max, mean.

### 0.4.1

*   Bugfix in Model class: dt param was not properly instantiated

### 0.4.0

*   Framework for Agent Based models
*   Framework for defining System Dynamics models in code with less effort. No need for complex recursive calls anymore. Simply define your equations as easy as element.equation = element * anotherElement. Example in the tutorial!
*   Simplify API: use comma-seperated values to specify scenarios/scenario managers or equations, no need for Python lists anymore!
*   Many more internal improvements under the hood.

### 0.3.7

*   PULSE functions can now be defined within Jupyter environment. Just use the new pulse_function_create(scenarios,scenario_managers) method and be surprised.
*   Cleaner method for strategy simulation. Now running stepwise, not using a complex while loop anymore. Improves readability tremendously!
*   Optimize imports using __init__.py properly.
*   Correct handling of decimal dt values within simulator.

### 0.3.6.1

*   Bugfix to reduce size of the package

### 0.3.6

*   Now interpreting strategies that modify at '0' as constants values and overwrite the constants
*   Use DT of simulation model

### 0.3.5.5

*   Fixed a bug that prevented from plotting properly when giving multiple scenario managers where one of them did not store the given scenario name

### 0.3.5.4

*   Monitoring of Scenario JSON files:
*   Reload scenarios upon change (also works if Scenario manager spreads over multiple files)
*   Find added scenarios
*   Merge base values spread over multiple files

### 0.3.5.3

*   horizontal lines in graphs to improve readability
*   Improvements to readme file
*   Small bug fixes