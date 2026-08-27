# Front matter the .py format cannot carry; injected on export.
# keywords: system dynamics, systemdynamics, xmile, bptk, bptk-py, python, business simulation
# description: Using XMILE System Dynamics models in the BPTK-Py business simulation framework.
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Introduction to XMILE")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Working with XMILE

    Part of the BPTK framework is a transpiler that allows you to convert an XMILE model into a Python class.

    This feature allows you to work with XMILE models independently of the tool you used to create the model: you can run them from Python via [bptk](../api/api_bptk.md), work with them interactively in a notebook, or serve them over HTTP with [BptkServer](../api/api_bptk_server/api_bptk_server.md).

    We use Stella from [iseesystems](https://www.iseesystems.com) to work with XMILE models.

    ## Contents

    - [Writing Computational Essays Based on Simulation Models](./writing_computational_essays/writing_computational_essays.md)
    - [XMILE Step by Step](./xmile_step_by_step/xmile_step_by_step.md)
    - [Exporting Simulation Results](./exporting_simulation_results/exporting_simulation_results.md)
    - [Working with Arrayed Variables in XMILE Models](./xmile_arrays/XMILE_arrays.md)
    - [Using the XMILE Compiler Standalone](./use_sd_compiler_standalone/use_sd_compiler_standalone.md)
    """)
    return


if __name__ == "__main__":
    app.run()
