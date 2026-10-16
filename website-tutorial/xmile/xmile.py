# Front matter the .py format cannot carry; injected on export.
# keywords: system dynamics, systemdynamics, xmile, bptk, bptk-py, python, business simulation
# description: Using XMILE System Dynamics models in the BPTK-Py business simulation framework.
#
# A section overview: prose and nothing else - not one chart, and no cell that offers
# a decision to take. Left reactive it booted Pyodide, some 8 MB, to display text, and
# it is the page a reader arrives on first.
# interactive: false
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

    - [XMILE Step by Step](./xmile_step_by_step/xmile_step_by_step.md)
    - [Working with Arrayed Variables in XMILE Models](./xmile_arrays/XMILE_arrays.md)
    - [Exporting Simulation Results](./exporting_simulation_results/exporting_simulation_results.md)
    - [Writing Computational Essays Based on Simulation Models](./writing_computational_essays/writing_computational_essays.md)
    - [Using the XMILE Compiler Standalone](./use_sd_compiler_standalone/use_sd_compiler_standalone.md)
    - [XMILE in the SD DSL](./xmile_in_the_sd_dsl/xmile_in_the_sd_dsl.md): for every XMILE builtin, its SD DSL function, the engines that run it and whether the transpiler compiles it
        - [Builtins Side by Side](./xmile_in_the_sd_dsl/builtins_side_by_side.md)
        - [Built from Other Functions](./xmile_in_the_sd_dsl/built_from_other_functions.md)
        - [Model Structure](./xmile_in_the_sd_dsl/model_structure.md)
    """)
    return


if __name__ == "__main__":
    app.run()
