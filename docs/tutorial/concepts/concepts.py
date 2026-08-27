# Front matter the .py format cannot carry; injected on export.
# keywords: agent-based modeling, system dynamics,abm, bptk, bptk-py, python, business simulation
# description: General overview of the BPTK-Py business simulation framework, as it applies to Agent-based modeling and System Dynamics.
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Core Concepts")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Core Concepts

    This section contains documents that are relevant to Agent-based modeling, System Dynamics with XMILE and System Dynamics with the SD DSL.

    ## Contents

    - [Architecture of the BPTK Framework](./bptk_architecture/bptk_architecture.md)
    - [Scenarios in Depth](./scenarios/scenarios.md)
    - [Accessing Raw Simulation Results](./accessing_raw_simulation_results/accessing_raw_simulation_results.md)
    - [Advanced Plotting Features](./advanced_plotting_features/advanced_plotting_features.md)
    - [Configuration of a BPTK Instance](./configuration/configuration.md)
    - [Execution Backends](./execution_backends/execution_backends.md)
    """)
    return


if __name__ == "__main__":
    app.run()
