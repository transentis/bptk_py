# Front matter the .py format cannot carry; injected on export.
# description: In-depth description of scenario management in the BPTK-Py business simulation framework, as it applies to Agent-based modeling and System Dynamics.
# keywords: agent-based modeling, abm, bptk, bptk-py, python, business simulation
#
# The reader can only look here: the models come from files, so none of the charts
# depends on the cells that define the scenarios - an edit to one of these dicts
# changes nothing on the page. The subject is the *shape* of a scenario definition,
# and a grey block shows that as well as an editor pretending otherwise.
# interactive: false
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Scenarios")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Scenarios In Depth

    Scenarios are the heart of a simulation. A scenario defines which simulation model to use, has a name and optionally points to a source model.
    It may override model constants and define execution strategies.

    ## Understanding The Scenario Definition Format

    Execution strategies change constants in different steps of the simulation. See the "strategy simulation" section for details.
    You write scenarios in [JSON format](http://www.json.org). The default location to store scenarios is the ``scenarios`` subfolder of your current working directory. The path to the ``scenarios`` folder can be changed in the bptk config.

    Simulations are grouped using "scenario managers". A scenario manager has a name and encapsulates one simulation model and an arbitrary number of scenarios. Scenarios are used to modify the initial values of a model. The required model is defined in the scenario manager's config file.
    A file can hold several scenario managers; this page's file holds one. It sits beside the
    page — [`scenarios/spm.json`](./scenarios/spm.json), which is what the framework reads when the
    page loads. It looks like this:

    ```json
    {
        "smSimpleProjectManagement": {
            "source":"simulation_models/sd_simple_project.itmx",
            "model":"simulation_models/sd_simple_project",
            "base_constants": {
                "deadline": 100,
                "effortPerTask": 1,
                "initialOpenTasks": 80,
                "initialStaff": 1
            },
            "base_points": {
                "productivity" : [
                [0,0.4],
                [0.25,0.444],
                [0.5,0.506],
                [0.75,0.594],
                [1,1],
                [1.25,1.119],
                [1.5,1.1625],
                [1.75,1.2125],
                [2,1.2375],
                [2.25,1.245],
                [2.5,1.25]
                ]
            },
            "scenarios": {
                "base": {
                },
                "scenario100": {
                    "constants": {
                        "initialOpenTasks": 100
                    }
                },
                "scenario80": {
                    "constants": {
                    }
                },
                "scenario120": {
                    "constants": {
                        "initialOpenTasks": 120
                    }
                },
                "scenario100WithPoints": {
                    "constants": {
                        "initialOpenTasks": 100
                    },
                    "points": {
                        "productivity" : [
                        [0,0.5],
                        [0.5,0.6],
                        [1,1],
                        [1.5,1.2],
                        [2.5,1.25]
                        ]
                    }
                }
            }
        }
    }
    ```
    A scenario manager requires a name.
    If the same name for a scenario manager is used in multiple files, this will be detected and the configs will be merged into one scenario manager. The files are read in alphabetical order, and where two of them set the same thing - a base constant, a base table, a scenario of the same name, ``model`` or ``source`` - the file read last wins.
    The scenario manager stores the model as well as all scenarios that belong to it. The ``model`` property is required, the ``source`` property is optional.
    The ``model`` property names the (python) simulation model, as a path to a module or as a dotted class - [Configuration](../configuration/configuration.md#configure-the-path-to-scenario-storage) says what it is relative to.
    The ``source`` property contains the path, relative to the same project directory, to the original model created in a 3rd party application. The framework provides automatic conversion from .itmx/.stmx (Stella Architect) files. When working with a supported 3rd party application, it is recommended to set the ``source`` property. When a value for ``source`` is provided, a file monitor will run in the background and check for changes in the source model. When changes are found the framework compiles the model again.

    The ``base_constants`` property defines the initial state for the model, regardless of the state in the model source file.
    ``base_constants`` can stretch over multiple files. If that is the case, ``bptk_py`` merges them constant by constant; a constant set in two files takes the value of the file that comes last in alphabetical order.
    The ``base_points`` property is used to define an initial state for graphical functions.

    Scenarios are defined in the ``scenarios`` property.
    Each scenario requires a unique name and a ``constants`` property. The ``constants`` property is used to override base constants (which were set in the ``base_constants`` property). In the example above ``scenario100`` overrides ``initialOpenTasks`` with the value ``100``, so that, when this scenario is run, the initial value for ``initialOpenTasks`` in the model is set to ``100``. ``scenario80`` does not override this value, therefore the ``initialOpenTasks`` value from the ``base_constants`` field is used when running this scenario.

    A scenario can also set its own graphical functions in a ``points`` property, as ``scenario100WithPoints`` does for ``productivity``; they replace the ``base_points`` of the same name for that scenario only.

    Values may either be defined using numerical expressions such as ``0.5`` or strings such as ``"4/10"`` which will be converted to ``0.4`` by the framework.

    Spreading scenarios across multiple files for one scenario manager can improve readability in situations with a high number of scenarios.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Creating Scenarios During Runtime

    It is possible to add scenarios during runtime. Here is example code that may be used as a template to generate scenarios during runtime.

    First, the details for the scenario manager are defined. After that, the name for the scenario is set up, then the strategy and the constants.
    """)
    return


@app.cell
def _(mo):
    import BPTK_Py

    bptk = BPTK_Py.bptk()

    scenario_manager = {
        "smSimpleProject_temp": {
            "source": "simulation_models/sd_simple_project.itmx",
            "model": "simulation_models/sd_simple_project",
        }
    }
    scenario_dictionary = {
        "scenario160": {
            "constants": {
                "deadline": 160,
                "effortPerTask": 0.1,
            }
        }
    }

    bptk.register_scenario_manager(scenario_manager)
    bptk.register_scenarios(
        scenario_manager="smSimpleProject_temp", scenarios=scenario_dictionary
    )

    with mo.capture_stdout() as output:
        bptk.list_scenarios(scenario_managers=["smSimpleProject_temp"])
    mo.vstack([
        mo.plain_text(output.getvalue()),
        bptk.plot_scenarios(
            scenario_managers=["smSimpleProject_temp"],
            scenarios=["scenario160"],
            equations=["openTasks", "closedTasks"],
            title="A scenario added at runtime",
            x_label="Time",
            y_label="Tasks",
            format="axes",
        ).figure,
    ])
    return (bptk,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can also register a scenario manager along with some scenarios directly:
    """)
    return


@app.cell
def _(bptk, mo):
    scenario_manager_1 = {
        "smSimpleProject_another_temp": {
            # No "source" this time: the XMILE file has already been transpiled for the
            # manager above, and naming only "model" reuses the compiled model instead of
            # compiling it a second time.
            "model": "simulation_models/sd_simple_project",
            "scenarios": {
                # Twice the effort per task, so the two managers are worth comparing
                "scenario160": {"constants": {"deadline": 160, "effortPerTask": 0.2}}
            },
        }
    }
    bptk.register_scenario_manager(scenario_manager_1)

    with mo.capture_stdout() as output_1:
        bptk.list_scenarios(
            scenario_managers=["smSimpleProject_temp", "smSimpleProject_another_temp"]
        )
    mo.vstack([
        mo.plain_text(output_1.getvalue()),
        bptk.plot_scenarios(
            scenario_managers=["smSimpleProject_another_temp", "smSimpleProject_temp"],
            scenarios=["scenario160"],
            equations=["openTasks"],
            title="The same scenario in two managers, at different effort per task",
            x_label="Time",
            y_label="Open tasks",
            format="axes",
        ).figure,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Resetting Scenarios
    After simulating for a while, modifying strategies, constants, and generating beautiful plots, it may be time to reset the simulation. For this purpose, three methods are available:

    * ``reset_scenario(scenario_manager, scenario)``: Delete a specific scenario from memory and reload it from file. Requires the scenario manager's name and the scenario name.
    * ``reset_all_scenarios()``: Reset all scenarios and reload from file
    * ``reset_scenario_cache(scenario_manager, scenario="")``: To optimize the runtime, scenarios cache the results of previous timesteps and previous runs. In some rare cases, this cache may not be flushed upon scenario modification. Hence, this method resets the simulation model's cache.

    For instance, ``bptk.reset_scenario(scenario_manager="smSimpleProjectManagement", scenario="scenario80")`` reloads ``scenario80`` from ``spm.json``, discarding any changes made at runtime.
    """)
    return


if __name__ == "__main__":
    app.run()
