# Front matter the .py format cannot carry; injected on export.
# keywords: configuration, bptk, bptk-py, python, business simulation
# description: General overview of the possible individual configuration of a simulation using the configuration attribute of the bptk constructor
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Configuration")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Configuration

    This document explains the configuration settings of a ``bptk`` object.

    The code on this page is shown rather than run: it configures logging, file monitors and
    where scenarios are read from, none of which has an effect you could see on a documentation
    page — and some of which needs a token or a directory that only exists on your own machine.
    The one section that *is* live is the last one, on graphical settings.

    ## General

    The ``bptk`` constructor accepts two arguments:

    * ``loglevel`` — adjusts the **global** logging level, so it also applies to other `bptk`
      instances in the same process.
    * ``configuration`` — a dictionary, and the subject of the rest of this page.

    ## Configure Logfire

    Logging to [Logfire](https://logfire.pydantic.dev) is enabled **globally** through the
    ``configuration`` argument. It needs the ``observability`` extra:

    ```bash
    pip install "BPTK-Py[observability]"
    ```

    Register with Logfire, obtain a write token, and keep it out of your code — an ``.env`` file
    beside your notebook is the usual place. Reading it needs `python-dotenv`, which BPTK does
    not depend on; install it alongside:

    ```bash
    pip install python-dotenv
    ```


    ```bash
    # .env
    LOGFIRE_TOKEN=pylf_v1_eu_your_write_token_here
    ```

    Then read it and hand it to the constructor:

    ```python
    import os
    from dotenv import load_dotenv
    from logfire import ConsoleOptions
    from BPTK_Py import bptk

    load_dotenv()

    bptk_instance = bptk(
        loglevel="INFO",
        configuration={
            "logfire_config": {
                "environment": "development",
                "token": os.getenv("LOGFIRE_TOKEN"),
                "console": ConsoleOptions(show_project_link=False),
            }
        },
    )
    ```

    Once Logfire is configured, every message written to ``bptk_py.log`` (the default logfile
    name) is also sent to Logfire. Inside ``"logfire_config"`` you can pass both the essentials —
    ``"environment"`` and ``"token"`` — and any of the optional settings that control Logfire's
    behaviour and its appearance in the console. The full list is in the
    [Logfire configuration reference](https://logfire.pydantic.dev/docs/reference/configuration/).

    Logfire can also be configured directly, without going through a `bptk` instance:

    ```python
    import BPTK_Py.logger.logger as logmod
    from logfire import ConsoleOptions

    logmod.configure_logfire(
        token=os.getenv("LOGFIRE_TOKEN"),
        console=ConsoleOptions(show_project_link=False),
    )
    ```

    Without the ``observability`` extra installed, this raises ``ImportError`` naming the extra.

    ## Configure Additional Logging Settings

    Two further keys control where log messages go. Both are applied **globally**.

    * ``"log_modes"`` — list of strings, any of ``"print"`` and ``"logfile"``. Default:
      ``["logfile"]``.
    * ``"log_file"`` — string, the name of the logfile. Default: ``"bptk_py.log"``.

    ```python
    bptk_instance = bptk(
        loglevel="WARN",
        configuration={
            "log_modes": ["print", "logfile"],
            "log_file": "test_bptk.log",
        },
    )
    ```

    With this setting, log messages are written both to ``test_bptk.log`` and to the console.

    ## Configure Scenario and Model Monitor

    For each ``bptk`` instance you can decide whether changes to scenario files and model files
    are detected and applied automatically.

    * ``"set_scenario_monitor"`` — boolean. When True, a ``FileMonitor`` thread runs for each
      scenario JSON file and reloads the scenarios in it when the file changes on disk.
      Default: True.
    * ``"set_model_monitor"`` — boolean. When True, a ``ModelMonitor`` thread runs for the
      associated model file and updates every scenario that depends on it when the file changes.
      Default: True.

    To switch both off:

    ```python
    bptk_instance = bptk(
        loglevel="WARN",
        configuration={
            "set_scenario_monitor": False,
            "set_model_monitor": False,
        },
    )
    ```

    Neither monitor runs in a browser: they need threads that never return, which the browser
    platform does not provide.

    ## Configure the path to scenario storage

    A ``bptk`` instance finds its scenarios through the ``"scenario_storage"`` key, which
    defaults to ``"scenarios/"`` — a folder named ``scenarios`` relative to any directory on
    ``sys.path``.

    The folders beside this page are laid out like this, and you can open the files:

    ```
    concepts/
    ├── configuration/
    │   └── subfolder1/
    │       └── scenarios/
    │           └── scenario2.json
    └── folder2/
        └── scenarios/
            └── scenario3.json
    ```

    To load [`scenario2.json`](./subfolder1/scenarios/scenario2.json), which sits one level
    below this page:

    ```python
    bptk_instance = bptk(
        loglevel="INFO",
        configuration={"scenario_storage": "subfolder1/scenarios/"},
    )
    ```

    To load [`scenario3.json`](../folder2/scenarios/scenario3.json), which sits in a sibling of
    this page's folder, use a relative path pointing one level up:

    ```python
    bptk_instance = bptk(
        loglevel="INFO",
        configuration={"scenario_storage": "../folder2/scenarios/"},
    )
    ```

    Note that the **parent** of the ``"scenario_storage"`` path is added to ``sys.path``. The
    instance therefore also resolves the ``"model"`` path inside the scenario JSON relative to
    that parent.

    ## Configure graphic settings

    Plotting reads its defaults from the same ``configuration`` dictionary, so you can set the
    look of every plot an instance produces in one place instead of per call. This section is
    live — the model below is built in the page, so both plots really run.
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model

    savings = Model(starttime=1.0, stoptime=20.0, dt=1.0, name="Savings")

    total_value = savings.stock("totalValue")
    deposit = savings.flow("deposit")
    interest = savings.flow("interest")
    interest_rate = savings.constant("interestRate")

    total_value.initial_value = 1000.0
    interest_rate.equation = 0.05
    deposit.equation = 100.0
    interest.equation = total_value * interest_rate
    total_value.equation = deposit + interest
    return (savings,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    With no graphic settings at all, an instance plots like this:
    """)
    return


@app.cell
def _(savings):
    import BPTK_Py

    bptk_default = BPTK_Py.bptk()
    bptk_default.register_model(savings)
    bptk_default.plot_scenarios(
        scenario_managers="smSavings",
        scenarios="base",
        equations=["totalValue", "interest", "deposit"],
        format="axes",
    )
    return (BPTK_Py,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can set the kind of diagram (`line`, `area`, `bar`), whether the series are stacked,
    the colours, the transparency and any matplotlib rc setting. Change a value below and press
    play to see the difference:
    """)
    return


@app.cell
def _(BPTK_Py, savings):
    bptk_styled = BPTK_Py.bptk(
        configuration={
            "kind": "bar",              # bars instead of lines
            "stacked": False,           # side by side rather than on top of each other
            "colors": ["Red", "Blue", "Green"],
            "alpha": 0.98,              # almost opaque
            "matplotlib_rc_settings": {
                "xtick.labelsize": 10,
                "ytick.labelsize": 12,
                "legend.fontsize": 14,
            },
        }
    )
    bptk_styled.register_model(savings)
    bptk_styled.plot_scenarios(
        scenario_managers="smSavings",
        scenarios="base",
        equations=["totalValue", "interest", "deposit"],
        format="axes",
    )
    return


if __name__ == "__main__":
    app.run()
