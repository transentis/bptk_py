# Business Prototyping Toolkit for Python

[![Coverage Status](https://coveralls.io/repos/github/transentis/bptk_py/badge.svg)](https://coveralls.io/github/transentis/bptk_py)

__System Dynamics and Agent-based Modeling in Python__

The Business Prototyping Toolkit for Python (BPTK-Py) is a computational modeling framework that enables you to build simulation models using System Dynamics (SD) and/or agent-based modeling (ABM) natively in Python and manage simulation scenarios with ease.

Models run on a compiled Rust engine where speed matters, and on pure Python everywhere else — including inside a browser, on WebAssembly.

The framework also includes a compiler for transpiling System Dynamics models conforming to the XMILE standard into Python code, so a model built in a visual modeling environment such as [Stella](https://www.iseesystems.com) or [iThink](https://www.iseesystems.com) can be used _independently_ in a Python environment.

The best way to get started with BPTK-Py is to read the [Quickstart](https://bptk.transentis.com/quickstart/quickstart.html) that is part of the extensive [online documentation](https://bptk.transentis.com). The Quickstart provides a _single page_ overview of all the computational modeling techniques supported by BPTK.

**Contents:** [Main Features](#main-features) · [Installation](#installation) · [Getting Help](#getting-help) · [Changelog](#changelog)


## Main Features

*   The objective of the framework is to let the modeller concentrate on building simulation models by providing a seamless interface for managing model settings and scenarios and for plotting simulation results.
*   **System Dynamics, agent-based and hybrid models.** Native SD models using a domain-specific language for System Dynamics (SD DSL), including multidimensional models; native agent-based models; and hybrid SD-ABM models, all in Python.
*   **A compiled Rust engine.** SD models run on a Rust engine that ships pre-compiled inside the wheel — nothing to install, nothing to configure. Choose it per run, per session or per server; anything it cannot express falls back to the Python engine automatically. See [Execution Backends](https://bptk.transentis.com/concepts/execution_backends/execution_backends.html).
*   **Runs in a browser.** BPTK installs into [Pyodide](https://pyodide.org) and runs on WebAssembly, so a model can be published as a page rather than as a notebook someone has to install first. The Python engine is the one that runs there.
*   **XMILE models become Python.** The compiler transpiles models built in Stella or iThink, and is installed with the `xmile` extra — see [Installation](#installation).
*   All plotting is done using [Matplotlib](https://www.matplotlib.org), which is installed with the `plotting` extra — see [Installation](#installation).
*   Simulation results are returned as [Pandas dataframes](https://pandas.pydata.org) and thus can easily be used for analytics.
*   Model settings and scenarios are kept in JSON files. These settings are automatically loaded by the framework upon initialization, as are the model classes themselves. This makes interactive modeling, coding and testing very painless, especially in a reactive notebook environment such as [marimo](https://marimo.io).

## Installation

BPTK-Py requires Python 3.12 or later.

```bash
pip install bptk-py
```

That gives you everything needed to build and simulate models: the SD DSL, agent-based modeling, hybrid models, and the Rust execution engine. The engine ships pre-compiled inside the wheel — there is no Rust toolchain to install and nothing to configure.

Capabilities that a modeller does not always need are available as extras:

| Install | Adds |
|---|---|
| `pip install bptk-py[plotting]` | Plotting via [Matplotlib](https://www.matplotlib.org) — `plot_scenarios`, `Element.plot`, `plot_lookup` |
| `pip install bptk-py[xmile]` | The XMILE compiler, for models built in Stella or iThink |
| `pip install bptk-py[server]` | `BptkServer` and the Postgres and Redis state adapters |
| `pip install bptk-py[observability]` | Logging to [Pydantic Logfire](https://logfire.pydantic.dev) |

They combine: `pip install "bptk-py[plotting,xmile]"`. Note the quotes — some shells, zsh among them, treat the brackets as a filename pattern.

Using a capability without its extra raises an error naming the extra to install, so nothing fails silently.

## Getting Help

BPTK-Py is developed and maintained by [transentis labs](https://www.transentis.com).

The first place to go to for help and installation instructions is the [online documentation](https://bptk.transentis.com).

The [Quickstart](https://bptk.transentis.com/quickstart/quickstart.html) provides a _single page_ overview of all the modeling techniques supported by BPTK.

The online documentation is generated from an extensive set of [marimo](https://marimo.io) notebooks, and those notebooks are in this repository under `website-tutorial`. To run them yourself:

```bash
pip install -r website-tutorial/requirements.txt
marimo edit website-tutorial/quickstart/quickstart.py
```

Every notebook brings the models and scenario files it needs. The diagrams do not travel with them - they are on the website, where the same notebook is rendered with its figures, so a notebook opened locally shows a broken image where the website shows a diagram.

We used BPTK to build our implementation of the infamous [Beer Distribution Game](https://beergame.transentis.com).

If you want to build simulation models using a UI and AI, please check our [Metapad](https://www.metapad.ai) platform.

For any questions or suggestions you have regarding BPTK, please contact us at: [support@transentis.com](mailto:support@transentis.com).

## Changelog

### 3.3.0

* Breaking: Python 3.12 or later is required; tested on 3.12, 3.13 and 3.14
* Breaking: `sd.step(height, t)` switches at `t` instead of one timestep after it, as XMILE's STEP and Stella do - a model using it moves by one timestep
* Breaking: `sd.round` rounds a half away from zero on both engines, as the Rust engine did - the Python engine rounded half to even, so 2.5 came out as 2 there
* Breaking: a scenario that sets a stock as a constant raises `ValueError` - it used to freeze the stock at that value; set the constant its initial value refers to instead
* Breaking: a statistical builtin given an argument it does not accept returns NaN and logs one `[ERROR]` naming the element, the time and the values - now also `uniform` with min > max, `geometric` with p outside (0, 1] and `negbinomial` with p = 0
* Breaking: `run_scenarios()` and `plot_scenarios()` without a `backend` use the instance's `default_backend`, as `begin_session()` does - they used to run on Python regardless
* Breaking: `CSVDataCollector` writes one file per agent type with a row per agent and timestep, and the events to `events.csv` - it used to keep one file per agent holding only the last timestep
* Breaking: `begin_session()` takes no agent arguments any more - sessions run System Dynamics only, and the server's `/begin-session` answers 400 to an agent field that is not empty
* Breaking: `ScenarioManagerFactory.add_scenario()` and `create_scenario()` are gone - use `bptk.register_scenarios()` and `bptk.export_scenarios()`
* Feature: the Python engine detects a loop between elements in the same timestep and raises `CyclicDependencyError` naming it, as the Rust engine does
* Upgraded numpy from 2.4.6 to 2.5.3, scipy from 1.15.3 to 1.18.1, matplotlib from 3.10.3 to 3.10.8, tqdm from 4.67.1 to 4.70.1, xlsxwriter from 3.2.5 to 3.2.9 and psycopg from 3.3.2 to 3.3.6
* Bugfixes:
    * Both engines: `invnorm(p, stddev=s)` without a mean; NaN arguments to statistical builtins; lookup points in any order; a `delay` shorter than half a step. On Rust: modulo of a negative operand, `delay` without an initial value, times on a dt such as 0.3, refusing at load what used to crash it or be misread, the package version. On Python: pulses on such a dt
    * Scenarios: `register_scenarios`, a scenario's settings and `get_scenarios` no longer change what they were given; overriding one lookup table keeps the model's other tables; a file without a parser among the scenario files no longer drops every manager's base values; `reset_all_scenarios` and `get_scenario_names` read the configured `scenario_storage`; `export_scenarios`' time column
    * Equations and arrays: a misspelt equation reported in a session and raised by `Model.simulate` on Rust; a `KeyError` inside an equation no longer taken for a misspelt name; an arrayed element asked for by its own name reported with its cells instead of answered with zeros; setting up an array no longer quadratic in the model's size; an empty array or an invalid operand refused where written
    * Sessions and server: `progress()` counts from the start time; a session read back from external state no longer keys its results by number; `run-steps` and `stream-steps` report a failing step instead of answering 200; `stream-steps` saves a stateless session; every response carries the CORS header, a 401 a JSON content type; a user-defined function raising in a Rust step is a `RuntimeError`, as on the first step
    * Agent-based models: configured and run twice without `IndexError`; `train_scenarios` with a progress bar; `agents`, `agent_properties` and `agent_property_types` as comma strings; a model property's attribute value
    * Elsewhere: errors swallowed in a model module, a plotted equation or a scenario file reload are reported; the hybrid scenario manager names the import error of a missing model; an invalid log level is reported; a narrow plot keeps its title; a user-defined function defined again replaces the first; concurrent `to_json()` calls; a stochastic transpiled XMILE model is reproducible with a seed

### 3.2.0

* Breaking: `backend="rust"` raises `RustBackendError` when the model cannot run on the engine, instead of quietly computing it in Python. The message names the cause - the model, a compiled XMILE model, an installation without the engine, or an engine failure
* Breaking: assigning a single value to an element you gave a shape raises - an arrayed element holds no value beside its cells. It used to be accepted, and the engines then disagreed: Python computed the value, the Rust engine returned no such series at all
* Breaking: a server session that asks for the Rust engine and cannot have it answers 400 on its first step, naming the reason, instead of serving the session from the Python engine
* Feature: a model with user-defined functions runs on the Rust backend, calling back into Python at those nodes. Hybrid models and `elementwise=False` functions still need `backend="python"`
* Feature: a user-defined function says how it treats an arrayed argument - per index by default, or the whole array with `elementwise=False`. See [User Defined Functions](https://bptk.transentis.com/sd-dsl/sd_user_defined_functions/sd_user_defined_functions.html)
* Feature: a stock starts from any expression, not only from a number, a constant or a converter - `stock.initial_value = k * 2.0 + 5.0`
* Upgraded numpy from 2.3.1 to 2.4.6 and pandas from 2.3.0 to 3.0.6
* Bugfixes:
    * `stock.initial_value` accepts an integer
    * a stock's initial value read through a converter is the same on both engines
    * a user-defined function in a stock's equation reads its arguments at `t-dt`
    * the training progress bar advances once per scenario
    * a script that builds a `bptk()` ends by itself
    * a dotted model name is found with an absolute `scenario_storage` or another working directory

### 3.1.1

* Breaking: a `bptk()` carries its own plotting configuration. `bptk(configuration=...)` used to write into the package-wide one and restyle every plot in the process; an instance now starts from `BPTK_Py.plotting_config` and keeps what it was built with. `Element.plot()` and `plot_agent_stats()` have no instance in reach and still read the package-wide one
* Feature: the `dot` operation is now supported for named arrays as well - see [Array Dot](https://bptk.transentis.com/sd-dsl/sd_dsl_multidimensional/sd_dsl_multidimensional.html#array-dot) for the rules and examples
* Bugfixes:
    * a cold evaluation at a late timestep no longer raises `RecursionError`
    * the column names of `run_scenarios` and `plot_scenarios` no longer depend on earlier calls
    * a `delay` reads a duration that is a model element at every step, not once at `starttime`
    * a `delay` whose input is a constant overridden per step lags again, also in a resumed session

### 3.1.0

* Feature: arrayed (multidimensional) models run on the Rust backend - `backend="rust"`, a Rust-backed session and `/execute` all accept them, with results identical to the Python engine
* Feature: every operator carries arrayedness through, not only `+ - * /`: math functions, comparisons, `If`, `And`, `Or`, `Not`, `**`, `%`, `max`, `min`, `lookup`, `step`, `pulse` and `smooth`/`trend`/`delay` apply element-wise to a vector or a matrix, in either operand order, each index of a stateful function keeping its own history
* Feature: `Element.arr_max()` and `Element.arr_min()`, matching the other aggregations and the XMILE standard
* Feature: a range subscript in an XMILE model compiles and resolves - `SUM(leaving[1:2])`, and `SUM(leaving[north:middle])` for a named dimension, where the range is the slice between the two labels in the order the dimension declares them. The generator used to raise `Cannot parse expression` on the range, and a named range dropped its dimension and read as `0.0`
* Feature: arrayed biflows - `setup_vector` and friends work on a `Biflow`, so a level that both rises and falls can be one element per index instead of a pair of flows
* Bugfixes:
    * an arrayed expression no longer yields zeros or raises `AttributeError` - math functions, comparisons, `If`, `**`, `%`, `2.0 * v`, `3.0 + v`
    * assigning a bare arrayed element as an equation works for every element type; arrayed setup on a type that does not support it raises
    * assigning an element to a `Constant` raises the documented error
    * `Model.to_json()` serializes an arrayed model
    * `%` groups a compound operand and accepts a number on its left
    * `arr_sum` and `arr_prod` reject a `dimensions` argument short of the array's depth with a clear error

### 3.0.3

* Breaking: `register_scenario_manager` leaves an already registered manager untouched and logs an error - it used to drop the model but still merge the scenarios passed with it, so a new scenario ran against the model the caller had just replaced. Use `register_scenarios` to add scenarios, or `reset_all_scenarios` to start over
* Breaking: the plot settings live in one central configuration that every plot method reads, applied around each drawing call instead of being written into the global `plt.rcParams` when a `bptk()` is constructed - charts drawn outside BPTK are no longer restyled, and `Element.plot()` looks the same whether a `bptk()` exists. `configuration` passed to the constructor writes into that central configuration, so it applies to every plot in the process; `BPTK_Py.plotting_config.reset()` returns to the defaults
* Breaking: removed the configuration keys `interactive`, `bptk_Py_module_path` and `sd_py_compiler_root`, none of which was read by anything
* Feature: `plot_scenarios`, `plot_lookup`, `Element.plot` and `visualizer.plot` take `matplotlib_rc_settings` to style a single plot - laid over the central configuration for that one call, which is left unchanged
* Upgraded dependencies: PyO3 0.29.2 in the wheel, Flask 3.1.3 in the `server` extra - both for published advisories, neither changes an API
* Bugfixes:
    * `run_scenarios` with `agents` but without `agent_states` counts every state the agent has
    * `begin_session` with an agent-based scenario manager says that sessions run System Dynamics only
    * `begin_session` reports a scenario or scenario manager name that matches nothing
    * `train_scenarios` stops when an argument is passed without the one it depends on
    * `RedisAdapter` compresses session state when `compress` is set
    * compressed session state keeps its step numbers
    * `Element.plot(format="axes")` leaves no figure in matplotlib's global registry
    * importing the XMILE code generator raises no `SyntaxWarning`
    * `figure.figsize` and `lines.linewidth` set through `matplotlib_rc_settings` reach the chart

### 3.0.2

* Feature: `format="plot" | "axes" | "df"` on `Model.plot_lookup()` and `bptk.plot_lookup()`, matching `Element.plot()` and `plot_scenarios()`
* Bugfixes:
    * `plot_scenarios()` logs and returns `None` for a run without rows
    * fan-out runs in sequence under Emscripten
    * `format="axes"` leaves no figure in matplotlib's global registry
    * `Model.reset()` resets the agent id counter
    * `list_equations()` prints converters and constants once
    * a scenario constant naming an equation the model does not have is reported
    * registering a different definition under an existing scenario name is reported
    * `series_names` keys that match no column are reported

### 3.0.1

* Bugfixes:
    * the browser wheel installs with `micropip`

### 3.0.0

* Breaking: introduced extras `plotting`, `xmile`, `server`, `observability` — see [Installation](https://bptk.transentis.com/usage/installation.html). Base install no longer pulls matplotlib, flask, psycopg, redis, logfire, parsimonious, xmltodict, jinja2
* Breaking: removed the widget layer — `SimpleDashboard`, `ScenarioWidget`, `ModelConnection`, the `BPTK_Py.widgets` package, `HybridRunner.run_scenario(widget=…)`, ipywidgets
* Breaking: removed the unused dependencies `cachetools`, `requests`, `distlib`, the unused `BPTK_Py.sdcompiler.sdmodel` module, and the Docker image — it had not built since the maturin migration
* Breaking: `configure_logfire()` raises `ImportError` when Logfire is missing instead of returning `False`
* Feature: added a pure-Python wheel next to the platform wheels, so `micropip` can install BPTK in the browser
* Feature: rebuilt `progress_bar` on `tqdm` — works in the terminal, in marimo and in Jupyter
* Feature: added `format="plot" | "axes" | "df"` to `Element.plot()`, matching `visualizer.plot()`
* Feature: replaced sympy in the XMILE built-in `CGROWTH` with a closed form; results unchanged
* Bugfixes:
    * various small fixes

### 2.4.1

* Feature: Rust backend — when a model is rejected because its equations form a circular dependency, the error now names the equations involved (`Cyclic dependency among non-stock entities: a → b → a`) instead of only reporting that one exists
* Feature: a fallback from the Rust backend to Python that happens *after* a step-by-step session has already advanced is now logged as `[ERROR]` rather than `[WARN]`, because the Python backend cannot see the rounds the Rust engine already played and recomputes them with the settings of the current step
* Bugfixes:
    * Rust backend: a feedback loop closed only by a `delay()` is no longer rejected as cyclic
    * Rust backend: no `PanicException` when a threaded server continues a session on another thread
    * Rust backend: overrides passed with the first `run_step()` take effect in that step

### 2.4.0

* Feature: Step-by-step execution on the Rust backend (`RustSdModel.init()` / `step()`), wired through `bptk.run_step()` so server step-by-step sessions can run on Rust
* Feature: New stateless `/execute` server endpoint: POST a complete JSON model plus scenarios and get results back (primary path for the visual modeler)
* Feature: `/begin-session` accepts a `backend` field, and `bptk` accepts a `default_backend` configuration option, so a server can run Rust-backed sessions
* Feature: Rust-backed session resume through the external state adapter: the engine's memo grid is externalized and imported on resume (no re-simulation), with seed plumbing for reproducible stochastic models
* Substantially expanded test coverage
* Bugfixes:
    * XMILE compiler: `NORMAL`/`PREVIOUS` code generation, scientific-notation parsing, Windows encoding

### 2.3.0

* Feature: Add Rust-based SD execution backend (`backend="rust"`) for significantly faster simulation performance
* Feature: Rust engine supports stocks, flows, biflows, converters, constants, all arithmetic/logical operators, stochastic/statistical distributions, and graphical functions
* Feature: Automatic silent fallback to Python backend for unsupported features (arrays, modules, custom functions)
* Feature: Add `Model.to_json()` for serializing SD DSL models to JSON
* Feature: Add `ln`, `log10`, `floor`, `ceil`, `negbinomial` functions to SD DSL
* Bugfixes:
    * Rust engine: `geometric` and `pareto` match Python/numpy semantics
    * `ScenarioManagerSd.get_cloned_model()` copies the `_equation` attribute

### 2.2.3

* Added unit tests
* Bugfixes:
    * fixed typos

### 2.2.2

* Bugfixes:
    * external state adapter

### 2.2.1

* Feature: improved logfire logging

### 2.2.0

* Feature: Add externalStateAdapters for Postgres and Redis
* Feature: Add option to externalize state completely, thus turning bptkServer into a stateless server
* Feature: Add pydantic logfire as logging backend
* Feature: improved return message on bptkServer /stop-instance

### 2.1.1

* Updated dependencies

### 2.1.0

* Feature: extend plot_scenario to accept a format parameter
* Feature: enable operations: not named vector and int/float
* Added unit tests
* Bugfixes:
    * typos in the server output
    * configurable file path for the bptk object

### 2.0.0

* Feature: support for multidimensional sddsl

### 1.9.6

* Enable modulo operation for sddsl-elements
* remove unnecessary code
* add unittests/pytests 

### 1.9.5

* Fix publication issues

### 1.9.4

* Fix publication issues

### 1.9.3

* Fix agent.py serialize method
* Removed to_string method of agent.py
* Fix csv_datacollector.py 
* Removed kinesis_datacollector.py, yaml_model_parser.py and serializer.py
* Fix model.py reset method
* Adjusted model.py configure_properties method (only dict-values allowed)
* added unittests

### 1.9.2

* Fix to build script

### 1.9.1

* Bump versions of key dependencies
* Update XMILE parser grammar to remove depreciation warning
* Remove obsolete documentation files
* Update setup to use pyproject.toml
* Bump Python Version to 3.11

### 1.9.0
* BPTKServer: `run` endpoint now also works for agent-based models
* Model: Add `configure_agent`, `configure_properties` and `delete_agent(s)` methods
* Bump versions of key dependencies

### 1.8.0
* BPTKServer: Add new endpoint `start-instances` that starts multiple instances in one goo

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
*   New dataCollector for retrieving agent-wise data

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
*   The XMILE compiler is a great tool that handles model conversion from XMILE SD Models to Python. For compatibility and readability, we change the equation names to camelCasing upon conversion. This might be confusing for some users. That's why we decided to give you a new function call that lists all equations for System Dynamics Models. Simply run ``bptk.list_equations()`` (optionally add scenario manager(s) and scenario(s)) and get an overview over available model elements. More details [in our documentation](https://bptk.transentis.com/xmile/xmile_step_by_step/xmile_step_by_step.html).
*   Improved error messages. In previous versions, a long error trace was printed when an equation was not found. Now you get a neat error message output wiht hints as to why the plotting failed.
*   If an equation / scenario / scenario manager is not found, ``BPTK_Py`` gives hints on which similar equations / scenarios / scenario managers might be available for use.
*   Register XMILE models without having to follow the directory structure: ``BPTK_PY`` scans the ``scenarios`` folder upon startup to find new scenario managers and XMILE / ABM models. We developed a simpler way to add simulation models during runtime without having to add scenarios beforehand: ``bptk.register_model("<path_to_itmx_stmx>","<modelname>")``. You can then easily simulate the model just as you're used to.

### 1.1.4
XMILE equations make use of double-quote enclosed identifiers in case it actually looks like a function call. For example, ``100*"Identifier(enclosed)"`` is a valid equation where one element (stock/flow) is called ``Identifier(enclosed)``. However, we were not able to parse this, until now.
Update BPTK-Py using the new update mechanism: [documentation](https://bptk.transentis.com/usage/installation.html#keeping-bptk-py-up-to-date)

### 1.1.3
We figured that the update mechanisms via ``pip`` might be confusing sometimes, especially for non-programmers. This is
why we decided to implement an update mechanism. Details are available in the [documentation](https://bptk.transentis.com/usage/installation.html#keeping-bptk-py-up-to-date)

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
    *   More documentation and how to use the __statistical (random numbers from various distributions) and trigonometric operators__ can be found in our [online documentation](https://bptk.transentis.com/sd-dsl/sd_dsl_functions/sd_dsl_functions.html)
*   We fixed a bug that caused BPTK to crash when an XMILE model was updated while BPTK was monitoring it
*   We fixed SINWAVE in the XMILE transpiler and added support for COSWAVE

### 1.1.0
*   We are supporting all XMILE operators now. Note that random numbers with seed are **never** the same as when using Stella Architect's seed! This is due to different random number generators in Python and Stella. We neither support the min / max arguments for the random number operators. Refer to the [documentation](https://bptk.transentis.com/usage/limitations.html))
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
