# Business Prototyping Toolkit for Python 

__System Dynamics and Agent-based Modeling in Python__

The Business Prototyping Toolkit for Python (BPTK-Py) is a computational modeling framework that enables you to build simulation models using System Dynamics (SD) and/or agent-based modeling (ABM) natively in Python and manage simulation scenarios with ease.

Next to providing the necessary SD and ABM language constructs to build simulation models directly in Python, the framework also includes a compiler for transpiling System Dynamics models conforming to the XMILE standard into Python code.

This means you can build models in a XMILE-compatible visual modeling environment (such as [Stella](http://www.iseesystems.com) or [iThink](http://www.iseesystems.com)) and then use them _independently_ in an Python environment.

The best way to get started with BPTK-Py is to read the [Quickstart](https://bptk.transentis.com/quickstart/quickstart.html) that is part ot the extensive [online documentation](http://bptk.transentis.com). The Quickstart provides a _single page_ overview of all the computational modeling techniques supported by BPTK.
  

## Main Features

*   The objective of the framework is to let the modeller concentrate on building simulation models by providing a seamless interface for managing model settings and scenarios and for plotting simulation results.
*   The BPTK-Py framework supports System Dynamics models in XMILE Format, native SD models using a domain-specific language for System Dynamics (SD DSL) and native Agent-based models. You can also build hybrid SD-ABM-Models natively in Python.
*   All plotting is done using [Matplotlib](http://www.matplotlib.org).
*   Simulation results are returned as [Pandas dataframes](http://pandas.pydata.org) and thus can easily be used for analytics.
*   Model settings and scenarios are kept in JSON files. These settings are automatically loaded by the framework upon initialization, as are the model classes themselves. This makes interactive modeling, coding and testing very painless, especially if using the Jupyter notebook environment.

## Getting Help

BPTK-Py is developed and maintained by [transentis labs](http://www.transentis.com/business-prototyping-toolki/en/). 

The first place to go to for help and installation instructions is the [online documentation](http://bptk.transentis.com). 

The [Quickstart](https://bptk.transentis.com/quickstart/quickstart.html) provides a _single page_ overview of all the modeling techniques supported by BPTK. 

The online documentation is generated from an extensive set of Jupyter notebooks, the __BPTK Tutorial__. The tutorial is available as a [git repository](https://github.com/transentis/bptk_py_tutorial) on GitHub. 

Our [Business Prototyping Toolkit Meetup Group](https://www.transentis.com/business-prototyping-toolkit-meetup/en/) gathers online regularly. This is a good place to see BPTK in action, ask questions and suggest new features. We record every session and you can _view past recordings_ on the [meetup homepage](https://www.transentis.com/resources/business-prototyping-toolkit-meetup).

We used BPTK to build our implementation of the infamous [Beer Distribution Game](https://beergame.transentis.com).

Our [beergame repository](https://github.com/transentis/bptk_py_tutorial/tree/master/model_library/beergame) contains Jupyter notebooks that analyse the Beergame in-depth and also provides XMILE, SD DSL and Agent-based versions of the Beergame.

For any questions our suggestions you have regarding BPTK, please contact us at: [support@transentis.com](mailto:support@transentis.com).

## Changelog

### 1.8.0
* BPTKServer: Add new endpoint start-instances that starts multiple instances in one goo

### 1.7.6
* BPTK: Improve handling of floating point numbers when using small DTs
* ScenarioManagerSD: Fixed an issue that caused models with biflows to be cloned incorrectly

### 1.7.5
* BPTK: Fix that caused a crash when using multiple scenario files for hybrid models

### 1.7.4
* BPTK: Fix bug in reset_scenarios for Hybrid Scenario Managers
### 1.7.3
* BPTK: Update dependencies of Pandas/Matplotlib/Sympy/Parsimonious/Pyyaml/Xlsxwriter/Jinja2/Requests/Jsonpickle/Flask
* Successfully tested with Python 3.11

### 1.7.2
* BPTK: Fix imports of SimpleDashboard class
* BPTK: Update dependency of Scipy, Numpy and Pyyaml
### 1.7.1
* BPTK: reset_cache now also resets the data collector in agent based models
* BPTK: reset_cache calls the reset_cache method on all agents
* BPTK: agents now have a reset_cache method that can be used to reset agent state
* BPTK: Updated dependency on ipywidgets to 8.0.4

### 1.7.0
* BPTK Server: Remote authorization for root, full-metrics and metrics endpoints
* BPTK Server: Add /healthy endpoint
* BPTK Server: stop-instance and load-state are now POST resources
* Bug Fix: Remove debug print message

### 1.6.6

* BPTK: Defer import of matplotlib and ipywidgets until they are needed

### 1.6.5

* BPTK: Hybrid scenarios can now be spread accross multiple scenario files
* BPTK: Remove filename attribute from hybrid scenario manager as it is obsolete
* BPTK: Scenario definitions for SD DSL scenarios now accept a runspecs setting to override starttime, stoptime and dt
* BPTK: begin_session now accepts a settings parameter to override scenario settings
* BPTK Server: begin_session now accepts a settings parameter to override scenario settings

### 1.6.4

* BPTK Server: Simplified bearer token authentication
### 1.6.3

* BPTK Server: Added optional bearer token authentication
### 1.6.2

* BPTK Server: Fixed unsafe external state adapter code
* BPTK Server: start_instance now returns correct content type

### 1.6.1

* SimpleDashboard: Deleted superfluous import statement
* bptk: Small improvements to documentation

### 1.6.0

* BPTK Server: The run_step methods now also support agent-based models
* BPTK Server: A new endpoint streams_steps runs all the steps of a model and streams the results, especially useful for models that run for a long-time.
* SimpleDashboard: A new utility class that allows easy creation of dashboards based on Jupyter Widgets.

### 1.5.3

* BPTK Server: Since v 1.5.0, BPTK Server requires a Python version >= 3.9. The package now informs the user about this upon import. Other parts of the BPTK framework should work fine with older Python3 versions.

### 1.5.2

* BPTK Server: Added file adapter as a concrete example of an external adapter
* BPTK: Improve cleanup of resources when bptk instance is destroyed

### 1.5.1

* BPTK Server: Improvements to the new state externalisation feature
* BPTK Server: Improve cleanup of resources when an instance times out 

### 1.5.0

* SD DSL: Added a new module class that makes it easy to structure large models
* BPTK Server: Add new endpoints to allow externalising the instance state
* BPTK Server: Changed the default timeout for equations for instances to 12h

### 1.4.3

* SD DSL: fix to delay function

###  1.4.2

* Small bugfixes in prometheus metrics.

###  1.4.1

* BPTK: Fix to plot_lookup
* BPTK Server: 'flat' version of session results
* SD DSL: small changes to SD functions pulse and delay to make them more robust.

### 1.4.0

* BPTK Server: add metrics endpoint
* SD DSL: fixed missing imports that caused some sddsl functions to throw an exception

### 1.3.12

* BPTK Server: fixed an issue that could lead to race conditions leading to server crashes

### 1.3.11
* BPTK Server: add a keep-alive method to keep instances from timing out
* BPTK Server: start-instances now accepts a timeout structure so that instance timeouts can be set flexibly.
* BPTK Server: fixed an issue that could lead to race conditions leading to server crashes
* XMILE: fixed an issue regarding lookups (graphical functions) that do not contain values on the x-axis

### 1.3.10
* BPTK: fixed an issue in train_scenarios which caused an exception in recent versions of bptk-py

### 1.3.9
* XMILE: Array arithmetic (such as array multiplication,...) within array functions such as SUM is now handled correctly.

### 1.3.8
* XMILE: Arrayed variables that have non-arrayed inputs with "apply to all" set are now handled correctly

### 1.3.7
* XMILE: Ensure the startime and stoptime in transpiled XMILE models are floating point values (e.g. 1.0, not 1)
* XMILE: Top level variables in a model that contains modules are now referenced correctly from submodules
* XMILE: Nested modules are now handled correctly
* XMILE: Array dimensions of length <3 are now handled correctly

### 1.3.6
* Add new method session_results to bptk and corresponding endpoint session-results to Bptk server that allows the session results so far to be retrieved.

### 1.3.5
* Fixed an issue that caused bptk-server to crash if start-instance was called after a previous instance had timed out

### 1.3.4
* Small improvements to the XMILE/SMILE parser regarding element names that include special characters and regarding operators surrounded by newlines.
### 1.3.3
* Return message from end-session resource now correctly reads "session terminated"
### 1.3.2
* Rename package due to issues with test pypi

### 1.3.1
* Add missing package in setup.py

### 1.3.0
* Fix bug in run_scenarios that arose with multiple scenario managers and when return_format was json or dict
* Add begin_session, end_session and run_step methods to bptk
* Add agent endpoint to BptkServer
* BptksServer now takes a bptk_factory function instead of a bptk object in its constructor
* Add start-instance endpoint to BptkServer
* Add begin-session, end-session and run-step endpoint to BptkServer

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
